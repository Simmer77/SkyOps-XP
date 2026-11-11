import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.schema import Company, Aircraft, FlightLog, MaintenanceEvent, FinancialTransaction

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
        "crew_label": "1 Pilota",
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
        "crew_label": "2 Piloti + 1 Assistente di Volo",
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
        "crew_label": "2 Piloti + 4 Assistenti di Volo",
    }
}

class EconomyService:
    @staticmethod
    def calculate_flight_financials(
        category: str,
        fuel_burned_kg: float,
        flight_hours: float,
        job_reward: float,
        is_leased: bool = False,
        lease_rate_hourly: float = 0.0,
        is_home_base: bool = False,
        exclude_crew_cost: bool = False
    ) -> Dict[str, Any]:
        """
        Calcola il bilancio finanziario completo del volo in Euro (€).
        Il carburante NON viene addebitato al consumo ma solo al momento del rifornimento.
        """
        specs = CATEGORY_SPECS.get(category, CATEGORY_SPECS["GA"])
        
        # 1. Costo Carburante a fine volo: 0 € (viene addebitato solo quando rifornisci il serbatoio)
        fuel_cost = 0.0
        
        # 2. Tassa d'atterraggio (Landing Fee): base + quota tonnellata MTOW con tariffa agevolata alla Base Operativa
        base_fee = specs["base_landing_fee_eur"] + (specs["avg_mtow_tonnes"] * specs["fee_per_tonne_eur"])
        if is_home_base:
            multiplier = 0.65 if is_leased else 0.30
            discount_pct = 35 if is_leased else 70
        else:
            multiplier = 1.0
            discount_pct = 0
        landing_fee = round(base_fee * multiplier, 2)
        
        # 3. Costo Noleggio se aereo noleggiato (Block hours * tariffa)
        lease_cost = round(flight_hours * lease_rate_hourly, 2) if is_leased else 0.0

        # 4. Costo Equipaggio (Piloti + Assistenti di Volo in base alla classe velivolo, escludibile per VFR / Solo)
        crew_hourly = specs.get("crew_hourly_rate_eur", 90.0)
        crew_cost = 0.0 if exclude_crew_cost else round(flight_hours * crew_hourly, 2)
        
        # 5. Spese totali e utile netto (al netto dei rifornimenti già pagati alla pompa)
        total_expenses = round(fuel_cost + landing_fee + lease_cost + crew_cost, 2)
        net_profit = round(job_reward - total_expenses, 2)
        
        return {
            "gross_revenue": round(job_reward, 2),
            "fuel_cost": fuel_cost,
            "landing_fee": landing_fee,
            "lease_cost": lease_cost,
            "crew_cost": crew_cost,
            "crew_excluded": exclude_crew_cost,
            "crew_label": specs.get("crew_label", "1 Pilota"),
            "crew_hourly_rate_eur": crew_hourly,
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
        
        details = []
        total_hangar = 0.0
        total_insurance = 0.0
        total_financing = 0.0
        
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
            "total_hangar_eur": round(total_hangar, 2),
            "total_insurance_eur": round(total_insurance, 2),
            "total_financing_eur": round(total_financing, 2),
            "total_fixed_eur": round(total_hangar + total_insurance + total_financing, 2),
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

        total_deductions = 0.0
        closed_months_summary = []

        for m_ym in elapsed_months:
            m_label = EconomyService.format_operating_month_it(m_ym)
            month_total = 0.0
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
        expense_lease = abs(sum(t.amount_eur for t in transactions if t.category in ["LEASE", "EXPENSE_LEASE"]))
        expense_crew = abs(sum(t.amount_eur for t in transactions if t.category in ["CREW", "EXPENSE_CREW"]))
        expense_maint = abs(sum(t.amount_eur for t in transactions if t.category in ["MAINTENANCE", "EXPENSE_MAINTENANCE"]))
        expense_hangar = abs(sum(t.amount_eur for t in transactions if t.category in ["FIXED_HANGAR"]))
        expense_insurance = abs(sum(t.amount_eur for t in transactions if t.category in ["FIXED_INSURANCE"]))
        expense_financing = abs(sum(t.amount_eur for t in transactions if t.category in ["FINANCING"]))
        
        # Fallback only if database has literally zero FinancialTransactions
        if not all_transactions:
            fl_res = await session.execute(select(FlightLog))
            flights = fl_res.scalars().all()
            revenue_flight = sum(f.revenue_usd or 0.0 for f in flights)
            expense_fuel = sum(f.fuel_cost_usd or 0.0 for f in flights)
            expense_landing = sum(f.landing_fee_usd or 0.0 for f in flights)
            expense_lease = sum(f.lease_cost_usd or 0.0 for f in flights)
            expense_crew = sum(f.crew_cost_usd or 0.0 for f in flights)
            
            mv_res = await session.execute(select(MaintenanceEvent))
            events = mv_res.scalars().all()
            expense_maint = sum(m.cost_usd or 0.0 for m in events)
            
        direct_operating_costs = round(expense_fuel + expense_landing + expense_lease + expense_crew, 2)
        fixed_overheads = round(expense_hangar + expense_insurance + expense_financing, 2)
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
                    "financing_eur": round(expense_financing, 2)
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
                "fuel_type": "Jet-A1 Kerosene",
                "price_per_kg_eur": settings.DEFAULT_FUEL_PRICE_EUR_PER_KG,
                "price_per_litre_approx_eur": round(settings.DEFAULT_FUEL_PRICE_EUR_PER_KG * 0.80, 2),
                "formula": "Costo Carburante = Kg Riforniti (Delta nel serbatoio) × 1.75 €/kg",
                "notes": "Paghi SOLO alla pompa quando rifornisci (o aggiungi carburante in X-Plane 12 prima del decollo). Il carburante residuo già a bordo e il consumo in volo non generano doppi addebiti."
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
                "formula": "Costo Equipaggio = Ore di Volo (Block Time) × Tariffa Oraria Equipaggio (escludibile su voli solo VFR)",
                "notes": "Puoi disattivare l'addebito dell'equipaggio prima della partenza o in plancia se voli in solitario (Owner-Pilot / VFR senza assistenti).",
                "categories": [
                    {"category": "General Aviation (GA)", "crew": "1 Pilota", "rate": "€ 90.00 / ora"},
                    {"category": "Business Jet (BIZJET)", "crew": "2 Piloti + 1 Assistente di Volo", "rate": "€ 240.00 / ora"},
                    {"category": "Airliner (AIRLINER)", "crew": "2 Piloti + 4 Assistenti di Volo", "rate": "€ 520.00 / ora"}
                ]
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
