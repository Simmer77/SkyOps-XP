from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.schema import Job, Aircraft, Company
from app.services.job_generator import JobGenerator
from app.services.dealerships import DealershipService
from app.api.simbrief import calculate_simbrief_reward

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class GenerateJobsRequest(BaseModel):
    origin_icao: str
    category: str = "GA" # "GA", "BIZJET", "AIRLINER"
    count: int = 5

class AcceptJobRequest(BaseModel):
    aircraft_id: int

class ManualFlightPlanRequest(BaseModel):
    aircraft_id: int
    origin_icao: str
    destination_icao: str
    alternate_icao: Optional[str] = ""
    flight_number: Optional[str] = ""
    distance_nm: Optional[float] = 0.0
    pax_count: int = 2
    cargo_kg: float = 0.0
    route: Optional[str] = ""
    is_commercial: bool = True
    exclude_crew_cost: bool = False
    flight_rules: str = "IFR"
    tour_id: Optional[int] = None

@router.get("/estimate_route")
async def estimate_manual_route(
    origin: str = Query(...),
    destination: str = Query(...),
    category: str = Query("GA"),
    pax: int = Query(0),
    cargo: float = Query(0.0),
    is_commercial: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Calcola in anteprima distanza (NM) ed incasso stimato per un piano di volo manuale."""
    comp = (await db.execute(select(Company).limit(1))).scalars().first()
    xp_path = comp.xp12_install_path if comp else None
    dist = DealershipService.distance_between_icaos_nm(origin, destination, xp_path)
    eff_dist = dist if (dist and dist > 0) else 150.0
    reward = calculate_simbrief_reward(eff_dist, pax, cargo, category) if is_commercial else 0.0
    return {
        "origin_icao": origin.strip().upper(),
        "destination_icao": destination.strip().upper(),
        "distance_nm": dist,
        "estimated_distance_nm": eff_dist,
        "estimated_reward_eur": reward
    }

@router.post("/plan_manual")
async def create_manual_flight_plan(req: ManualFlightPlanRequest, db: AsyncSession = Depends(get_db)):
    """
    Crea un piano di volo manuale (senza SimBrief) assegnato all'aeromobile selezionato.
    Supporta Volo Commerciale ad incasso (default) oppure Volo Personale / Ferry (solo costi).
    """
    aircraft = await db.get(Aircraft, req.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")

    orig = req.origin_icao.strip().upper()
    dest = req.destination_icao.strip().upper()
    if len(orig) < 3 or len(dest) < 3:
        raise HTTPException(status_code=400, detail="Inserisci codici ICAO validi per Partenza e Destinazione.")

    comp = (await db.execute(select(Company).limit(1))).scalars().first()
    xp_path = comp.xp12_install_path if comp else None

    dist = req.distance_nm if (req.distance_nm and req.distance_nm > 0) else DealershipService.distance_between_icaos_nm(orig, dest, xp_path)
    if not dist or dist <= 0:
        dist = 150.0

    # Cancel any previous ACCEPTED/IN_PROGRESS jobs assigned to this aircraft
    old_jobs = (await db.execute(
        select(Job).where(Job.aircraft_id == aircraft.id, Job.status.in_(["ACCEPTED", "IN_PROGRESS"]))
    )).scalars().all()
    for oj in old_jobs:
        oj.status = "CANCELLED"

    flt_num = (req.flight_number or f"SO{aircraft.tail_number[-3:]}").strip().upper()
    if req.is_commercial:
        reward = calculate_simbrief_reward(dist, req.pax_count, req.cargo_kg, aircraft.category)
        jtype = "PASSENGER" if req.pax_count > 0 else "CARGO"
        title = f"Piano {flt_num}: {orig} -> {dest}"
    else:
        reward = 0.0
        jtype = "PERSONAL"
        title = f"Volo Personale/Ferry {flt_num}: {orig} -> {dest}"

    job = Job(
        title=title,
        job_type=jtype,
        origin_icao=orig,
        destination_icao=dest,
        distance_nm=round(dist, 1),
        pax_count=max(0, req.pax_count),
        cargo_kg=max(0.0, req.cargo_kg),
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
    await db.commit()
    await db.refresh(job)

    return {
        "message": f"Piano di volo manuale {orig} ➔ {dest} preparato ({'Ricavo: € ' + str(int(reward)) if req.is_commercial else 'Volo Personale senza ricavi'})!",
        "job": job
    }

@router.get("/")
async def get_jobs(airport: Optional[str] = None, status: str = "AVAILABLE", db: AsyncSession = Depends(get_db)):
    query = select(Job).where(Job.status == status)
    if airport:
        query = query.where(Job.origin_icao == airport.upper())
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/generate")
async def generate_jobs(req: GenerateJobsRequest, db: AsyncSession = Depends(get_db)):
    """Generates 4-5 dynamic contracts from the specified airport"""
    jobs_data = JobGenerator.generate_jobs_for_airport(req.origin_icao, req.category, req.count)
    created_jobs = []
    for jd in jobs_data:
        job = Job(**jd)
        db.add(job)
        created_jobs.append(job)
    await db.commit()
    for j in created_jobs:
        await db.refresh(j)
    return created_jobs

@router.post("/{job_id}/accept")
async def accept_job(job_id: int, req: AcceptJobRequest, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Incarico non trovato.")
    if job.status != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Incarico non disponibile o già assegnato.")
        
    aircraft = await db.get(Aircraft, req.aircraft_id)
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aeromobile non trovato.")
        
    if aircraft.current_icao.upper() != job.origin_icao.upper():
        raise HTTPException(
            status_code=400,
            detail=f"L'aeromobile {aircraft.tail_number} si trova a {aircraft.current_icao}, mentre l'incarico parte da {job.origin_icao}."
        )
        
    job.status = "ACCEPTED"
    job.aircraft_id = aircraft.id
    await db.commit()
    await db.refresh(job)
    return {
        "message": f"Incarico accettato con successo per {aircraft.tail_number}.",
        "job": job
    }
