import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.core.database import get_db
from app.models.schema import (
    Company, Aircraft, Job, FlightLog, MaintenanceEvent,
    FinancialTransaction, MarketAircraft
)
from app.services.xp_scanner import XP12ScannerService
from app.services.flight_tracker import flight_tracker

logger = logging.getLogger("SkyOps.CompanyAPI")
router = APIRouter(prefix="/company", tags=["Company"])

DIFFICULTY_CAPITALS = {
    "HARDCORE": {"label": "Pilota Indipendente (Hardcore)", "capital_eur": 35000.0},
    "REALISTIC": {"label": "Carriera Realistica (Start-up)", "capital_eur": 150000.0},
    "STANDARD": {"label": "Compagnia Emergente (Standard)", "capital_eur": 500000.0},
    "EXECUTIVE": {"label": "Operatore Executive (Avanzato)", "capital_eur": 2500000.0},
    "MAGNATE": {"label": "Major Airline / Magnate", "capital_eur": 25000000.0},
}

class CreateCompanyRequest(BaseModel):
    name: str
    home_base_icao: str = "LIRN"
    difficulty_level: str = "STANDARD"
    starting_capital_eur: Optional[float] = None
    simbrief_id: Optional[str] = ""
    xp12_install_path: Optional[str] = ""
    sync_xp12: bool = True

class SyncXP12Request(BaseModel):
    xp12_install_path: Optional[str] = None

@router.post("/create")
async def create_company_profile(req: CreateCompanyRequest, db: AsyncSession = Depends(get_db)):
    """
    Crea il profilo aziendale iniziale, imposta base operativa e capitale iniziale,
    e opzionalmente sincronizza gli aerei installati in X-Plane 12 nel Mercato & Noleggio.
    """
    existing = (await db.execute(select(Company).limit(1))).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Esiste già un profilo attivo. Esegui prima il reset se vuoi ricominciare.")
        
    diff_key = req.difficulty_level.upper()
    diff_info = DIFFICULTY_CAPITALS.get(diff_key, DIFFICULTY_CAPITALS["STANDARD"])
    capital = req.starting_capital_eur if req.starting_capital_eur is not None else diff_info["capital_eur"]
    
    raw_sb = (req.simbrief_id or "").strip()
    sb_pilot = raw_sb if raw_sb.isdigit() else ""
    sb_user = "" if raw_sb.isdigit() else raw_sb
    
    detected_xp = (req.xp12_install_path or "").strip() or (XP12ScannerService.detect_xp12_path() or "")
    
    company = Company(
        name=req.name.strip() or "SkyOps Aviation",
        home_base_icao=req.home_base_icao.strip().upper()[:4] or "LIRN",
        cash_balance=capital,
        starting_capital_eur=capital,
        difficulty_level=diff_key,
        reputation=100.0,
        virtual_date=datetime.now(timezone.utc),
        operating_day=1,
        operating_month=datetime.now(timezone.utc).strftime("%Y-%m"),
        simbrief_username=sb_user,
        simbrief_pilot_id=sb_pilot,
        xp12_install_path=detected_xp
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    
    scan_res = None
    if req.sync_xp12:
        scan_res = await XP12ScannerService.scan_and_sync_to_db(db, detected_xp)
        
    return {
        "status": "success",
        "message": f"Profilo '{company.name}' creato con successo presso la base {company.home_base_icao}!",
        "company": company,
        "xp12_sync": scan_res
    }

@router.post("/sync_xp12")
async def sync_xp12_aircraft(req: SyncXP12Request, db: AsyncSession = Depends(get_db)):
    """
    Scansiona la cartella Aircraft di X-Plane 12 e aggiorna il catalogo Mercato & Noleggio.
    """
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    
    target_path = (req.xp12_install_path or "").strip()
    if not target_path and company and company.xp12_install_path:
        target_path = company.xp12_install_path
    if not target_path:
        target_path = XP12ScannerService.detect_xp12_path() or ""
        
    scan_res = await XP12ScannerService.scan_and_sync_to_db(db, target_path)
    if not scan_res.get("success"):
        raise HTTPException(status_code=400, detail=scan_res.get("error", "Errore scansione X-Plane 12."))
        
    if company and scan_res.get("xp12_path"):
        company.xp12_install_path = scan_res["xp12_path"]
        await db.commit()
        
    return {
        "status": "success",
        "message": f"Sincronizzati {scan_res['count']} velivoli da X-Plane 12 nel Mercato & Noleggio!",
        "sync": scan_res
    }

@router.delete("/reset")
async def reset_company_profile(db: AsyncSession = Depends(get_db)):
    """
    Cancella interamente il profilo aziendale, la flotta, i voli e il libro mastro,
    riportando SkyOps XP allo stato iniziale per creare una nuova carriera.
    """
    # Reset active tracker
    flight_tracker.phase = "OFFLINE"
    flight_tracker.active_aircraft_id = None
    flight_tracker.active_job_id = None

    await db.execute(delete(FinancialTransaction))
    await db.execute(delete(FlightLog))
    await db.execute(delete(MaintenanceEvent))
    await db.execute(delete(Job))
    await db.execute(delete(Aircraft))
    await db.execute(delete(MarketAircraft))
    await db.execute(delete(Company))
    await db.commit()
    
    logger.info("Company profile and all career data wiped cleanly.")
    return {
        "status": "reset",
        "message": "Profilo cancellato e database azzerato con successo."
    }
