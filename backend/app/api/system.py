from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import asyncio
import json

from app.core.database import get_db
from app.models.schema import Company
from app.services.xp_connector import xp_connector
from app.services.xp_scanner import XP12ScannerService
from app.services.maintenance import MaintenanceService
from app.services.economy import EconomyService
from app.services.flight_tracker import flight_tracker

router = APIRouter(prefix="/system", tags=["System"])

class FailureInjectRequest(BaseModel):
    failure_dref: str
    mode: int = 6

@router.get("/status")
async def get_system_status(db: AsyncSession = Depends(get_db)):
    comp_res = await db.execute(select(Company).limit(1))
    company = comp_res.scalars().first()
    detected_xp = XP12ScannerService.detect_xp12_path() or ""
    
    return {
        "has_profile": company is not None,
        "xp12_detected_path": detected_xp,
        "xp_connected": xp_connector.is_connected,
        "xp_aircraft_icao": xp_connector.detected_icao,
        "xp_aircraft_tailnum": xp_connector.detected_tailnum,
        "xp_ip": xp_connector.xp_ip,
        "xp_port": xp_connector.xp_port,
        "active_flight_phase": flight_tracker.phase,
        "company": {
            "name": company.name,
            "home_base_icao": company.home_base_icao or "LIRN",
            "difficulty_level": company.difficulty_level or "STANDARD",
            "starting_capital_eur": company.starting_capital_eur or 150000.0,
            "cash_balance": company.cash_balance,
            "reputation": company.reputation,
            "operating_day": company.operating_day or 1,
            "virtual_date": company.virtual_date.isoformat() if company.virtual_date else None,
            "simbrief_username": company.simbrief_username or "",
            "simbrief_pilot_id": company.simbrief_pilot_id or "",
            "xp12_install_path": company.xp12_install_path or detected_xp,
        } if company else None,
        "services_catalog": MaintenanceService.get_service_costs()
    }

@router.get("/financial_guide")
async def get_financial_guide():
    """Restituisce le regole economiche, formule, tariffe e costi di riferimento"""
    return EconomyService.get_financial_guide()

@router.post("/inject_failure")
async def inject_failure(req: FailureInjectRequest):
    success = xp_connector.inject_failure(req.failure_dref, req.mode)
    return {
        "success": success,
        "message": f"Inviato comando avaria: {req.failure_dref} (mode: {req.mode})"
    }

@router.websocket("/ws")
async def websocket_telemetry(websocket: WebSocket):
    """Real-time streaming telemetry and flight status to UI dashboard"""
    await websocket.accept()
    try:
        while True:
            payload = {
                "xp_connected": xp_connector.is_connected,
                "xp_aircraft_icao": xp_connector.detected_icao,
                "xp_aircraft_tailnum": xp_connector.detected_tailnum,
                "flight_phase": flight_tracker.phase,
                "telemetry": xp_connector.telemetry,
                "touchdown": {
                    "fpm": flight_tracker.touchdown_fpm,
                    "g": flight_tracker.touchdown_g,
                    "rating": flight_tracker.touchdown_rating
                }
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.1) # 10 Hz refresh
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
