from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.schema import Aircraft, Job, FlightLog
from app.services.flight_tracker import flight_tracker
from app.services.xp_connector import xp_connector

router = APIRouter(prefix="/flights", tags=["Flights"])

class StartFlightRequest(BaseModel):
    aircraft_id: int
    job_id: Optional[int] = None

@router.get("/active")
async def get_active_flight(db: AsyncSession = Depends(get_db)):
    aircraft = None
    job = None
    if flight_tracker.active_aircraft_id:
        aircraft = await db.get(Aircraft, flight_tracker.active_aircraft_id)
    if flight_tracker.active_job_id:
        job = await db.get(Job, flight_tracker.active_job_id)
        
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
        "telemetry": xp_connector.telemetry,
        "xp_connected": xp_connector.is_connected
    }

@router.post("/start")
async def start_flight(req: StartFlightRequest, db: AsyncSession = Depends(get_db)):
    aircraft = await db.get(Aircraft, req.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    job = None
    if req.job_id:
        job = await db.get(Job, req.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Incarico non trovato.")
            
    aircraft.is_in_flight = True
    if job:
        job.status = "IN_PROGRESS"
    await db.commit()
    
    flight_tracker.start_flight(aircraft.id, req.job_id)
    
    # Auto-sync fuel to X-Plane if simulator is running
    if xp_connector.is_connected:
        xp_connector.set_fuel_kg(aircraft.fuel_quantity_kg)
        
    return {
        "message": f"Volo avviato per {aircraft.tail_number}.",
        "phase": flight_tracker.phase
    }

@router.post("/finalize")
async def finalize_flight():
    if not flight_tracker.active_aircraft_id:
        raise HTTPException(status_code=400, detail="Nessun volo attivo da chiudere.")
        
    summary = await flight_tracker.finalize_flight()
    if not summary:
        raise HTTPException(status_code=500, detail="Errore durante la chiusura del volo.")
        
    return {
        "message": "Volo completato con successo!",
        "summary": summary
    }

@router.get("/history")
async def get_flight_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FlightLog).order_by(FlightLog.id.desc()).limit(limit))
    return result.scalars().all()
