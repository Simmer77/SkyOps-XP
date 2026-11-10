from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.schema import Aircraft, Job, FlightLog, Company
from app.services.flight_tracker import flight_tracker
from app.services.xp_connector import xp_connector
from app.services.dealerships import DealershipService

router = APIRouter(prefix="/flights", tags=["Flights"])

MAX_AIRPORT_RADIUS_NM = 5.0

class StartFlightRequest(BaseModel):
    aircraft_id: int
    job_id: Optional[int] = None

class FinalizeFlightRequest(BaseModel):
    actual_arrival_icao: Optional[str] = None
    diversion_reason: Optional[str] = None

async def _resolve_active_job(db: AsyncSession, aircraft_id: Optional[int]) -> Optional[Job]:
    if flight_tracker.active_job_id:
        j = await db.get(Job, flight_tracker.active_job_id)
        if j:
            return j
    if aircraft_id:
        res = await db.execute(
            select(Job)
            .where(Job.aircraft_id == aircraft_id, Job.status.in_(["IN_PROGRESS", "ACCEPTED"]))
            .order_by(Job.id.desc())
        )
        return res.scalars().first()
    return None

@router.get("/active")
async def get_active_flight(
    aircraft_id: Optional[int] = Query(None),
    alternate_icao: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    target_ac_id = flight_tracker.active_aircraft_id or aircraft_id
    aircraft = await db.get(Aircraft, target_ac_id) if target_ac_id else None
    job = await _resolve_active_job(db, target_ac_id)
    
    comp = (await db.execute(select(Company).limit(1))).scalars().first()
    xp_path = comp.xp12_install_path if comp else None

    t = xp_connector.telemetry
    xp_conn = xp_connector.is_connected
    on_ground = bool(t.get("on_ground", 1.0) > 0.5 and t.get("groundspeed_kts", 0.0) < 5.0)
    parking_brake_set = bool(t.get("parking_brake", 0.0) >= 0.5)
    lat = t.get("latitude", 0.0)
    lon = t.get("longitude", 0.0)

    origin_icao = (job.origin_icao if job else (aircraft.current_icao if aircraft else "")).upper()
    dest_icao = (
        alternate_icao.strip().upper()
        if (alternate_icao and alternate_icao.strip())
        else (job.destination_icao if job else (aircraft.current_icao if aircraft else ""))
    ).upper()

    orig_dist = DealershipService.distance_from_live_pos_nm(lat, lon, origin_icao, xp_path) if (xp_conn and origin_icao) else None
    dest_dist = DealershipService.distance_from_live_pos_nm(lat, lon, dest_icao, xp_path) if (xp_conn and dest_icao) else None

    at_origin = (orig_dist is not None and orig_dist <= MAX_AIRPORT_RADIUS_NM)
    at_destination = (dest_dist is not None and dest_dist <= MAX_AIRPORT_RADIUS_NM)

    return {
        "is_active": flight_tracker.active_aircraft_id is not None,
        "phase": flight_tracker.phase,
        "aircraft": aircraft,
        "job": job,
        "start_fuel_kg": flight_tracker.start_fuel_kg,
        "current_fuel_kg": flight_tracker.current_fuel_kg,
        "max_g": flight_tracker.max_g,
        "min_g": flight_tracker.min_g,
        "touchdown_fpm": flight_tracker.touchdown_fpm,
        "touchdown_g": flight_tracker.touchdown_g,
        "touchdown_rating": flight_tracker.touchdown_rating,
        "telemetry": t,
        "xp_connected": xp_conn,
        "flight_checks": {
            "xp_connected": xp_conn,
            "on_ground_stopped": on_ground,
            "parking_brake_set": parking_brake_set,
            "planned_origin_icao": origin_icao,
            "origin_distance_nm": orig_dist,
            "at_origin": at_origin if orig_dist is not None else xp_conn,
            "origin_verified": orig_dist is not None,
            "planned_destination_icao": dest_icao,
            "destination_distance_nm": dest_dist,
            "at_destination": at_destination if dest_dist is not None else xp_conn,
            "destination_verified": dest_dist is not None,
            "can_start": bool(xp_conn and on_ground and parking_brake_set and (at_origin or orig_dist is None)),
            "can_finalize": bool(xp_conn and on_ground and parking_brake_set and (at_destination or dest_dist is None))
        }
    }

@router.post("/start")
async def start_flight(req: StartFlightRequest, db: AsyncSession = Depends(get_db)):
    aircraft = await db.get(Aircraft, req.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    job = await db.get(Job, req.job_id) if req.job_id else await _resolve_active_job(db, aircraft.id)
    if req.job_id and not job:
        raise HTTPException(status_code=404, detail="Piano di volo / Incarico non trovato.")

    # Pre-flight safety & location checks against live X-Plane 12 telemetry
    if not xp_connector.is_connected:
        raise HTTPException(
            status_code=400,
            detail="X-Plane 12 non connesso. Avvia il simulatore e posizionati sull'aeroporto di partenza prima di iniziare il volo."
        )

    t = xp_connector.telemetry
    if t.get("on_ground", 1.0) <= 0.5 or t.get("groundspeed_kts", 0.0) >= 5.0:
        raise HTTPException(
            status_code=400,
            detail="L'aeromobile deve essere fermo al parcheggio a terra (Ground Speed < 5 kts) per avviare il monitoraggio."
        )

    if t.get("parking_brake", 0.0) < 0.5:
        raise HTTPException(
            status_code=400,
            detail="Freno di parcheggio (Parking Brake) NON inserito! Inserisci i freni di parcheggio in X-Plane 12 per avviare il volo."
        )

    origin_icao = (job.origin_icao if job else aircraft.current_icao).upper()
    comp = (await db.execute(select(Company).limit(1))).scalars().first()
    xp_path = comp.xp12_install_path if comp else None
    dist = DealershipService.distance_from_live_pos_nm(t.get("latitude", 0.0), t.get("longitude", 0.0), origin_icao, xp_path)

    if dist is not None and dist > MAX_AIRPORT_RADIUS_NM:
        raise HTTPException(
            status_code=400,
            detail=f"Posizione non valida in X-Plane 12! L'aereo si trova a {dist:.1f} NM dall'aeroporto di partenza pianificato ({origin_icao}). Spostati a {origin_icao} oppure aggiorna il piano di volo."
        )
            
    aircraft.is_in_flight = True
    if job:
        job.status = "IN_PROGRESS"
        job.aircraft_id = aircraft.id
    await db.commit()
    
    flight_tracker.start_flight(aircraft.id, job.id if job else None)
    
    # Auto-sync fuel to X-Plane if simulator is running
    xp_connector.set_fuel_kg(aircraft.fuel_quantity_kg)
        
    return {
        "message": f"Volo avviato da {origin_icao} per {aircraft.tail_number}.",
        "phase": flight_tracker.phase,
        "job_id": job.id if job else None
    }

@router.post("/finalize")
async def finalize_flight(
    req: Optional[FinalizeFlightRequest] = Body(default=None),
    db: AsyncSession = Depends(get_db)
):
    if not flight_tracker.active_aircraft_id:
        raise HTTPException(status_code=400, detail="Nessun volo attivo da chiudere.")

    if not xp_connector.is_connected:
        raise HTTPException(
            status_code=400,
            detail="X-Plane 12 non connesso. Assicurati che il simulatore sia aperto con l'aereo fermo al parcheggio."
        )

    t = xp_connector.telemetry
    if t.get("on_ground", 1.0) <= 0.5 or t.get("groundspeed_kts", 0.0) >= 5.0:
        raise HTTPException(
            status_code=400,
            detail="Impossibile chiudere il volo: l'aeromobile deve essere fermo a terra (Ground Speed < 5 kts)."
        )

    if t.get("parking_brake", 0.0) < 0.5:
        raise HTTPException(
            status_code=400,
            detail="Inserisci i freni di parcheggio (Parking Brake) in X-Plane 12 al termine della rullata per chiudere il volo."
        )

    aircraft = await db.get(Aircraft, flight_tracker.active_aircraft_id)
    job = await _resolve_active_job(db, flight_tracker.active_aircraft_id)

    planned_dest = (job.destination_icao if job else (aircraft.current_icao if aircraft else "")).upper()
    actual_arr = req.actual_arrival_icao.strip().upper() if (req and req.actual_arrival_icao and req.actual_arrival_icao.strip()) else planned_dest

    comp = (await db.execute(select(Company).limit(1))).scalars().first()
    xp_path = comp.xp12_install_path if comp else None
    dist = DealershipService.distance_from_live_pos_nm(t.get("latitude", 0.0), t.get("longitude", 0.0), actual_arr, xp_path)

    if dist is not None and dist > MAX_AIRPORT_RADIUS_NM:
        raise HTTPException(
            status_code=400,
            detail=f"Non ti trovi sull'aeroporto di arrivo {actual_arr} (sei a {dist:.1f} NM di distanza). Raggiungi {actual_arr} oppure inserisci manualmente il codice ICAO dell'aeroporto alternato / d'emergenza su cui sei atterrato."
        )

    summary = await flight_tracker.finalize_flight(
        actual_arrival_icao=actual_arr,
        diversion_reason=(req.diversion_reason if req else None)
    )
    if not summary:
        raise HTTPException(status_code=500, detail="Errore durante la chiusura del volo.")
        
    return {
        "message": f"Volo completato con successo presso {actual_arr}!",
        "summary": summary
    }

@router.get("/history")
async def get_flight_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FlightLog).order_by(FlightLog.id.desc()).limit(limit))
    return result.scalars().all()
