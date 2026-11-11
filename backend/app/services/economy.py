import logging
import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.schema import Company, Aircraft, FlightLog, MaintenanceEvent, FinancialTransaction, CrewMember

logger = logging.getLogger("SkyOps.Economy")

MONTHS_IT_FULL = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]
MONTHS_IT_SHORT = [
    "", "Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
    "Lug", "Ago", "Set", "Ott", "Nov", "Dic"
]

# Parametri operativi e categorie velivolo basati su standard reali EASA / FAA
CATEGORY_SPECS = {
    "GA": {
        "label": "General Aviation (Monomotori, VLJ, Vision Jet)",
        "avg_mtow_tonnes": 2.7,
        "base_landing_fee_eur": 22.0,
        "fee_per_tonne_eur": 7.50,
        "hangar_monthly_eur": 480.0,
        "insurance_monthly_eur": 640.0,
        "default_lease_rate_eur_h": 320.0,
        "pilots_count": 1,
        "attendants_count": 0,
        "crew_hourly_rate_eur": 90.0,
        "crew_monthly_salary_eur": 1800.0,
        "crew_label": "1 Pilota",
        "handling_per_pax_eur": 15.0,
        "hard_landing_penalty_eur": 150.0,
        "structural_penalty_eur": 450.0,
    },
    "BIZJET": {
        "label": "Business Jet (Phenom 300, Eclipse 550, Citation)",
        "avg_mtow_tonnes": 8.5,
        "base_landing_fee_eur": 65.0,
        "fee_per_tonne_eur": 9.20,
        "hangar_monthly_eur": 1400.0,
        "insurance_monthly_eur": 2080.0,
        "default_lease_rate_eur_h": 850.0,
        "pilots_count": 2,
        "attendants_count": 1,
        "crew_hourly_rate_eur": 240.0,
        "crew_monthly_salary_eur": 4800.0,
        "crew_label": "2 Piloti + 1 Assistente di Volo",
        "handling_per_pax_eur": 45.0,
        "hard_landing_penalty_eur": 450.0,
        "structural_penalty_eur": 1500.0,
    },
    "AIRLINER": {
        "label": "Airliner di Linea (Boeing 737, Airbus A320)",
        "avg_mtow_tonnes": 75.0,
        "base_landing_fee_eur": 280.0,
        "fee_per_tonne_eur": 11.20,
        "hangar_monthly_eur": 5600.0,
        "insurance_monthly_eur": 7800.0,
        "default_lease_rate_eur_h": 1650.0,
        "pilots_count": 2,
        "attendants_count": 4,
        "crew_hourly_rate_eur": 520.0,
        "crew_monthly_salary_eur": 10400.0,
        "crew_label": "2 Piloti + 4 Assistenti di Volo",
        "handling_per_pax_eur": 18.0,
        "hard_landing_penalty_eur": 1200.0,
        "structural_penalty_eur": 4500.0,
    }
}

class EconomyService:
    @staticmethod
    def is_eurocontrol_icao(icao: Optional[str]) -> bool:
        """Restituisce True solo per aeroporti nello spazio aereo Eurocontrol / Europa."""
        code = (icao or "").strip().upper()
        if not code:
            return False
        return code[0] in ("E", "L", "B") or code.startswith(("GC", "GM", "UD", "UG"))

    @staticmethod
    def get_fuel_price_per_kg(category: str = "GA", economy_mode: str = "REALISTIC") -> float:
        """Prezzo realistico Jet-A1 / AvGas al kg alla pompa per categoria e modalità."""
        mode = (economy_mode or "REALISTIC").strip().upper()
        if mode == "STANDARD":
            return 1.05
        cat = (category or "GA").strip().upper()
        prices = {"AIRLINER": 0.90, "BIZJET": 1.25, "GA": 1.35}
        return prices.get(cat, 1.25)

    @staticmethod
    def calculate_route_reward(
        distance_nm: float,
        pax_count: int,
        cargo_kg: float,
        category: str = "GA",
        mtow_kg: float = 0.0,
        job_type: str = "PASSENGER",
        economy_mode: str = "REALISTIC"
    ) -> float:
        """
        Calcola ricavi commerciali realistici senza doppio conteggio distanza + pax:
        - AIRLINER: tariffa biglietto + ancillari a passeggero + eventuale belly cargo
        - BIZJET: noleggio orario/distanza dell'intero jet scalato su MTOW + catering VIP
        - GA: aerotaxi proporzionato a MTOW e distanza + pax/cargo
        """
        cat = (category or "GA").strip().upper()
        specs = CATEGORY_SPECS.get(cat, CATEGORY_SPECS["GA"])
        mtow_t = (mtow_kg / 1000.0) if (mtow_kg and mtow_kg > 0) else specs["avg_mtow_tonnes"]
        dist = max(0.0, float(distance_nm or 0.0))
        pax = max(0, int(pax_count or 0))
        cargo = max(0.0, float(cargo_kg or 0.0))

        if cat == "AIRLINER":
            if pax > 0:
                pax_yield = 80.0 + min(185.0, dist * 0.062)
                raw = (pax * pax_yield) + (cargo * 0.40)
            else:
                raw = cargo * (0.45 + dist * 0.0012)
            raw = max(1200.0, raw)
        elif cat == "BIZJET":
            w_mult = 0.72 + (mtow_t / 45.0)
            raw = (dist * 13.8 * w_mult) + (pax * 45.0) + (cargo * 0.40)
            raw = max(1400.0, raw)
        else:
            w_mult = 0.45 + (mtow_t / 6.0)
            raw = (dist * 6.4 * w_mult) + (pax * 55.0) + (cargo * 0.45)
            raw = max(320.0, raw)

        jtype = (job_type or "PASSENGER").strip().upper()
        if jtype == "MEDEVAC":
            raw *= 1.22
        elif jtype == "VIP":
            raw *= 1.15

        if (economy_mode or "REALISTIC").strip().upper() == "STANDARD":
            raw *= 1.25

        return float(round(raw, 0))

    @staticmethod
    def calculate_flight_financials(
        category: str,
        fuel_burned_kg: float,
        flight_hours: float,
        job_reward: float,
        is_leased: bool = False,
        lease_rate_hourly: float = 0.0,
        is_home_base: bool = False,
        exclude_crew_cost: bool = False,
        mtow_kg: float = 0.0,
        distance_nm: float = 0.0,
        pax_count: int = 0,
        is_ifr: bool = True,
        has_salaried_crew: bool = False,
        company_reputation: float = 100.0,
        touchdown_rating: Optional[str] = None,
        max_g: float = 1.0,
        min_g: float = 1.0,
        origin_icao: str = "",
        destination_icao: str = "",
        economy_mode: str = "REALISTIC"
    ) -> Dict[str, Any]:
        """
        Calcola il Trip P&L completo in modalità REALISTIC (margini reali 4–12%) o STANDARD.
        """
        cat = (category or "GA").strip().upper()
        specs = CATEGORY_SPECS.get(cat, CATEGORY_SPECS["GA"])
        mode = (economy_mode or "REALISTIC").strip().upper()
        cost_realism = 1.0 if mode == "REALISTIC" else 0.60
        mtow_t = (mtow_kg / 1000.0) if (mtow_kg and mtow_kg > 0) else specs["avg_mtow_tonnes"]
        
        # 1. Carburante a fine volo: € 0 (già addebitato alla pompa al rifornimento)
        fuel_cost = 0.0
        
        # 2. Tassa d'atterraggio (Landing Fee reale su MTOW effettivo, scontata alla Base Operativa)
        landing_params = {
            "GA": (22.0, 7.50),
            "BIZJET": (140.0, 11.50),
            "AIRLINER": (280.0, 5.20),
        }
        base_l, per_t_l = landing_params.get(cat, (22.0, 7.50))
        base_fee = base_l + (mtow_t * per_t_l)
        if is_home_base:
            multiplier = 0.65 if is_leased else 0.30
            discount_pct = 35 if is_leased else 70
        else:
            multiplier = 1.0
            discount_pct = 0
        landing_fee = round(base_fee * multiplier, 2)

        # 3. Tariffe Rotta / Navigazione Eurocontrol + TNC (solo IFR in spazio Eurocontrol)
        if origin_icao or destination_icao:
            orig_ec = EconomyService.is_eurocontrol_icao(origin_icao)
            dest_ec = EconomyService.is_eurocontrol_icao(destination_icao)
            if orig_ec and dest_ec:
                eurocontrol_factor = 1.0
            elif orig_ec or dest_ec:
                eurocontrol_factor = 0.45
            else:
                eurocontrol_factor = 0.0
        else:
            eurocontrol_factor = 1.0

        nav_fee = 0.0
        if is_ifr and eurocontrol_factor > 0 and distance_nm > 0 and mtow_t >= 2.0:
            dist_km = distance_nm * 1.852
            enroute = math.sqrt(mtow_t / 50.0) * (dist_km / 100.0) * 65.0 * eurocontrol_factor
            tnc_rates = {"GA": 15.0, "BIZJET": 75.0, "AIRLINER": 320.0}
            tnc = tnc_rates.get(cat, 15.0) * (1.0 if eurocontrol_factor == 1.0 else 0.5)
            nav_fee = round(enroute + tnc, 2)
        nav_exempt_reason = None
        if not is_ifr:
            nav_exempt_reason = "VFR"
        elif eurocontrol_factor == 0.0:
            nav_exempt_reason = "EXTRA_EU"
        elif mtow_t < 2.0:
            nav_exempt_reason = "MTOW_UNDER_2T"

        # 4. Ground Handling / FBO + Catering & Diritti Passeggeri (esenti su voli VFR solo/privati)
        handling_fee = 0.0
        if is_ifr and (job_reward > 0 or pax_count > 0):
            hb_hand_mult = 0.70 if (is_home_base and not is_leased) else 1.0
            if cat == "AIRLINER":
                handling_raw = (1250.0 * hb_hand_mult) + (max(0, pax_count) * 10.0)
            elif cat == "BIZJET":
                fbo_base = (350.0 + mtow_t * 42.0) * hb_hand_mult
                handling_raw = fbo_base + (max(0, pax_count) * 50.0)
            else:
                handling_raw = (45.0 * hb_hand_mult) + (max(0, pax_count) * 5.0)
            handling_fee = round(handling_raw * cost_realism, 2)

        # 5. Riserva Manutenzione Oraria (Power-by-the-Hour / Check C-D)
        if cat == "AIRLINER":
            res_rate_h = 680.0 + (mtow_t * 2.8)
        elif cat == "BIZJET":
            res_rate_h = 320.0 + (mtow_t * 32.0)
        else:
            res_rate_h = 35.0 + (mtow_t * 30.0)
        lease_res_mult = 0.35 if is_leased else 1.0
        maint_reserve_cost = round(flight_hours * res_rate_h * lease_res_mult * cost_realism, 2)

        # 6. Costo Noleggio se aereo noleggiato
        lease_cost = round(flight_hours * lease_rate_hourly, 2) if is_leased else 0.0

        # 7. Costo Equipaggio (Solo VFR -> 0, Assunto Fisso -> 0 orario, altrimenti Freelance)
        crew_hourly = specs.get("crew_hourly_rate_eur", 90.0)
        if exclude_crew_cost:
            crew_cost = 0.0
            crew_source = "SOLO_VFR"
        elif has_salaried_crew:
            crew_cost = 0.0
            crew_source = "SALARIED"
        else:
            crew_cost = round(flight_hours * crew_hourly, 2)
            crew_source = "FREELANCE"

        # 8. Sistema Reputazione & Bonus Qualità / Penali Atterraggio
        rep = max(0.0, min(100.0, company_reputation if company_reputation is not None else 100.0))
        rep_bonus_pct = 0.0
        if job_reward > 0:
            if rep >= 95.0:
                rep_bonus_pct = 10.0
            elif rep >= 85.0:
                rep_bonus_pct = 5.0
            elif rep < 50.0:
                rep_bonus_pct = -20.0
            elif rep < 70.0:
                rep_bonus_pct = -10.0
            if touchdown_rating == "BUTTER":
                rep_bonus_pct += 5.0

        reputation_bonus_eur = round(job_reward * (rep_bonus_pct / 100.0), 2) if job_reward > 0 else 0.0
        adjusted_gross_revenue = round(max(0.0, job_reward + reputation_bonus_eur), 2)

        # 9. Costi Indiretti (IOC: GDS, carte di credito, broker, accantonamento EU261, OCC)
        ioc_pct_map = {"GA": 0.02, "BIZJET": 0.045, "AIRLINER": 0.08}
        ioc_pct = ioc_pct_map.get(cat, 0.02) * (1.0 if mode == "REALISTIC" else 0.5)
        ioc_cost = round(adjusted_gross_revenue * ioc_pct, 2) if adjusted_gross_revenue > 0 else 0.0

        reputation_delta = 0.0
        penalty_eur = 0.0
        if touchdown_rating == "BUTTER":
            reputation_delta += 1.5
        elif touchdown_rating == "GOOD":
            reputation_delta += 0.5
        elif touchdown_rating == "HARD":
            reputation_delta -= 3.0
            base_pen = specs.get("hard_landing_penalty_eur", 150.0)
            penalty_eur = round(base_pen if pax_count > 0 else base_pen * 0.5, 2)
        elif touchdown_rating == "STRUCTURAL_DAMAGE":
            reputation_delta -= 8.0
            penalty_eur = round(specs.get("structural_penalty_eur", 450.0), 2)

        if max_g > 2.8 or min_g < 0.0:
            reputation_delta -= 2.0

        reputation_delta = round(reputation_delta, 1)
        new_reputation = round(max(0.0, min(100.0, rep + reputation_delta)), 1)
        
        # 10. Spese totali e utile netto
        total_expenses = round(
            fuel_cost + landing_fee + nav_fee + handling_fee + maint_reserve_cost + lease_cost + crew_cost + ioc_cost + penalty_eur,
            2
        )
        net_profit = round(adjusted_gross_revenue - total_expenses, 2)
        
        return {
            "economy_mode": mode,
            "base_reward": round(job_reward, 2),
            "reputation_bonus_eur": reputation_bonus_eur,
            "reputation_bonus_pct": rep_bonus_pct,
            "gross_revenue": adjusted_gross_revenue,
            "fuel_cost": fuel_cost,
            "landing_fee": landing_fee,
            "nav_fee": nav_fee,
            "nav_exempt_reason": nav_exempt_reason,
            "eurocontrol_area": eurocontrol_factor > 0,
            "handling_fee": handling_fee,
            "maint_reserve_cost": maint_reserve_cost,
            "ioc_cost": ioc_cost,
            "lease_cost": lease_cost,
            "crew_cost": crew_cost,
            "crew_source": crew_source,
            "crew_excluded": exclude_crew_cost,
            "has_salaried_crew": has_salaried_crew,
            "crew_label": specs.get("crew_label", "1 Pilota"),
            "crew_hourly_rate_eur": crew_hourly,
            "penalty_eur": penalty_eur,
            "reputation_delta": reputation_delta,
            "new_reputation": new_reputation,
            "flight_rules": "IFR" if is_ifr else "VFR",
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "is_home_base": is_home_base,
            "landing_fee_discount_pct": discount_pct
        }

    @staticmethod
    def current_ym() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m")

    @staticmethod
    def format_operating_month_it(ym: Optional[str], short: bool = False) -> str:
        raw = (ym or "").strip()
        try:
            y_str, m_str = raw.split("-")
            m_idx = int(m_str)
            if 1 <= m_idx <= 12:
                names = MONTHS_IT_SHORT if short else MONTHS_IT_FULL
                return f"{names[m_idx]} {y_str}"
        except Exception:
            pass
        now = datetime.now(timezone.utc)
        names = MONTHS_IT_SHORT if short else MONTHS_IT_FULL
        return f"{names[now.month]} {now.year}"

    @staticmethod
    def iter_elapsed_months(start_ym: str, end_ym: str) -> List[str]:
        """Genera ogni mese YYYY-MM da start_ym (incluso) fino a end_ym (escluso)."""
        try:
            sy, sm = map(int, start_ym.split("-"))
            ey, em = map(int, end_ym.split("-"))
        except Exception:
            return []
        res: List[str] = []
        y, m = sy, sm
        while (y, m) < (ey, em):
            res.append(f"{y:04d}-{m:02d}")
            m += 1
            if m > 12:
                m = 1
                y += 1
        return res

    @staticmethod
    def calculate_fixed_monthly_costs(category: str) -> Dict[str, float]:
        """Calcola i costi fissi mensili (hangar + assicurazione) per categoria."""
        specs = CATEGORY_SPECS.get(category, CATEGORY_SPECS["GA"])
        hangar = round(specs["hangar_monthly_eur"], 2)
        insurance = round(specs["insurance_monthly_eur"], 2)
        return {
            "hangar_eur": hangar,
            "insurance_eur": insurance,
            "total_fixed_eur": round(hangar + insurance, 2)
        }

    @staticmethod
    async def record_transaction(
        session: AsyncSession,
        category: str,
        title: str,
        amount_eur: float,
        description: Optional[str] = None,
        aircraft_tail: Optional[str] = None,
        flight_id: Optional[int] = None,
        company: Optional[Company] = None,
        operating_month: Optional[str] = None
    ) -> FinancialTransaction:
        """
        Registra una transazione nel libro mastro (Ledger) e aggiorna la cassa aziendale.
        """
        if not company:
            comp_res = await session.execute(select(Company).limit(1))
            company = comp_res.scalars().first()
            if not company:
                company = Company(cash_balance=175000.0, operating_day=1, operating_month=EconomyService.current_ym())
                session.add(company)
                await session.flush()

        company.cash_balance = round(company.cash_balance + amount_eur, 2)
        tx_month = operating_month or company.operating_month or EconomyService.current_ym()
        
        tx = FinancialTransaction(
            timestamp=datetime.now(timezone.utc),
            operating_day=company.operating_day or 1,
            operating_month=tx_month,
            category=category,
            title=title,
            description=description,
            amount_eur=round(amount_eur, 2),
            balance_after_eur=company.cash_balance,
            related_aircraft_tail=aircraft_tail,
            related_flight_id=flight_id
        )
        session.add(tx)
        return tx

    @staticmethod
    async def get_projected_monthly_fixed_costs(session: AsyncSession) -> Dict[str, Any]:
        """
        Calcola i costi fissi mensili previsti per tutta la flotta di proprietà alla chiusura del mese.
        """
        ac_res = await session.execute(select(Aircraft).where(Aircraft.ownership == "OWNED"))
        owned_aircraft = ac_res.scalars().all()
        cm_res = await session.execute(select(CrewMember).where(CrewMember.is_active == True))
        active_crew = cm_res.scalars().all()
        
        details = []
        total_hangar = 0.0
        total_insurance = 0.0
        total_financing = 0.0
        total_salaries = round(sum(c.monthly_salary_eur or 0.0 for c in active_crew), 2)
        
        for ac in owned_aircraft:
            specs = CATEGORY_SPECS.get(ac.category, CATEGORY_SPECS["GA"])
            hangar = round(specs["hangar_monthly_eur"], 2)
            insurance = round(specs["insurance_monthly_eur"], 2)
            financing = 0.0
            if (ac.remaining_payments_months or 0) > 0 and (ac.monthly_payment_eur or 0.0) > 0:
                financing = round(min(ac.monthly_payment_eur, ac.financed_amount_remaining_eur or ac.monthly_payment_eur), 2)
                
            subtotal = round(hangar + insurance + financing, 2)
            total_hangar += hangar
            total_insurance += insurance
            total_financing += financing
            details.append({
                "aircraft_id": ac.id,
                "tail_number": ac.tail_number,
                "name": ac.name,
                "category": ac.category,
                "hangar_eur": hangar,
                "insurance_eur": insurance,
                "financing_eur": financing,
                "remaining_months": ac.remaining_payments_months or 0,
                "subtotal_eur": subtotal
            })
            
        return {
            "period": "MONTHLY",
            "owned_aircraft_count": len(owned_aircraft),
            "hired_crew_count": len(active_crew),
            "total_hangar_eur": round(total_hangar, 2),
            "total_insurance_eur": round(total_insurance, 2),
            "total_financing_eur": round(total_financing, 2),
            "total_crew_salaries_eur": total_salaries,
            "total_fixed_eur": round(total_hangar + total_insurance + total_financing + total_salaries, 2),
            "aircraft_breakdown": details
        }

    @staticmethod
    async def sync_operating_months(session: AsyncSession, target_ym: Optional[str] = None) -> Dict[str, Any]:
        """
        Sincronizza il Mese Operativo con il calendario reale.
        Addebita automaticamente Hangar, Assicurazione e Rate Mensili per OGNI mese reale trascorso
        senza tetti massimi (realismo gestionale completo).
        """
        comp_res = await session.execute(select(Company).limit(1))
        company = comp_res.scalars().first()
        real_ym = (target_ym or EconomyService.current_ym()).strip()
        if not company:
            return {"operating_month": real_ym, "closed_months": [], "total_deductions_eur": 0.0}

        now_utc = datetime.now(timezone.utc)
        company.virtual_date = now_utc

        if not company.operating_month:
            company.operating_month = real_ym
            await session.commit()
            return {"operating_month": real_ym, "closed_months": [], "total_deductions_eur": 0.0}

        if real_ym <= company.operating_month:
            await session.commit()
            return {"operating_month": company.operating_month, "closed_months": [], "total_deductions_eur": 0.0}

        elapsed_months = EconomyService.iter_elapsed_months(company.operating_month, real_ym)
        if not elapsed_months:
            company.operating_month = real_ym
            await session.commit()
            return {"operating_month": real_ym, "closed_months": [], "total_deductions_eur": 0.0}

        ac_res = await session.execute(select(Aircraft).where(Aircraft.ownership == "OWNED"))
        owned_aircraft = ac_res.scalars().all()
        cm_res = await session.execute(select(CrewMember).where(CrewMember.is_active == True))
        active_crew = cm_res.scalars().all()

        total_deductions = 0.0
        closed_months_summary = []

        for m_ym in elapsed_months:
            m_label = EconomyService.format_operating_month_it(m_ym)
            month_total = 0.0
            for cm in active_crew:
                sal = round(cm.monthly_salary_eur or 0.0, 2)
                if sal > 0:
                    await EconomyService.record_transaction(
                        session=session,
                        category="CREW_SALARY",
                        title=f"Stipendio Fisso {cm.name} ({cm.category} • {m_label})",
                        amount_eur=-sal,
                        description=f"Stipendio mensile equipaggio fisso ({cm.role_label}) — {m_label}",
                        company=company,
                        operating_month=m_ym
                    )
                    month_total += sal

            for ac in owned_aircraft:
                specs = CATEGORY_SPECS.get(ac.category, CATEGORY_SPECS["GA"])
                hangar_cost = round(specs["hangar_monthly_eur"], 2)
                insurance_cost = round(specs["insurance_monthly_eur"], 2)
                financing_cost = 0.0

                if hangar_cost > 0:
                    await EconomyService.record_transaction(
                        session=session,
                        category="FIXED_HANGAR",
                        title=f"Rimessaggio Hangar {ac.tail_number} ({m_label})",
                        amount_eur=-hangar_cost,
                        description=f"Canone mensile hangar per {ac.name} presso {ac.current_icao} ({m_label})",
                        aircraft_tail=ac.tail_number,
                        company=company,
                        operating_month=m_ym
                    )
                    month_total += hangar_cost

                if insurance_cost > 0:
                    await EconomyService.record_transaction(
                        session=session,
                        category="FIXED_INSURANCE",
                        title=f"Polizza Corpi & RC {ac.tail_number} ({m_label})",
                        amount_eur=-insurance_cost,
                        description=f"Copertura assicurativa mensile Kasko/RC {ac.name} ({m_label})",
                        aircraft_tail=ac.tail_number,
                        company=company,
                        operating_month=m_ym
                    )
                    month_total += insurance_cost

                if (ac.remaining_payments_months or 0) > 0 and (ac.monthly_payment_eur or 0.0) > 0:
                    rem_debt = ac.financed_amount_remaining_eur or 0.0
                    if ac.remaining_payments_months == 1 and rem_debt > 0:
                        financing_cost = round(rem_debt, 2)
                    else:
                        financing_cost = round(min(ac.monthly_payment_eur, rem_debt) if rem_debt > 0 else ac.monthly_payment_eur, 2)

                    if financing_cost > 0:
                        mode_label = "Leasing Finanziario" if ac.acquisition_mode == "FINANCIAL_LEASE" else "Mutuo Aeronautico"
                        new_rem_months = max(0, (ac.remaining_payments_months or 0) - 1)
                        await EconomyService.record_transaction(
                            session=session,
                            category="FINANCING",
                            title=f"Rata Mensile {mode_label} {ac.tail_number} ({m_label})",
                            amount_eur=-financing_cost,
                            description=f"Canone mensile {m_label} per {ac.name} — Rate residue: {new_rem_months} mesi",
                            aircraft_tail=ac.tail_number,
                            company=company,
                            operating_month=m_ym
                        )
                        month_total += financing_cost
                        ac.financed_amount_remaining_eur = max(0.0, round(rem_debt - financing_cost, 2))
                        ac.remaining_payments_months = new_rem_months
                        if ac.remaining_payments_months == 0 or ac.financed_amount_remaining_eur <= 0.01:
                            ac.acquisition_mode = "OWNED_CASH"
                            ac.monthly_payment_eur = 0.0
                            ac.remaining_payments_months = 0
                            ac.financed_amount_remaining_eur = 0.0

            total_deductions += month_total
            closed_months_summary.append({
                "ym": m_ym,
                "label": m_label,
                "total_deductions_eur": round(month_total, 2)
            })

        company.operating_month = real_ym
        await session.commit()
        await session.refresh(company)

        return {
            "operating_month": company.operating_month,
            "operating_month_label": EconomyService.format_operating_month_it(company.operating_month),
            "closed_months": closed_months_summary,
            "total_deductions_eur": round(total_deductions, 2),
            "new_cash_balance_eur": company.cash_balance
        }

    @staticmethod
    async def get_financial_statement(session: AsyncSession, month_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Genera il Rendiconto Finanziario Completo sincronizzando prima il Mese Operativo reale:
        - Stato Patrimoniale (Attivo Circolante, Flotta, Patrimonio Netto)
        - Conto Economico filtrabile per Mese Operativo o Storico Totale
        - Previsioni Chiusura Mese Operativo Corrente
        """
        await EconomyService.sync_operating_months(session)

        comp_res = await session.execute(select(Company).limit(1))
        company = comp_res.scalars().first()
        curr_ym = EconomyService.current_ym()
        if not company:
            return {
                "operating_day": 1,
                "operating_month": curr_ym,
                "operating_month_label": EconomyService.format_operating_month_it(curr_ym),
                "selected_period": "ALL",
                "available_months": [{"ym": curr_ym, "label": EconomyService.format_operating_month_it(curr_ym)}],
                "virtual_date": datetime.now(timezone.utc).isoformat(),
                "balance_sheet": {
                    "cash_balance_eur": 0.0,
                    "fleet_book_value_eur": 0.0,
                    "financed_debt_eur": 0.0,
                    "total_net_worth_eur": 0.0,
                    "owned_aircraft_count": 0
                },
                "income_statement": {
                    "gross_revenue_eur": 0.0,
                    "direct_operating_costs": {"total_eur": 0.0, "fuel_eur": 0.0, "landing_fees_eur": 0.0, "aircraft_leases_eur": 0.0, "crew_eur": 0.0},
                    "maintenance_costs": {"total_eur": 0.0},
                    "fixed_overheads": {"total_eur": 0.0, "hangar_eur": 0.0, "insurance_eur": 0.0, "financing_eur": 0.0},
                    "total_expenses_eur": 0.0,
                    "net_profit_eur": 0.0,
                    "profit_margin_pct": 0.0
                },
                "upcoming_fixed_costs_monthly": {"period": "MONTHLY", "owned_aircraft_count": 0, "total_hangar_eur": 0.0, "total_insurance_eur": 0.0, "total_financing_eur": 0.0, "total_fixed_eur": 0.0, "aircraft_breakdown": []}
            }
            
        # 2. Owned aircraft valuation & active financing debt
        ac_res = await session.execute(select(Aircraft).where(Aircraft.ownership == "OWNED"))
        owned_aircraft = ac_res.scalars().all()
        fleet_book_value = sum(ac.purchase_price_eur or 0.0 for ac in owned_aircraft)
        financed_debt = sum(ac.financed_amount_remaining_eur or 0.0 for ac in owned_aircraft)
        
        # 3. Aggregates from FinancialTransactions (with optional month filter)
        tx_res = await session.execute(select(FinancialTransaction))
        all_transactions = tx_res.scalars().all()

        op_month = company.operating_month or curr_ym
        month_set = {op_month}
        for t in all_transactions:
            m_val = getattr(t, "operating_month", None) or (t.timestamp.strftime("%Y-%m") if t.timestamp else None)
            if m_val:
                month_set.add(m_val)
        available_months = [
            {"ym": ym, "label": EconomyService.format_operating_month_it(ym)}
            for ym in sorted(month_set, reverse=True)
        ]

        selected_period = month_filter.strip() if (month_filter and month_filter.strip() and month_filter.strip().upper() != "ALL") else "ALL"
        if selected_period != "ALL":
            transactions = [
                t for t in all_transactions
                if (getattr(t, "operating_month", None) or (t.timestamp.strftime("%Y-%m") if t.timestamp else "")) == selected_period
            ]
        else:
            transactions = all_transactions
        
        revenue_flight = sum(t.amount_eur for t in transactions if t.category in ["REVENUE", "REVENUE_FLIGHT"] and t.amount_eur > 0)
        expense_fuel = abs(sum(t.amount_eur for t in transactions if t.category in ["FUEL", "EXPENSE_FUEL"]))
        expense_landing = abs(sum(t.amount_eur for t in transactions if t.category in ["LANDING_FEE", "EXPENSE_LANDING"]))
        expense_nav = abs(sum(t.amount_eur for t in transactions if t.category in ["NAV_FEE"]))
        expense_handling = abs(sum(t.amount_eur for t in transactions if t.category in ["HANDLING"]))
        expense_penalty = abs(sum(t.amount_eur for t in transactions if t.category in ["PENALTY"]))
        expense_lease = abs(sum(t.amount_eur for t in transactions if t.category in ["LEASE", "EXPENSE_LEASE"]))
        expense_crew = abs(sum(t.amount_eur for t in transactions if t.category in ["CREW", "EXPENSE_CREW"]))
        expense_maint_res = abs(sum(t.amount_eur for t in transactions if t.category in ["MAINT_RESERVE"]))
        expense_ioc = abs(sum(t.amount_eur for t in transactions if t.category in ["IOC"]))
        expense_maint = abs(sum(t.amount_eur for t in transactions if t.category in ["MAINTENANCE", "EXPENSE_MAINTENANCE"]))
        expense_hangar = abs(sum(t.amount_eur for t in transactions if t.category in ["FIXED_HANGAR"]))
        expense_insurance = abs(sum(t.amount_eur for t in transactions if t.category in ["FIXED_INSURANCE"]))
        expense_financing = abs(sum(t.amount_eur for t in transactions if t.category in ["FINANCING"]))
        expense_crew_salary = abs(sum(t.amount_eur for t in transactions if t.category in ["CREW_SALARY"]))
        
        # Fallback only if database has literally zero FinancialTransactions
        if not all_transactions:
            fl_res = await session.execute(select(FlightLog))
            flights = fl_res.scalars().all()
            revenue_flight = sum(f.revenue_usd or 0.0 for f in flights)
            expense_fuel = sum(f.fuel_cost_usd or 0.0 for f in flights)
            expense_landing = sum(f.landing_fee_usd or 0.0 for f in flights)
            expense_nav = sum(getattr(f, "nav_fee_eur", 0.0) or 0.0 for f in flights)
            expense_handling = sum(getattr(f, "handling_fee_eur", 0.0) or 0.0 for f in flights)
            expense_penalty = sum(getattr(f, "penalty_eur", 0.0) or 0.0 for f in flights)
            expense_maint_res = sum(getattr(f, "maint_reserve_eur", 0.0) or 0.0 for f in flights)
            expense_ioc = sum(getattr(f, "ioc_cost_eur", 0.0) or 0.0 for f in flights)
            expense_lease = sum(f.lease_cost_usd or 0.0 for f in flights)
            expense_crew = sum(f.crew_cost_usd or 0.0 for f in flights)
            
            mv_res = await session.execute(select(MaintenanceEvent))
            events = mv_res.scalars().all()
            expense_maint = sum(m.cost_usd or 0.0 for m in events)
            
        direct_operating_costs = round(
            expense_fuel + expense_landing + expense_nav + expense_handling + expense_maint_res + expense_ioc + expense_penalty + expense_lease + expense_crew,
            2
        )
        fixed_overheads = round(expense_hangar + expense_insurance + expense_financing + expense_crew_salary, 2)
        total_expenses = round(direct_operating_costs + expense_maint + fixed_overheads, 2)
        net_profit = round(revenue_flight - total_expenses, 2)
        margin_pct = round((net_profit / revenue_flight * 100.0), 1) if revenue_flight > 0 else 0.0
        
        # Next month closing projection
        projections = await EconomyService.get_projected_monthly_fixed_costs(session)
        
        return {
            "operating_day": company.operating_day or 1,
            "operating_month": op_month,
            "operating_month_label": EconomyService.format_operating_month_it(op_month),
            "selected_period": selected_period,
            "available_months": available_months,
            "economy_mode": (company.economy_mode or "REALISTIC").upper(),
            "reputation": company.reputation if company.reputation is not None else 100.0,
            "virtual_date": (company.virtual_date or datetime.now(timezone.utc)).isoformat(),
            
            # Stato Patrimoniale (Balance Sheet)
            "balance_sheet": {
                "cash_balance_eur": company.cash_balance,
                "fleet_book_value_eur": round(fleet_book_value, 2),
                "financed_debt_eur": round(financed_debt, 2),
                "total_net_worth_eur": round(company.cash_balance + fleet_book_value - financed_debt, 2),
                "owned_aircraft_count": len(owned_aircraft)
            },
            
            # Conto Economico (P&L Statement)
            "income_statement": {
                "gross_revenue_eur": round(revenue_flight, 2),
                "direct_operating_costs": {
                    "total_eur": direct_operating_costs,
                    "fuel_eur": round(expense_fuel, 2),
                    "landing_fees_eur": round(expense_landing, 2),
                    "nav_fees_eur": round(expense_nav, 2),
                    "handling_fees_eur": round(expense_handling, 2),
                    "maint_reserves_eur": round(expense_maint_res, 2),
                    "ioc_costs_eur": round(expense_ioc, 2),
                    "penalties_eur": round(expense_penalty, 2),
                    "aircraft_leases_eur": round(expense_lease, 2),
                    "crew_eur": round(expense_crew, 2)
                },
                "maintenance_costs": {
                    "total_eur": round(expense_maint, 2)
                },
                "fixed_overheads": {
                    "total_eur": fixed_overheads,
                    "hangar_eur": round(expense_hangar, 2),
                    "insurance_eur": round(expense_insurance, 2),
                    "financing_eur": round(expense_financing, 2),
                    "crew_salaries_eur": round(expense_crew_salary, 2)
                },
                "total_expenses_eur": total_expenses,
                "net_profit_eur": net_profit,
                "profit_margin_pct": margin_pct
            },
            
            # Previsioni Chiusura Mese Corrente
            "upcoming_fixed_costs_monthly": projections
        }

    @staticmethod
    def get_financial_guide() -> Dict[str, Any]:
        """
        Restituisce la documentazione verosimile e dettagliata delle formule economiche.
        """
        return {
            "currency": "EUR (€)",
            "fuel_rules": {
                "fuel_type": "Jet-A1 Kerosene / AvGas",
                "price_per_kg_eur": 0.90,
                "price_per_litre_approx_eur": 0.72,
                "formula": "Realistico: € 0,90/kg (Airliner) • € 1,25/kg (BizJet) • € 1,35/kg (GA) | Standard: € 1,05/kg",
                "notes": "Paghi SOLO alla pompa quando rifornisci (o aggiungi carburante in X-Plane 12 prima del decollo). In linea con il mercato europeo (~900 €/t Airliner, ~1.250 €/t GAT)."
            },
            "landing_fee_rules": {
                "formula": "Tassa Atterraggio = (Tassa Base + MTOW × Quota/t) × Sconto Base Operativa",
                "notes": "Gli atterraggi presso la tua Base Operativa godono di tariffa residente scontata (-70% per flotta di proprietà, -35% per velivoli a noleggio).",
                "categories": [
                    {
                        "category": "General Aviation (GA)",
                        "base": "€22.00",
                        "per_tonne": "€7.50 / t",
                        "typical_cost": "~€42.00 (es. Cirrus SF50 Vision Jet da 2.7 t)"
                    },
                    {
                        "category": "Business Jet (BIZJET)",
                        "base": "€65.00",
                        "per_tonne": "€9.20 / t",
                        "typical_cost": "~€143.00 (es. Phenom 300 da 8.5 t)"
                    },
                    {
                        "category": "Airliner (AIRLINER)",
                        "base": "€280.00",
                        "per_tonne": "€11.20 / t",
                        "typical_cost": "~€1,120.00 (es. B737-800 da 75 t)"
                    }
                ]
            },
            "revenue_rules": {
                "formula": "Ricavo Incarico = (Distanza NM × Tariffa/NM) + (Passeggeri × Quota/Pax) + (Cargo Kg × Quota/Kg) × Moltiplicatore Urgenza",
                "breakdown": [
                    {"component": "Tariffa Base Distanza", "description": "Da 14.00 € a 28.00 € per miglio nautico in base alla classe."},
                    {"component": "Quota Passeggeri", "description": "Da 90 € a 180 € per passeggero (biglietto / tariffa VIP catering)."},
                    {"component": "Quota Merci (Cargo)", "description": "Circa 1.50 € per kg di merce trasportata."},
                    {"component": "Moltiplicatore Missione", "description": "Voli Sanitari (Medevac) e VIP godono di un bonus urgenza del +15% - +25%."}
                ]
            },
            "rental_rules": {
                "formula": "Costo Noleggio = Ore di Volo Effettive (Block Time) × Tariffa Oraria Noleggio",
                "types": [
                    {"type": "Dry Lease (Noleggio a Secco)", "description": "Tariffa oraria fissa per la cellula. Il carburante è interamente a tuo carico."},
                    {"type": "Wet Lease (Noleggio Completo)", "description": "Include assicurazione e manutenzione ordinaria a carico del noleggiatore."}
                ]
            },
            "crew_rules": {
                "formula": "Freelance a Volo (Ore × Tariffa) OPPURE Equipaggio Assunto Fisso (€/mese = € 0 a volo) OPPURE Volo Solo VFR (€ 0)",
                "notes": "Se assumi un equipaggio fisso per la categoria, paghi uno stipendio mensile fisso e tutti i voli del mese sono a € 0/ora! Break-even: 20 ore di volo/mese.",
                "categories": [
                    {"category": "General Aviation (GA)", "crew": "1 Pilota", "rate": "€ 90/h Freelance • € 1.800/mese Fisso"},
                    {"category": "Business Jet (BIZJET)", "crew": "2 Piloti + 1 A/V", "rate": "€ 240/h Freelance • € 4.800/mese Fisso"},
                    {"category": "Airliner (AIRLINER)", "crew": "2 Piloti + 4 A/V", "rate": "€ 520/h Freelance • € 10.400/mese Fisso"}
                ]
            },
            "eurocontrol_and_handling_rules": {
                "formula": "Eurocontrol+TNC (UE IFR) + FBO/Ground Handling + Riserva Manutenzione Oraria + Costi Indiretti (IOC 2%–8%)",
                "notes": "In modalità REALISTICA (margini netti 4%–12%), ogni volo IFR paga handling, riserve motori/check-C e distribuzione/EU261. Voli extra-UE (es. USA) e VFR sono esenti da Eurocontrol."
            },
            "reputation_rules": {
                "formula": "Reputazione (0–100%) modifica i ricavi charter (+10% se >=95%, +5% extra per Butter Landing) e genera penali per atterraggi duri",
                "notes": "Butter (+1.5%), Good (+0.5%), Hard (-3.0% + risarcimento pax/controllo), Danno Strutturale (-8.0% + penale assicurativa), Over-G (-2.0%)."
            },
            "fixed_costs_rules": {
                "formula": "Costi Fissi Mensili = Hangar + Assicurazione + Eventuale Rata Finanziamento (addebitati automaticamente a ogni cambio mese reale)",
                "notes": "Il Mese Operativo segue il calendario reale: che tu faccia 1 o 100 voli al mese i costi fissi mensili non cambiano. Le pause di più mesi reali maturano tutti i mesi trascorsi. Puoi estinguere in anticipo mutuo/leasing dall'Hangar.",
                "categories": [
                    {"category": "General Aviation (GA)", "hangar": "€ 480 / mese", "insurance": "€ 640 / mese", "total": "€ 1.120 / mese"},
                    {"category": "Business Jet (BIZJET)", "hangar": "€ 1.400 / mese", "insurance": "€ 2.080 / mese", "total": "€ 3.480 / mese"},
                    {"category": "Airliner (AIRLINER)", "hangar": "€ 5.600 / mese", "insurance": "€ 7.800 / mese", "total": "€ 13.400 / mese"}
                ]
            },
            "wear_and_maintenance_rules": {
                "wear_breakdown": [
                    {"part": "Motore", "wear": "0.45% per ora di volo (aumento se EGT/ITT elevate). Revisione generale a 3.500h (TBO)."},
                    {"part": "Cellula", "wear": "0.15% per ora di volo ordinaria. Penalità forte in caso di Over-G (> 2.8G)."},
                    {"part": "Pneumatici & Freni", "wear": "0.4% base + usura da attrito frenante ed energia cinetica all'atterraggio."}
                ],
                "touchdown_impact_table": [
                    {"rating": "Butter Landing", "fpm": "< 160 fpm e < 1.4 G", "impact": "Nessuna usura extra (+0.2% normale)."},
                    {"rating": "Good / Normal", "fpm": "< 300 fpm e < 1.8 G", "impact": "Usura pneumatici standard (+1.5%)."},
                    {"rating": "Hard Landing", "fpm": "> 400 fpm o > 2.0 G", "impact": "+8% usura pneumatici, +3% usura carrello e cellula."},
                    {"rating": "Danno Strutturale", "fpm": "> 600 fpm o > 2.2 G", "impact": "+25% usura immediata, rischio rottura e costo riparazione."}
                ]
            }
        }
