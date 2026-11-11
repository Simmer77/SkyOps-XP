from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.schema import Tour, FlightLog, Job, Company
from app.services.dealerships import DealershipService

router = APIRouter(prefix="/tours", tags=["Tours"])


class CreateTourRequest(BaseModel):
    name: str
    description: Optional[str] = ""


class UpdateTourRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # "ACTIVE" | "COMPLETED"


@router.get("/")
async def list_tours(db: AsyncSession = Depends(get_db)):
    """Restituisce tutti i Tour creati con le statistiche aggregate delle tappe completate."""
    tours_res = await db.execute(select(Tour).order_by(Tour.id.desc()))
    tours = tours_res.scalars().all()

    logs_res = await db.execute(select(FlightLog).where(FlightLog.tour_id.isnot(None)).order_by(FlightLog.id.asc()))
    logs = logs_res.scalars().all()

    comp = (await db.execute(select(Company).limit(1))).scalars().first()
    xp_path = comp.xp12_install_path if comp else None

    logs_by_tour = {}
    for lg in logs:
        logs_by_tour.setdefault(lg.tour_id, []).append(lg)

    result = []
    for t in tours:
        t_logs = logs_by_tour.get(t.id, [])
        total_nm = 0.0
        for lg in t_logs:
            d = lg.distance_flown_nm or 0.0
            if d <= 0 and lg.origin_icao and lg.destination_icao:
                calc = DealershipService.distance_between_icaos_nm(lg.origin_icao, lg.destination_icao, xp_path)
                d = calc or 0.0
            total_nm += d
        total_min = sum(lg.flight_duration_min or 0.0 for lg in t_logs)
        total_fuel = sum(lg.fuel_used_kg or 0.0 for lg in t_logs)
        total_profit = sum(lg.net_profit_usd or 0.0 for lg in t_logs)
        td_fpms = [abs(lg.touchdown_fpm) for lg in t_logs if lg.touchdown_fpm is not None]
        avg_fpm = round(sum(td_fpms) / len(td_fpms), 0) if td_fpms else None
        route_chain = [t_logs[0].origin_icao] + [lg.destination_icao for lg in t_logs] if t_logs else []

        result.append({
            "id": t.id,
            "name": t.name,
            "description": t.description or "",
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "legs_count": len(t_logs),
            "total_nm": round(total_nm, 1),
            "total_hours": round(total_min / 60.0, 1),
            "total_fuel_kg": round(total_fuel, 1),
            "total_net_profit_eur": round(total_profit, 2),
            "avg_touchdown_fpm": avg_fpm,
            "route_chain": route_chain,
        })
    return result


@router.post("/")
async def create_tour(req: CreateTourRequest, db: AsyncSession = Depends(get_db)):
    name = (req.name or "").strip()
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Inserisci un nome valido per il Tour (es. IVAO World Tour).")

    dup = (await db.execute(select(Tour).where(Tour.name == name))).scalars().first()
    if dup:
        raise HTTPException(status_code=400, detail=f"Esiste già un Tour chiamato '{name}'.")

    tour = Tour(name=name, description=(req.description or "").strip(), status="ACTIVE")
    db.add(tour)
    await db.commit()
    await db.refresh(tour)
    return {"message": f"Tour '{tour.name}' creato con successo!", "tour": tour}


@router.get("/{tour_id}")
async def get_tour_detail(tour_id: int, db: AsyncSession = Depends(get_db)):
    """Restituisce tutte le tappe cronologiche del Tour con coordinate aeroporti per la mappa."""
    tour = await db.get(Tour, tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour non trovato.")

    comp = (await db.execute(select(Company).limit(1))).scalars().first()
    xp_path = comp.xp12_install_path if comp else None

    logs = (
        await db.execute(select(FlightLog).where(FlightLog.tour_id == tour_id).order_by(FlightLog.id.asc()))
    ).scalars().all()

    legs = []
    total_nm = 0.0
    total_min = 0.0
    total_fuel = 0.0
    total_profit = 0.0
    td_fpms = []

    for idx, lg in enumerate(logs, start=1):
        orig_name, orig_lat, orig_lon = DealershipService.get_airport_coords(lg.origin_icao, xp_path)
        dest_name, dest_lat, dest_lon = DealershipService.get_airport_coords(lg.destination_icao, xp_path)
        dist = lg.distance_flown_nm or 0.0
        if dist <= 0:
            dist = DealershipService._haversine_nm(orig_lat, orig_lon, dest_lat, dest_lon)

        total_nm += dist
        total_min += lg.flight_duration_min or 0.0
        total_fuel += lg.fuel_used_kg or 0.0
        total_profit += lg.net_profit_usd or 0.0
        if lg.touchdown_fpm is not None:
            td_fpms.append(abs(lg.touchdown_fpm))

        legs.append({
            "leg_number": idx,
            "flight_log_id": lg.id,
            "flight_number": lg.flight_number,
            "origin_icao": lg.origin_icao,
            "origin_name": orig_name,
            "origin_lat": orig_lat,
            "origin_lon": orig_lon,
            "destination_icao": lg.destination_icao,
            "destination_name": dest_name,
            "destination_lat": dest_lat,
            "destination_lon": dest_lon,
            "distance_nm": round(dist, 1),
            "duration_min": lg.flight_duration_min,
            "fuel_used_kg": lg.fuel_used_kg,
            "touchdown_fpm": lg.touchdown_fpm,
            "touchdown_rating": lg.touchdown_rating,
            "net_profit_eur": lg.net_profit_usd,
            "flight_rules": getattr(lg, "flight_rules", "IFR"),
            "start_time": lg.start_time.isoformat() if lg.start_time else None,
        })

    return {
        "tour": tour,
        "stats": {
            "legs_count": len(legs),
            "total_nm": round(total_nm, 1),
            "total_hours": round(total_min / 60.0, 1),
            "total_fuel_kg": round(total_fuel, 1),
            "total_net_profit_eur": round(total_profit, 2),
            "avg_touchdown_fpm": round(sum(td_fpms) / len(td_fpms), 0) if td_fpms else None,
        },
        "legs": legs,
    }


@router.patch("/{tour_id}")
async def update_tour(tour_id: int, req: UpdateTourRequest, db: AsyncSession = Depends(get_db)):
    tour = await db.get(Tour, tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour non trovato.")
    if req.name and req.name.strip():
        tour.name = req.name.strip()
    if req.description is not None:
        tour.description = req.description.strip()
    if req.status and req.status.upper() in ["ACTIVE", "COMPLETED"]:
        tour.status = req.status.upper()
    await db.commit()
    await db.refresh(tour)
    return {"message": f"Tour '{tour.name}' aggiornato.", "tour": tour}


@router.delete("/{tour_id}")
async def delete_tour(tour_id: int, db: AsyncSession = Depends(get_db)):
    tour = await db.get(Tour, tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour non trovato.")

    await db.execute(update(Job).where(Job.tour_id == tour_id).values(tour_id=None))
    await db.execute(update(FlightLog).where(FlightLog.tour_id == tour_id).values(tour_id=None))
    await db.delete(tour)
    await db.commit()
    return {"message": f"Tour '{tour.name}' eliminato (i voli restano salvati nel Logbook)."}
