from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.schema import Aircraft, Company, MaintenanceEvent
from app.services.xp_connector import xp_connector
from app.services.maintenance import MaintenanceService
from app.core.config import settings

router = APIRouter(prefix="/fleet", tags=["Fleet"])

class AircraftCreate(BaseModel):
    tail_number: str
    aircraft_type: str
    name: str
    category: str = "GA" # "GA", "BIZJET", "AIRLINER"
    ownership: str = "OWNED" # "OWNED", "LEASED"
    current_icao: str = "LIRN"
    fuel_capacity_kg: float = 900.0
    fuel_quantity_kg: float = 450.0
    hourly_lease_rate: float = 0.0

class RefuelRequest(BaseModel):
    target_fuel_kg: float

class ServiceRequest(BaseModel):
    service_code: str # "OIL_AND_FILTER", "INSPECTION_100H", "TIRES_REPLACE", "BRAKES_OVERHAUL", "ANNUAL_INSPECTION", "ENGINE_OVERHAUL"

@router.get("/")
async def get_fleet(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Aircraft))
    aircraft_list = result.scalars().all()
    return aircraft_list

@router.post("/")
async def create_aircraft(data: AircraftCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Aircraft).where(Aircraft.tail_number == data.tail_number.upper()))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Aeromobile con questa marche (Tail Number) già presente.")
        
    aircraft = Aircraft(
        tail_number=data.tail_number.upper(),
        aircraft_type=data.aircraft_type.upper(),
        name=data.name,
        category=data.category.upper(),
        ownership=data.ownership.upper(),
        current_icao=data.current_icao.upper(),
        fuel_capacity_kg=data.fuel_capacity_kg,
        fuel_quantity_kg=data.fuel_quantity_kg,
        hourly_lease_rate=data.hourly_lease_rate,
        health_engine_pct=100.0,
        health_brakes_pct=100.0,
        health_tires_pct=100.0,
        health_airframe_pct=100.0,
        health_avionics_pct=100.0
    )
    db.add(aircraft)
    await db.commit()
    await db.refresh(aircraft)
    return aircraft

@router.post("/{aircraft_id}/sync_xp")
async def sync_aircraft_to_xp(aircraft_id: int, db: AsyncSession = Depends(get_db)):
    """
    Sends the stored fuel quantity and configuration of this aircraft to X-Plane 12.
    """
    aircraft = await db.get(Aircraft, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    if not xp_connector.is_connected:
        return {"status": "warning", "message": "X-Plane non connesso. I dati verranno applicati non appena il simulatore si collega."}
        
    # Inject fuel to X-Plane
    success = xp_connector.set_fuel_kg(aircraft.fuel_quantity_kg)
    return {
        "status": "success" if success else "failed",
        "message": f"Sincronizzati {aircraft.fuel_quantity_kg:.1f} kg di carburante su X-Plane 12 per {aircraft.tail_number}."
    }

@router.post("/{aircraft_id}/refuel")
async def refuel_aircraft(aircraft_id: int, req: RefuelRequest, db: AsyncSession = Depends(get_db)):
    aircraft = await db.get(Aircraft, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    target = min(aircraft.fuel_capacity_kg, max(0.0, req.target_fuel_kg))
    diff_kg = target - aircraft.fuel_quantity_kg
    
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    
    cost = 0.0
    if diff_kg > 0:
        cost = round(diff_kg * settings.DEFAULT_FUEL_PRICE_USD_PER_KG, 2)
        if company and company.cash_balance < cost:
            raise HTTPException(status_code=400, detail="Fondi insufficienti per il rifornimento.")
        if company:
            company.cash_balance -= cost
            
    aircraft.fuel_quantity_kg = target
    await db.commit()
    
    # Sync to X-Plane if connected
    if xp_connector.is_connected:
        xp_connector.set_fuel_kg(target)
        
    return {
        "message": f"Rifornimento completato: {target:.1f} kg a bordo.",
        "cost_usd": cost,
        "fuel_added_kg": max(0.0, diff_kg)
    }

@router.post("/{aircraft_id}/service")
async def perform_service(aircraft_id: int, req: ServiceRequest, db: AsyncSession = Depends(get_db)):
    aircraft = await db.get(Aircraft, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    services = MaintenanceService.get_service_costs()
    if req.service_code not in services:
        raise HTTPException(status_code=400, detail="Tipo di manutenzione non valido.")
        
    srv = services[req.service_code]
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    
    if company and company.cash_balance < srv["cost_usd"]:
        raise HTTPException(status_code=400, detail="Fondi societari insufficienti per questo intervento.")
        
    if company:
        company.cash_balance -= srv["cost_usd"]
        
    # Apply health restoration
    if "engine_health_gain" in srv:
        aircraft.health_engine_pct = min(100.0, aircraft.health_engine_pct + srv["engine_health_gain"])
    if "brakes_health_gain" in srv:
        aircraft.health_brakes_pct = min(100.0, aircraft.health_brakes_pct + srv["brakes_health_gain"])
    if "tires_health_gain" in srv:
        aircraft.health_tires_pct = min(100.0, aircraft.health_tires_pct + srv["tires_health_gain"])
    if "airframe_health_gain" in srv:
        aircraft.health_airframe_pct = min(100.0, aircraft.health_airframe_pct + srv["airframe_health_gain"])
    if "avionics_health_gain" in srv:
        aircraft.health_avionics_pct = min(100.0, aircraft.health_avionics_pct + srv["avionics_health_gain"])
        
    event = MaintenanceEvent(
        aircraft_id=aircraft.id,
        event_type=req.service_code,
        cost_usd=srv["cost_usd"],
        notes=srv["name"]
    )
    db.add(event)
    await db.commit()
    
    return {
        "message": f"Intervento '{srv['name']}' completato con successo.",
        "cost_usd": srv["cost_usd"],
        "aircraft_health": {
            "engine": aircraft.health_engine_pct,
            "brakes": aircraft.health_brakes_pct,
            "tires": aircraft.health_tires_pct,
            "airframe": aircraft.health_airframe_pct,
            "avionics": aircraft.health_avionics_pct
        }
    }
