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

# Catalogo Modelli a Noleggio Disponibili (Dry/Wet Lease Charter Market)
RENTAL_CATALOG = [
    {
        "id": "c172",
        "name": "Cessna 172 Skyhawk SP",
        "aircraft_type": "C172",
        "category": "GA",
        "hourly_rate_eur": 165.0,
        "fuel_capacity_kg": 145.0,
        "cruising_speed_kts": 120,
        "range_nm": 640,
        "description": "Monomotore a pistoni ideale per addestramento, voli turistici e brevi collegamenti GA."
    },
    {
        "id": "sf50",
        "name": "Cirrus Vision SF50 G2",
        "aircraft_type": "SF50",
        "category": "GA",
        "hourly_rate_eur": 390.0,
        "fuel_capacity_kg": 907.0,
        "cruising_speed_kts": 305,
        "range_nm": 1150,
        "description": "Personal Single-Engine Jet con paracadute CAPS, cabina pressurizzata e avionica Garmin Perspective+."
    },
    {
        "id": "e550",
        "name": "Eclipse 550 NG",
        "aircraft_type": "E550",
        "category": "BIZJET",
        "hourly_rate_eur": 680.0,
        "fuel_capacity_kg": 1140.0,
        "cruising_speed_kts": 375,
        "range_nm": 1125,
        "description": "Very Light Jet bimotore estremamente veloce ed economico per rotte executive europee."
    },
    {
        "id": "phenom300",
        "name": "Embraer Phenom 300E",
        "aircraft_type": "E55P",
        "category": "BIZJET",
        "hourly_rate_eur": 980.0,
        "fuel_capacity_kg": 2450.0,
        "cruising_speed_kts": 450,
        "range_nm": 1950,
        "description": "Il jet leggero business più venduto al mondo. Cabina confortevole per 7-9 passeggeri e alta quota."
    },
    {
        "id": "b738",
        "name": "Boeing 737-800X (Zibo)",
        "aircraft_type": "B738",
        "category": "AIRLINER",
        "hourly_rate_eur": 1850.0,
        "fuel_capacity_kg": 20800.0,
        "cruising_speed_kts": 460,
        "range_nm": 2930,
        "description": "Airliner narrow-body di linea per eccellenza. Ideale per collegamenti charter ad alta capienza."
    },
    {
        "id": "a320",
        "name": "Airbus A320neo",
        "aircraft_type": "A20N",
        "category": "AIRLINER",
        "hourly_rate_eur": 1920.0,
        "fuel_capacity_kg": 19000.0,
        "cruising_speed_kts": 455,
        "range_nm": 3300,
        "description": "Airliner fly-by-wire ad altissima efficienza per voli commerciali e rotte passeggeri europee."
    }
]

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

class RentAircraftRequest(BaseModel):
    template_id: str
    tail_number: str
    pickup_icao: str = "LIRN"
    initial_fuel_kg: Optional[float] = None

class RefuelRequest(BaseModel):
    target_fuel_kg: float

class ServiceRequest(BaseModel):
    service_code: str

@router.get("/")
async def get_fleet(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Aircraft))
    aircraft_list = result.scalars().all()
    return aircraft_list

@router.get("/rentals/catalog")
async def get_rental_catalog():
    """Restituisce il catalogo degli aerei noleggiabili on-demand"""
    return RENTAL_CATALOG

@router.post("/rent")
async def rent_aircraft(req: RentAircraftRequest, db: AsyncSession = Depends(get_db)):
    """Noleggia un aereo dal catalogo per uso immediato o continuativo"""
    template = next((item for item in RENTAL_CATALOG if item["id"] == req.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Modello a noleggio non trovato nel catalogo.")
        
    tail = req.tail_number.strip().upper()
    existing = await db.execute(select(Aircraft).where(Aircraft.tail_number == tail))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail=f"Un aeromobile con marche {tail} è già presente in flotta.")
        
    fuel = req.initial_fuel_kg if req.initial_fuel_kg is not None else (template["fuel_capacity_kg"] * 0.5)
    
    aircraft = Aircraft(
        tail_number=tail,
        aircraft_type=template["aircraft_type"],
        name=f"{template['name']} (Noleggio)",
        category=template["category"],
        ownership="LEASED",
        current_icao=req.pickup_icao.strip().upper(),
        fuel_capacity_kg=template["fuel_capacity_kg"],
        fuel_quantity_kg=min(template["fuel_capacity_kg"], max(20.0, fuel)),
        hourly_lease_rate=template["hourly_rate_eur"],
        health_engine_pct=98.0,
        health_brakes_pct=96.0,
        health_tires_pct=95.0,
        health_airframe_pct=99.0,
        health_avionics_pct=100.0,
        airframe_hours=450.0,
        engine_hours=450.0
    )
    db.add(aircraft)
    await db.commit()
    await db.refresh(aircraft)
    return {
        "message": f"Contratto di noleggio stipulato! {aircraft.tail_number} ({template['name']}) disponibile a {aircraft.current_icao} a {template['hourly_rate_eur']} €/h.",
        "aircraft": aircraft
    }

@router.delete("/{aircraft_id}")
async def delete_aircraft(aircraft_id: int, db: AsyncSession = Depends(get_db)):
    """Rimuove un aereo di proprietà o riconsegna un aereo a noleggio"""
    aircraft = await db.get(Aircraft, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    if aircraft.is_in_flight:
        raise HTTPException(status_code=400, detail="Impossibile eliminare o riconsegnare un aereo attualmente in volo!")
        
    tail = aircraft.tail_number
    ownership = aircraft.ownership
    await db.delete(aircraft)
    await db.commit()
    
    action_str = "restituito al locatore" if ownership == "LEASED" else "rimosso dall'hangar"
    return {"message": f"Aeromobile {tail} {action_str} con successo."}

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
    Invia la quantità di carburante e la configurazione salvata dell'aereo a X-Plane 12.
    """
    aircraft = await db.get(Aircraft, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    if not xp_connector.is_connected:
        return {"status": "warning", "message": "X-Plane non connesso. I dati verranno applicati non appena il simulatore si collega."}
        
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
    
    cost_eur = 0.0
    if diff_kg > 0:
        cost_eur = round(diff_kg * settings.DEFAULT_FUEL_PRICE_EUR_PER_KG, 2)
        if company and company.cash_balance < cost_eur:
            raise HTTPException(status_code=400, detail="Fondi insufficienti per il rifornimento.")
        if company:
            company.cash_balance -= cost_eur
            
    aircraft.fuel_quantity_kg = target
    await db.commit()
    
    if xp_connector.is_connected:
        xp_connector.set_fuel_kg(target)
        
    return {
        "message": f"Rifornimento completato: {target:.1f} kg a bordo.",
        "cost_eur": cost_eur,
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
    cost_eur = srv.get("cost_eur", srv.get("cost_usd", 0.0))
    
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    
    if company and company.cash_balance < cost_eur:
        raise HTTPException(status_code=400, detail="Fondi societari insufficienti per questo intervento.")
        
    if company:
        company.cash_balance -= cost_eur
        
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
        cost_usd=cost_eur,
        notes=srv["name"]
    )
    db.add(event)
    await db.commit()
    
    return {
        "message": f"Intervento '{srv['name']}' completato con successo.",
        "cost_eur": cost_eur,
        "aircraft_health": {
            "engine": aircraft.health_engine_pct,
            "brakes": aircraft.health_brakes_pct,
            "tires": aircraft.health_tires_pct,
            "airframe": aircraft.health_airframe_pct,
            "avionics": aircraft.health_avionics_pct
        }
    }
