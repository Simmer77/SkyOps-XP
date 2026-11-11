from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.models.schema import Aircraft, Job, FlightLog, Company, CrewMember
from app.services.flight_tracker import flight_tracker
from app.services.xp_connector import xp_connector
from app.services.dealerships import DealershipService
from app.services.economy import EconomyService, CATEGORY_SPECS

router = APIRouter(prefix="/flights", tags=["Flights"])

MAX_AIRPORT_RADIUS_NM = 5.0

class StartFlightRequest(BaseModel):
    aircraft_id: int
    job_id: Optional[int] = None
    exclude_crew_cost: Optional[bool] = None
    flight_rules: Optional[str] = None
    tour_id: Optional[int] = None

class FinalizeFlightRequest(BaseModel):
    actual_arrival_icao: Optional[str] = None
    diversion_reason: Optional[str] = None
    exclude_crew_cost: Optional[bool] = None
    flight_rules: Optional[str] = None
    tour_id: Optional[int] = None

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

    cat_key = (aircraft.category if aircraft else "GA") or "GA"
    cat_specs = CATEGORY_SPECS.get(cat_key, CATEGORY_SPECS["GA"])
    salaried_crew = (
        await db.execute(select(CrewMember).where(CrewMember.category == cat_key, CrewMember.is_active == True))
    ).scalars().first()
    effective_exclude_crew = (
        flight_tracker.exclude_crew_cost
        if flight_tracker.active_aircraft_id is not None
        else bool(job.exclude_crew_cost if job else False)
    )
    effective_rules = (
        flight_tracker.flight_rules
        if flight_tracker.active_aircraft_id is not None
        else (getattr(job, "flight_rules", None) or "IFR")
    )
    effective_tour_id = (
        flight_tracker.tour_id
        if flight_tracker.active_aircraft_id is not None
        else getattr(job, "tour_id", None)
    )

    return {
        "is_active": flight_tracker.active_aircraft_id is not None,
        "phase": flight_tracker.phase,
        "aircraft": aircraft,
        "job": job,
        "exclude_crew_cost": effective_exclude_crew,
        "flight_rules": effective_rules,
        "tour_id": effective_tour_id,
        "has_salaried_crew": salaried_crew is not None,
        "salaried_crew_name": salaried_crew.name if salaried_crew else None,
        "crew_spec": {
            "label": cat_specs.get("crew_label", "1 Pilota"),
            "hourly_rate_eur": cat_specs.get("crew_hourly_rate_eur", 90.0),
            "monthly_salary_eur": cat_specs.get("crew_monthly_salary_eur", 1800.0),
            "pilots_count": cat_specs.get("pilots_count", 1),
            "attendants_count": cat_specs.get("attendants_count", 0),
        },
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

    # Smart Pre-Flight Fuel Delta Sync:
    # Se il pilota ha aggiunto carburante direttamente in X-Plane 12 (es. da 315 kg a 532 kg),
    # addebita SOLO la differenza rifornita (217 kg) ed evita di sovrascrivere il serbatoio del sim.
    xp_fuel = round(t.get("fuel_total_kg", 0.0), 1)
    saved_fuel = round(aircraft.fuel_quantity_kg or 0.0, 1)
    preflight_refuel_kg = 0.0
    preflight_refuel_cost = 0.0

    if xp_fuel > saved_fuel + 2.0:
        capped_xp_fuel = min(aircraft.fuel_capacity_kg or xp_fuel, xp_fuel) if (aircraft.fuel_capacity_kg and aircraft.fuel_capacity_kg > 0) else xp_fuel
        added_kg = round(capped_xp_fuel - saved_fuel, 1)
        if added_kg > 2.0:
            refuel_cost = round(added_kg * settings.DEFAULT_FUEL_PRICE_EUR_PER_KG, 2)
            if comp and comp.cash_balance < refuel_cost:
                raise HTTPException(
                    status_code=400,
                    detail=f"Fondi insufficienti per il carburante imbarcato in X-Plane ({added_kg:.1f} kg = € {refuel_cost:,.2f}). Saldo attuale: € {comp.cash_balance:,.2f}."
                )
            if comp:
                await EconomyService.record_transaction(
                    session=db,
                    category="FUEL",
                    title=f"Rifornimento Pre-Volo ({added_kg:.1f} kg a {origin_icao})",
                    amount_eur=-refuel_cost,
                    description=f"Delta carburante aggiunto in X-Plane 12 ({saved_fuel:.1f} -> {capped_xp_fuel:.1f} kg) per {aircraft.tail_number}",
                    aircraft_tail=aircraft.tail_number,
                    company=comp
                )
            aircraft.fuel_quantity_kg = capped_xp_fuel
            preflight_refuel_kg = added_kg
            preflight_refuel_cost = refuel_cost
    elif xp_fuel > 0.5 and abs(xp_fuel - saved_fuel) > 2.0 and xp_fuel < saved_fuel:
        # Adotta il carburante effettivo di X-Plane senza addebiti se inferiore al residuo salvato
        aircraft.fuel_quantity_kg = xp_fuel
            
    aircraft.is_in_flight = True
    if job:
        job.status = "IN_PROGRESS"
        job.aircraft_id = aircraft.id
    exclude_crew = (
        bool(req.exclude_crew_cost)
        if req.exclude_crew_cost is not None
        else bool(job.exclude_crew_cost if job else False)
    )
    eff_rules = (
        req.flight_rules.strip().upper()
        if (req.flight_rules and req.flight_rules.strip())
        else ((getattr(job, "flight_rules", None) if job else None) or "IFR")
    ).upper()
    eff_tour_id = req.tour_id if req.tour_id is not None else (getattr(job, "tour_id", None) if job else None)

    if job:
        if req.exclude_crew_cost is not None:
            job.exclude_crew_cost = exclude_crew
        if req.flight_rules:
            job.flight_rules = eff_rules
        if req.tour_id is not None:
            job.tour_id = eff_tour_id
    await db.commit()
    
    flight_tracker.start_flight(
        aircraft.id,
        job.id if job else None,
        exclude_crew_cost=exclude_crew,
        flight_rules=eff_rules,
        tour_id=eff_tour_id
    )
    
    # Se X-Plane riportava serbatoio vuoto (0 kg), ripristina quello salvato in SkyOps
    if xp_fuel <= 0.5 and aircraft.fuel_quantity_kg > 0:
        xp_connector.set_fuel_kg(aircraft.fuel_quantity_kg)

    msg = f"Volo avviato da {origin_icao} per {aircraft.tail_number}."
    if preflight_refuel_kg > 0:
        msg += f" Rilevato rifornimento pre-volo: +{preflight_refuel_kg:.1f} kg (€ {preflight_refuel_cost:,.2f})."
        
    return {
        "message": msg,
        "phase": flight_tracker.phase,
        "job_id": job.id if job else None,
        "preflight_refuel_kg": preflight_refuel_kg,
        "preflight_refuel_cost": preflight_refuel_cost
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
        diversion_reason=(req.diversion_reason if req else None),
        exclude_crew_cost=(req.exclude_crew_cost if req else None),
        flight_rules=(req.flight_rules if req else None),
        tour_id=(req.tour_id if req else None)
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
