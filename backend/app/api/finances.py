import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.core.database import get_db
from app.models.schema import FinancialTransaction, Company
from app.services.economy import EconomyService

logger = logging.getLogger("SkyOps.Finances")
router = APIRouter(prefix="/finances", tags=["Finances"])

class AdvanceTimeRequest(BaseModel):
    days: int = 7

@router.get("/overview")
async def get_financial_overview(db: AsyncSession = Depends(get_db)):
    """
    Restituisce il rendiconto economico completo:
    Stato Patrimoniale, Conto Economico (P&L), Giorno Operativo e stima costi futuri.
    """
    statement = await EconomyService.get_financial_statement(db)
    return statement

@router.get("/ledger")
async def get_financial_ledger(
    limit: int = Query(default=100, ge=1, le=500),
    category: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Restituisce la cronologia dettagliata delle registrazioni contabili (Libro Mastro / Registro Cassa).
    """
    query = select(FinancialTransaction).order_by(desc(FinancialTransaction.id))
    if category and category != "ALL":
        query = query.where(FinancialTransaction.category == category)
        
    query = query.limit(limit)
    res = await db.execute(query)
    transactions = res.scalars().all()
    return transactions

@router.post("/advance_time")
async def advance_operating_cycle(req: AdvanceTimeRequest, db: AsyncSession = Depends(get_db)):
    """
    Simula il passaggio del tempo virtuale (es. 1 settimana / +7 giorni).
    Calcola e addebita i costi fissi (hangaraggio e polizze assicurative) per tutti
    gli aeromobili di proprietà registrati in flotta.
    """
    if req.days < 1 or req.days > 90:
        raise HTTPException(status_code=400, detail="L'avanzamento deve essere compreso tra 1 e 90 giorni.")
        
    result = await EconomyService.advance_operating_cycle(db, days=req.days)
    return {
        "status": "success",
        "message": f"Tempo operativo avanzato con successo di {req.days} giorni (Giorno {result['new_day']}).",
        "data": result
    }

@router.get("/projections")
async def get_projected_costs(days: int = Query(default=7, ge=1, le=90), db: AsyncSession = Depends(get_db)):
    """
    Restituisce la stima dei costi fissi per il prossimo ciclo operativo indicato.
    """
    projections = await EconomyService.get_projected_fixed_costs(db, days=days)
    return projections
