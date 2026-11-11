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
async def get_financial_overview(
    month: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Restituisce il rendiconto economico completo (Mese Operativo Reale):
    Stato Patrimoniale, Conto Economico (P&L) mensile o storico, e previsione oneri mensili.
    """
    statement = await EconomyService.get_financial_statement(db, month_filter=month)
    return statement

@router.get("/ledger")
async def get_financial_ledger(
    limit: int = Query(default=150, ge=1, le=500),
    category: Optional[str] = Query(default=None),
    month: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Restituisce la cronologia dettagliata delle registrazioni contabili (Libro Mastro / Registro Cassa).
    """
    query = select(FinancialTransaction).order_by(desc(FinancialTransaction.id))
    if category and category != "ALL":
        query = query.where(FinancialTransaction.category == category)
    if month and month != "ALL":
        query = query.where(FinancialTransaction.operating_month == month)
        
    query = query.limit(limit)
    res = await db.execute(query)
    transactions = res.scalars().all()
    return transactions

@router.post("/sync_month")
async def sync_operating_month(db: AsyncSession = Depends(get_db)):
    """
    Sincronizza il Mese Operativo con il calendario reale di sistema e addebita eventuali mesi trascorsi.
    """
    result = await EconomyService.sync_operating_months(db)
    return {
        "status": "success",
        "data": result
    }

@router.get("/projections")
async def get_projected_costs(db: AsyncSession = Depends(get_db)):
    """
    Restituisce il dettaglio previsto dei costi fissi mensili per tutta la flotta di proprietà.
    """
    return await EconomyService.get_projected_monthly_fixed_costs(db)
