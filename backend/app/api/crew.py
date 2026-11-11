from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.schema import CrewMember
from app.services.economy import CATEGORY_SPECS

router = APIRouter(prefix="/crew", tags=["Crew"])


class HireCrewRequest(BaseModel):
    category: str  # "GA", "BIZJET", "AIRLINER"
    name: Optional[str] = None


@router.get("/")
async def get_crew_roster(db: AsyncSession = Depends(get_db)):
    """
    Restituisce il personale fisso assunto in azienda e il listino per assumere
    equipaggi fissi mensili per ciascuna categoria (vs tariffa oraria freelance).
    """
    res = await db.execute(select(CrewMember).where(CrewMember.is_active == True).order_by(CrewMember.id))
    hired = res.scalars().all()
    hired_by_cat = {c.category: c for c in hired}

    catalog = []
    for cat_key in ["GA", "BIZJET", "AIRLINER"]:
        spec = CATEGORY_SPECS[cat_key]
        salary = spec["crew_monthly_salary_eur"]
        hourly = spec["crew_hourly_rate_eur"]
        breakeven_h = round(salary / hourly, 1) if hourly > 0 else 0.0
        active_member = hired_by_cat.get(cat_key)
        catalog.append({
            "category": cat_key,
            "category_label": spec["label"],
            "role_label": spec["crew_label"],
            "monthly_salary_eur": salary,
            "freelance_hourly_eur": hourly,
            "breakeven_hours_per_month": breakeven_h,
            "is_hired": active_member is not None,
            "hired_member": active_member,
        })

    return {
        "hired": hired,
        "catalog": catalog,
        "total_monthly_salaries_eur": round(sum(c.monthly_salary_eur or 0.0 for c in hired), 2),
    }


@router.post("/hire")
async def hire_fixed_crew(req: HireCrewRequest, db: AsyncSession = Depends(get_db)):
    """Assume un equipaggio fisso mensile per una classe di aeromobili (azzerando i costi orari a volo)."""
    cat = (req.category or "").strip().upper()
    if cat not in CATEGORY_SPECS:
        raise HTTPException(status_code=400, detail="Categoria equipaggio non valida (GA, BIZJET, AIRLINER).")

    existing = (
        await db.execute(select(CrewMember).where(CrewMember.category == cat, CrewMember.is_active == True))
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Esiste già un equipaggio fisso attivo per la classe {cat} ({existing.name}).")

    spec = CATEGORY_SPECS[cat]
    default_names = {
        "GA": "Comandante Linea GA",
        "BIZJET": "Equipaggio Executive BizJet",
        "AIRLINER": "Equipaggio Linea Commerciale",
    }
    member = CrewMember(
        name=(req.name or "").strip() or default_names.get(cat, f"Equipaggio {cat}"),
        category=cat,
        role_label=spec["crew_label"],
        monthly_salary_eur=spec["crew_monthly_salary_eur"],
        is_active=True,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return {
        "message": f"Assunto '{member.name}' ({member.role_label}) con stipendio fisso di € {member.monthly_salary_eur:,.2f}/mese. I voli {cat} non pagheranno più tariffe orarie freelance!",
        "member": member,
    }


@router.delete("/{crew_id}")
async def fire_fixed_crew(crew_id: int, db: AsyncSession = Depends(get_db)):
    """Licenzia un equipaggio fisso tornando al regime freelance per volo."""
    member = await db.get(CrewMember, crew_id)
    if not member or not member.is_active:
        raise HTTPException(status_code=404, detail="Equipaggio fisso non trovato.")

    member.is_active = False
    await db.commit()
    return {
        "message": f"Contratto chiuso per '{member.name}' ({member.category}). I prossimi voli torneranno a tariffa oraria freelance."
    }
