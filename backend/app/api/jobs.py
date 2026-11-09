from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.schema import Job, Aircraft
from app.services.job_generator import JobGenerator

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class GenerateJobsRequest(BaseModel):
    origin_icao: str
    category: str = "GA" # "GA", "BIZJET", "AIRLINER"
    count: int = 5

class AcceptJobRequest(BaseModel):
    aircraft_id: int

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
