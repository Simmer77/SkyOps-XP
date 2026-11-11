from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.schema import Job, Aircraft, Company
from app.services.simbrief import SimBriefService
from app.services.economy import EconomyService

router = APIRouter(prefix="/simbrief", tags=["SimBrief"])

class ImportOFPRequest(BaseModel):
    username: Optional[str] = None
    pilot_id: Optional[str] = None
    aircraft_id: int
    is_commercial: bool = True
    exclude_crew_cost: bool = False
    flight_rules: str = "IFR"
    tour_id: Optional[int] = None

def calculate_simbrief_reward(
    dist_nm: float,
    pax_count: int,
    cargo_kg: float,
    category: str = "GA",
    mtow_kg: float = 0.0,
    economy_mode: str = "REALISTIC"
) -> float:
    return EconomyService.calculate_route_reward(
        distance_nm=dist_nm,
        pax_count=pax_count,
        cargo_kg=cargo_kg,
        category=category,
        mtow_kg=mtow_kg,
        economy_mode=economy_mode
    )

@router.get("/latest")
async def get_latest_ofp(
    username: Optional[str] = Query(None),
    pilot_id: Optional[str] = Query(None),
    category: str = Query("GA"),
    mtow_kg: float = Query(0.0),
    db: AsyncSession = Depends(get_db)
):
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()

    # If not passed in query, try looking up saved company settings
    if not username and not pilot_id and company:
        pilot_id = company.simbrief_pilot_id
        username = company.simbrief_username
            
    if not username and not pilot_id:
        raise HTTPException(status_code=400, detail="Inserisci il tuo username o Pilot ID di SimBrief.")
        
    ofp = await SimBriefService.fetch_latest_ofp(username=username, pilot_id=pilot_id)
    if not ofp:
        raise HTTPException(
            status_code=404, 
            detail="Nessun piano di volo SimBrief trovato. Verifica il tuo Pilot ID numerico (es. 1106351) o username e assicurati di aver generato un OFP su SimBrief."
        )

    # Save valid SimBrief credentials for future sessions
    if company:
        raw_val = (pilot_id or username or "").strip()
        if raw_val.isdigit():
            company.simbrief_pilot_id = raw_val
        elif raw_val:
            company.simbrief_username = raw_val
        if ofp.get("user_id"):
            company.simbrief_pilot_id = ofp["user_id"]
        await db.commit()
        
    # Attach estimated commercial reward using company's active economy_mode
    econ_mode = (company.economy_mode if company and getattr(company, "economy_mode", None) else "REALISTIC")
    ofp["estimated_reward_eur"] = calculate_simbrief_reward(
        ofp.get("distance_nm", 0.0),
        ofp.get("pax_count", 0),
        ofp.get("cargo_kg", 0.0),
        category=category,
        mtow_kg=mtow_kg,
        economy_mode=econ_mode
    )
    return ofp

@router.post("/import_flight")
async def import_simbrief_flight(req: ImportOFPRequest, db: AsyncSession = Depends(get_db)):
    """
    Imports the latest OFP from SimBrief directly as an active flight plan/contract for the selected aircraft.
    Supports both Commercial (default, generates revenue) and Personal/Ferry (no revenue, costs only).
    """
    ofp = await SimBriefService.fetch_latest_ofp(username=req.username, pilot_id=req.pilot_id)
    if not ofp:
        raise HTTPException(status_code=404, detail="Impossibile recuperare il piano SimBrief.")
        
    aircraft = await db.get(Aircraft, req.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")

    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    econ_mode = (company.economy_mode if company and getattr(company, "economy_mode", None) else "REALISTIC")

    # Cancel any previous ACCEPTED/IN_PROGRESS jobs assigned to this aircraft to avoid conflicts
    old_jobs = (await db.execute(
        select(Job).where(Job.aircraft_id == aircraft.id, Job.status.in_(["ACCEPTED", "IN_PROGRESS"]))
    )).scalars().all()
    for oj in old_jobs:
        oj.status = "CANCELLED"

    # Calculate reward if commercial flight, or 0 for personal/ferry flight
    dist = ofp["distance_nm"]
    if req.is_commercial:
        reward = calculate_simbrief_reward(
            dist, ofp["pax_count"], ofp["cargo_kg"],
            category=aircraft.category,
            mtow_kg=aircraft.mtow_kg or 0.0,
            economy_mode=econ_mode
        )
        jtype = "PASSENGER" if ofp["pax_count"] > 0 else "CARGO"
        title_prefix = f"SimBrief {ofp['flight_number']}"
    else:
        reward = 0.0
        jtype = "PERSONAL"
        title_prefix = f"Volo Personale/Ferry {ofp['flight_number']}"
    
    # Create Job directly
    job = Job(
        title=f"{title_prefix}: {ofp['origin_icao']} -> {ofp['destination_icao']}",
        job_type=jtype,
        origin_icao=ofp["origin_icao"],
        destination_icao=ofp["destination_icao"],
        distance_nm=dist,
        pax_count=ofp["pax_count"],
        cargo_kg=ofp["cargo_kg"],
        required_category=aircraft.category,
        reward_usd=reward,
        penalty_usd=round(reward * 0.15, 0) if reward > 0 else 0.0,
        status="ACCEPTED",
        exclude_crew_cost=req.exclude_crew_cost,
        flight_rules=(req.flight_rules or "IFR").strip().upper(),
        tour_id=req.tour_id,
        aircraft_id=aircraft.id
    )
    db.add(job)
    
    # Save SimBrief username/id
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    if company:
        raw_val = (req.pilot_id or req.username or "").strip()
        if raw_val.isdigit():
            company.simbrief_pilot_id = raw_val
        elif raw_val:
            company.simbrief_username = raw_val
        if ofp.get("user_id"):
            company.simbrief_pilot_id = ofp["user_id"]
            
    await db.commit()
    await db.refresh(job)
    
    return {
        "message": f"Piano di volo {ofp['flight_number']} importato con successo!",
        "job": job,
        "ofp": ofp
    }
