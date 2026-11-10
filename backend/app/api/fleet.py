import os
import shutil
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.schema import Aircraft, Company, MaintenanceEvent, MarketAircraft
from app.services.xp_connector import xp_connector
from app.services.maintenance import MaintenanceService
from app.services.economy import EconomyService
from app.services.dealerships import DealershipService
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
    year_manufactured: int = 2021
    purchase_date: Optional[str] = None
    purchase_price_eur: float = 0.0
    image_url: Optional[str] = ""
    engine_type: Optional[str] = "Standard"
    avionics_system: Optional[str] = "Standard Avionics"

class AircraftUpdate(BaseModel):
    tail_number: Optional[str] = None
    purchase_date: Optional[str] = None
    name: Optional[str] = None
    aircraft_type: Optional[str] = None
    category: Optional[str] = None
    current_icao: Optional[str] = None
    fuel_capacity_kg: Optional[float] = None
    fuel_quantity_kg: Optional[float] = None
    year_manufactured: Optional[int] = None
    purchase_price_eur: Optional[float] = None
    image_url: Optional[str] = None
    engine_type: Optional[str] = None
    avionics_system: Optional[str] = None

class RentAircraftRequest(BaseModel):
    template_id: str
    tail_number: str
    pickup_icao: str = "LIRN"
    initial_fuel_kg: Optional[float] = None

class RefuelRequest(BaseModel):
    target_fuel_kg: float

class ServiceRequest(BaseModel):
    service_code: str

class AcquireAircraftRequest(BaseModel):
    market_aircraft_id: int
    tail_number: str
    acquisition_mode: str = "RENTAL_HOURLY" # "RENTAL_HOURLY", "OWNED_CASH", "FINANCIAL_LEASE", "FINANCED_LOAN"
    delivery_option: str = "DELIVER_HOME" # "DELIVER_HOME", "PICKUP_DEALERSHIP" (only for purchases)
    pickup_icao: Optional[str] = None

@router.get("/")
async def get_fleet(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Aircraft))
    aircraft_list = result.scalars().all()
    return aircraft_list

@router.get("/market")
async def get_synced_market(db: AsyncSession = Depends(get_db)):
    """
    Restituisce tutti i velivoli sincronizzati da X-Plane 12 organizzati per il Mercato & Noleggio,
    con calcolo trasparente di acquisto cash, leasing finanziario, mutuo bancario, noleggio orario
    e info sede di vendita / consegna ferry nel continente della base operativa.
    """
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    home_base = (company.home_base_icao if company and company.home_base_icao else "LIRN")
    xp12_path = (company.xp12_install_path if company else None)

    result = await db.execute(
        select(MarketAircraft).order_by(MarketAircraft.category, MarketAircraft.manufacturer, MarketAircraft.purchase_price_eur)
    )
    items = result.scalars().all()
    
    enriched = []
    for m in items:
        price = m.purchase_price_eur or 0.0
        # Financial lease: 20% down, rest +4% interest over 52 weeks
        lease_down = round(price * 0.20, 2)
        lease_total_financed = round(price * 0.80 * 1.04, 2)
        lease_weekly = round(lease_total_financed / 52.0, 2)
        
        # Bank loan: 10% down, rest +6% interest over 104 weeks
        loan_down = round(price * 0.10, 2)
        loan_total_financed = round(price * 0.90 * 1.06, 2)
        loan_weekly = round(loan_total_financed / 104.0, 2)
        
        delivery_info = DealershipService.get_dealership_for_aircraft(
            manufacturer=m.manufacturer,
            category=m.category,
            home_base_icao=home_base,
            xp12_path=xp12_path
        )
        
        enriched.append({
            "id": m.id,
            "acf_path": m.acf_path,
            "name": m.name,
            "aircraft_type": m.aircraft_type,
            "manufacturer": m.manufacturer,
            "studio": m.studio,
            "category": m.category,
            "fuel_capacity_kg": m.fuel_capacity_kg,
            "mtow_kg": m.mtow_kg,
            "cruise_speed_kts": m.cruise_speed_kts,
            "num_engines": m.num_engines,
            "engine_type": m.engine_type,
            "avionics_system": m.avionics_system,
            "year_manufactured": m.year_manufactured,
            "airframe_hours": m.airframe_hours,
            "condition_pct": m.condition_pct,
            "is_used": m.is_used,
            "purchase_price_eur": price,
            "hourly_lease_rate_eur": m.hourly_lease_rate_eur,
            "image_url": m.image_url,
            "default_tail": m.default_tail,
            "description": m.description,
            "delivery_info": delivery_info,
            "financing_options": {
                "cash": {"down_payment_eur": price, "weekly_eur": 0.0, "weeks": 0},
                "financial_lease": {"down_payment_eur": lease_down, "weekly_eur": lease_weekly, "weeks": 52, "total_financed_eur": lease_total_financed},
                "bank_loan": {"down_payment_eur": loan_down, "weekly_eur": loan_weekly, "weeks": 104, "total_financed_eur": loan_total_financed},
                "rental_hourly": {"down_payment_eur": 0.0, "hourly_eur": m.hourly_lease_rate_eur}
            }
        })
    return enriched

@router.post("/acquire")
async def acquire_market_aircraft(req: AcquireAircraftRequest, db: AsyncSession = Depends(get_db)):
    """
    Acquisisce un velivolo dal catalogo Mercato & Noleggio (XP12) secondo la formula scelta:
    Noleggio Orario, Acquisto Immediato Cash, Leasing Finanziario o Mutuo Bancario,
    con scelta tra ritiro presso la sede costruttore nel continente o consegna ferry alla base.
    """
    m = await db.get(MarketAircraft, req.market_aircraft_id)
    if not m:
        raise HTTPException(status_code=404, detail="Modello non trovato nel Mercato.")
        
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    if not company:
        raise HTTPException(status_code=400, detail="Profilo aziendale non inizializzato.")
        
    tail = req.tail_number.strip().upper()
    if not tail:
        raise HTTPException(status_code=400, detail="Inserisci le marche (Tail Number) del velivolo.")
        
    existing = await db.execute(select(Aircraft).where(Aircraft.tail_number == tail))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail=f"Un aeromobile con marche {tail} è già presente in flotta.")
        
    mode = req.acquisition_mode.upper()
    price = m.purchase_price_eur or 0.0
    
    down_payment = 0.0
    weekly_payment = 0.0
    remaining_weeks = 0
    financed_remaining = 0.0
    ownership = "OWNED"
    hourly_rate = 0.0
    display_suffix = ""
    
    if mode == "RENTAL_HOURLY":
        ownership = "LEASED"
        hourly_rate = m.hourly_lease_rate_eur
        display_suffix = " (Noleggio)"
    elif mode == "OWNED_CASH":
        down_payment = price
    elif mode == "FINANCIAL_LEASE":
        down_payment = round(price * 0.20, 2)
        financed_remaining = round(price * 0.80 * 1.04, 2)
        remaining_weeks = 52
        weekly_payment = round(financed_remaining / 52.0, 2)
    elif mode == "FINANCED_LOAN":
        down_payment = round(price * 0.10, 2)
        financed_remaining = round(price * 0.90 * 1.06, 2)
        remaining_weeks = 104
        weekly_payment = round(financed_remaining / 104.0, 2)
    else:
        raise HTTPException(status_code=400, detail="Modalità di acquisizione non valida.")

    # Calculate delivery & dealership location (for purchases only)
    ferry_fee = 0.0
    delivery_note = ""
    if mode == "RENTAL_HOURLY":
        final_icao = (req.pickup_icao or company.home_base_icao or "LIRN").strip().upper()
    else:
        delivery_info = DealershipService.get_dealership_for_aircraft(
            manufacturer=m.manufacturer,
            category=m.category,
            home_base_icao=company.home_base_icao or "LIRN",
            xp12_path=company.xp12_install_path
        )
        if req.delivery_option.upper() == "DELIVER_HOME":
            ferry_fee = delivery_info["ferry_delivery_fee_eur"]
            final_icao = company.home_base_icao or "LIRN"
            delivery_note = f"Consegnato con volo Ferry presso {final_icao} ({delivery_info['dealership_icao']} ➔ {final_icao})"
        else:
            ferry_fee = 0.0
            final_icao = delivery_info["dealership_icao"]
            delivery_note = f"Pronto per il ritiro presso sede costruttore {final_icao} ({delivery_info['dealership_name']})"

    total_due = round(down_payment + ferry_fee, 2)
    if total_due > 0 and company.cash_balance < total_due:
        raise HTTPException(
            status_code=400, 
            detail=f"Fondi insufficienti (€ {company.cash_balance:,.2f} disponibili vs € {total_due:,.2f} richiesti tra anticipo e consegna). Valuta il ritiro in sede, il Mutuo o il Noleggio."
        )
        
    if down_payment > 0:
        mode_names = {
            "OWNED_CASH": "Acquisto Immediato Cash",
            "FINANCIAL_LEASE": "Anticipo Leasing Finanziario (20%)",
            "FINANCED_LOAN": "Anticipo Finanziamento Bancario (10%)"
        }
        await EconomyService.record_transaction(
            session=db,
            category="AIRCRAFT_PURCHASE",
            title=f"{mode_names.get(mode, 'Acquisto')}: {m.name} ({tail})",
            amount_eur=-down_payment,
            description=f"Immatricolazione {tail} ({m.aircraft_type}) — {delivery_note}",
            aircraft_tail=tail,
            company=company
        )

    if ferry_fee > 0:
        await EconomyService.record_transaction(
            session=db,
            category="DELIVERY_FEE",
            title=f"Consegna Ferry a Domicilio {tail}",
            amount_eur=-ferry_fee,
            description=delivery_note,
            aircraft_tail=tail,
            company=company
        )
        
    base_icao = final_icao
    cond = m.condition_pct or 95.0
    
    aircraft = Aircraft(
        tail_number=tail,
        aircraft_type=m.aircraft_type,
        name=f"{m.name}{display_suffix}",
        manufacturer=m.manufacturer,
        category=m.category,
        ownership=ownership,
        current_icao=base_icao,
        fuel_capacity_kg=m.fuel_capacity_kg,
        fuel_quantity_kg=round(m.fuel_capacity_kg * 0.5, 1),
        mtow_kg=m.mtow_kg,
        airframe_hours=m.airframe_hours,
        engine_hours=m.airframe_hours,
        year_manufactured=m.year_manufactured,
        purchase_date=datetime.now(timezone.utc),
        purchase_price_eur=price if ownership == "OWNED" else 0.0,
        image_url=m.image_url or "",
        engine_type=m.engine_type,
        avionics_system=m.avionics_system,
        next_annual_inspection=datetime.now(timezone.utc) + timedelta(days=365),
        next_50h_inspection_hours=round(m.airframe_hours + 50.0, 1),
        next_100h_inspection_hours=round(m.airframe_hours + 100.0, 1),
        health_engine_pct=cond,
        health_brakes_pct=cond,
        health_tires_pct=cond,
        health_airframe_pct=min(100.0, cond + 1.5),
        health_avionics_pct=min(100.0, cond + 2.0),
        acquisition_mode=mode,
        weekly_payment_eur=weekly_payment,
        remaining_payments_weeks=remaining_weeks,
        financed_amount_remaining_eur=financed_remaining,
        hourly_lease_rate=hourly_rate
    )
    db.add(aircraft)
    await db.commit()
    await db.refresh(aircraft)
    
    msg_action = "noleggiato" if mode == "RENTAL_HOURLY" else "acquisito in flotta"
    return {
        "message": f"Aeromobile {tail} ({m.name}) {msg_action} con successo presso {base_icao}!",
        "aircraft": aircraft,
        "new_cash_balance": company.cash_balance
    }

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
        
    purchase_dt = datetime.now(timezone.utc)
    if data.purchase_date:
        try:
            if len(data.purchase_date) == 10:
                purchase_dt = datetime.strptime(data.purchase_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                purchase_dt = datetime.fromisoformat(data.purchase_date.replace("Z", "+00:00"))
        except Exception:
            pass

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
        year_manufactured=data.year_manufactured,
        purchase_date=purchase_dt,
        purchase_price_eur=data.purchase_price_eur,
        image_url=data.image_url or "",
        engine_type=data.engine_type or "Standard",
        avionics_system=data.avionics_system or "Standard Avionics",
        next_annual_inspection=datetime.now(timezone.utc) + timedelta(days=365),
        next_50h_inspection_hours=50.0,
        next_100h_inspection_hours=100.0,
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

@router.put("/{aircraft_id}")
async def update_aircraft(aircraft_id: int, data: AircraftUpdate, db: AsyncSession = Depends(get_db)):
    """Aggiorna i dettagli (marche, data acquisto, immagine, motore, anno, prezzo) di un aeromobile"""
    aircraft = await db.get(Aircraft, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    update_data = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.dict(exclude_unset=True)
    
    # Check tail_number uniqueness if changed
    if "tail_number" in update_data and update_data["tail_number"]:
        new_tail = update_data["tail_number"].strip().upper()
        if new_tail != aircraft.tail_number:
            existing = await db.execute(select(Aircraft).where(Aircraft.tail_number == new_tail, Aircraft.id != aircraft_id))
            if existing.scalars().first():
                raise HTTPException(status_code=400, detail=f"Un aeromobile con marche {new_tail} è già presente.")
            update_data["tail_number"] = new_tail

    # Parse purchase_date if provided
    if "purchase_date" in update_data:
        val = update_data["purchase_date"]
        if val:
            try:
                if len(val) == 10:  # YYYY-MM-DD
                    update_data["purchase_date"] = datetime.strptime(val, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    update_data["purchase_date"] = datetime.fromisoformat(val.replace("Z", "+00:00"))
            except Exception:
                del update_data["purchase_date"]
        else:
            del update_data["purchase_date"]

    for key, value in update_data.items():
        if value is not None:
            setattr(aircraft, key, value)
            
    await db.commit()
    await db.refresh(aircraft)
    return aircraft

@router.post("/{aircraft_id}/upload_image")
async def upload_aircraft_image(
    aircraft_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Carica un file immagine dal computer e la associa all'aeromobile"""
    aircraft = await db.get(Aircraft, aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../static/uploads"))
    os.makedirs(uploads_dir, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        ext = ".jpg"
        
    safe_tail = aircraft.tail_number.replace("-", "_").lower()
    filename = f"aircraft_{safe_tail}_{aircraft_id}{ext}"
    file_path = os.path.join(uploads_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    image_url = f"/uploads/{filename}"
    aircraft.image_url = image_url
    await db.commit()
    await db.refresh(aircraft)
    
    return {
        "message": f"Immagine caricata e salvata con successo per {aircraft.tail_number}!",
        "image_url": image_url,
        "aircraft": aircraft
    }

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
            await EconomyService.record_transaction(
                session=db,
                category="FUEL",
                title=f"Rifornimento a Terra ({diff_kg:.1f} kg)",
                amount_eur=-cost_eur,
                description=f"Carburante Jet-A1 imbarcato per {aircraft.tail_number} ({aircraft.current_icao})",
                aircraft_tail=aircraft.tail_number,
                company=company
            )
            
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
        await EconomyService.record_transaction(
            session=db,
            category="MAINTENANCE",
            title=f"Manutenzione: {srv['name']}",
            amount_eur=-cost_eur,
            description=f"Intervento officina su {aircraft.tail_number} ({aircraft.name})",
            aircraft_tail=aircraft.tail_number,
            company=company
        )
        
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
        
    if req.service_code == "OIL_AND_FILTER":
        aircraft.next_50h_inspection_hours = round(aircraft.airframe_hours + 50.0, 1)
    elif req.service_code == "INSPECTION_100H":
        aircraft.next_100h_inspection_hours = round(aircraft.airframe_hours + 100.0, 1)
        aircraft.next_50h_inspection_hours = round(aircraft.airframe_hours + 50.0, 1)
    elif req.service_code == "ANNUAL_INSPECTION":
        from datetime import datetime, timezone, timedelta
        aircraft.next_annual_inspection = datetime.now(timezone.utc) + timedelta(days=365)

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
