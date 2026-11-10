from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.schema import Job, Aircraft, Company
from app.services.simbrief import SimBriefService

router = APIRouter(prefix="/simbrief", tags=["SimBrief"])

class ImportOFPRequest(BaseModel):
    username: Optional[str] = None
    pilot_id: Optional[str] = None
    aircraft_id: int

@router.get("/latest")
async def get_latest_ofp(
    username: Optional[str] = Query(None),
    pilot_id: Optional[str] = Query(None),
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
        
    return ofp

@router.post("/import_flight")
async def import_simbrief_flight(req: ImportOFPRequest, db: AsyncSession = Depends(get_db)):
    """
    Imports the latest OFP from SimBrief directly as an active contract for the selected aircraft.
    """
    ofp = await SimBriefService.fetch_latest_ofp(username=req.username, pilot_id=req.pilot_id)
    if not ofp:
        raise HTTPException(status_code=404, detail="Impossibile recuperare il piano SimBrief.")
        
    aircraft = await db.get(Aircraft, req.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    # Reward estimation based on distance, pax, and category
    dist = ofp["distance_nm"]
    reward = round(dist * 22.0 + (ofp["pax_count"] * 120.0) + (ofp["cargo_kg"] * 1.5), 0)
    
    # Create Job directly
    job = Job(
        title=f"SimBrief {ofp['flight_number']}: {ofp['origin_icao']} -> {ofp['destination_icao']}",
        job_type="PASSENGER" if ofp["pax_count"] > 0 else "CARGO",
        origin_icao=ofp["origin_icao"],
        destination_icao=ofp["destination_icao"],
        distance_nm=dist,
        pax_count=ofp["pax_count"],
        cargo_kg=ofp["cargo_kg"],
        required_category=aircraft.category,
        reward_usd=max(500.0, reward),
        penalty_usd=round(reward * 0.15, 0),
        status="ACCEPTED",
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
