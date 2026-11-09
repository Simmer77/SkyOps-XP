import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.schema import Company, Aircraft, FlightLog, MaintenanceEvent, FinancialTransaction

logger = logging.getLogger("SkyOps.Economy")

# Parametri operativi e categorie velivolo basati su standard reali EASA / FAA
CATEGORY_SPECS = {
    "GA": {
        "label": "General Aviation (Monomotori, VLJ, Vision Jet)",
        "avg_mtow_tonnes": 2.7,
        "base_landing_fee_eur": 22.0,
        "fee_per_tonne_eur": 7.50,
        "hangar_weekly_eur": 120.0,
        "insurance_weekly_eur": 160.0,
        "default_lease_rate_eur_h": 320.0,
    },
    "BIZJET": {
        "label": "Business Jet (Phenom 300, Eclipse 550, Citation)",
        "avg_mtow_tonnes": 8.5,
        "base_landing_fee_eur": 65.0,
        "fee_per_tonne_eur": 9.20,
        "hangar_weekly_eur": 350.0,
        "insurance_weekly_eur": 520.0,
        "default_lease_rate_eur_h": 850.0,
    },
    "AIRLINER": {
        "label": "Airliner di Linea (Boeing 737, Airbus A320)",
        "avg_mtow_tonnes": 75.0,
        "base_landing_fee_eur": 280.0,
        "fee_per_tonne_eur": 11.20,
        "hangar_weekly_eur": 1400.0,
        "insurance_weekly_eur": 1950.0,
        "default_lease_rate_eur_h": 1650.0,
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
        lease_rate_hourly: float = 0.0
    ) -> Dict[str, float]:
        """
        Calcola il bilancio finanziario completo del volo in Euro (€).
        """
        specs = CATEGORY_SPECS.get(category, CATEGORY_SPECS["GA"])
        
        # 1. Costo Carburante: kg consumati * prezzo al kg Jet-A1
        fuel_cost = round(fuel_burned_kg * settings.DEFAULT_FUEL_PRICE_EUR_PER_KG, 2)
        
        # 2. Tassa d'atterraggio (Landing Fee): base + quota tonnellata MTOW
        landing_fee = round(specs["base_landing_fee_eur"] + (specs["avg_mtow_tonnes"] * specs["fee_per_tonne_eur"]), 2)
        
        # 3. Costo Noleggio se aereo noleggiato (Block hours * tariffa)
        lease_cost = round(flight_hours * lease_rate_hourly, 2) if is_leased else 0.0
        
        # 4. Spese totali e utile netto
        total_expenses = round(fuel_cost + landing_fee + lease_cost, 2)
        net_profit = round(job_reward - total_expenses, 2)
        
        return {
            "gross_revenue": round(job_reward, 2),
            "fuel_cost": fuel_cost,
            "landing_fee": landing_fee,
            "lease_cost": lease_cost,
            "total_expenses": total_expenses,
            "net_profit": net_profit
        }

    @staticmethod
    def calculate_fixed_period_costs(category: str, days: int = 7) -> Dict[str, float]:
        """Calcola i costi fissi (hangar + assicurazione) per il periodo virtuale trascorso"""
        specs = CATEGORY_SPECS.get(category, CATEGORY_SPECS["GA"])
        factor = days / 7.0
        hangar = round(specs["hangar_weekly_eur"] * factor, 2)
        insurance = round(specs["insurance_weekly_eur"] * factor, 2)
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
        company: Optional[Company] = None
    ) -> FinancialTransaction:
        """
        Registra una transazione nel libro mastro (Ledger) e aggiorna la cassa aziendale se richiesto.
        """
        if not company:
            comp_res = await session.execute(select(Company).limit(1))
            company = comp_res.scalars().first()
            if not company:
                company = Company(cash_balance=175000.0, operating_day=1)
                session.add(company)
                await session.flush()

        company.cash_balance = round(company.cash_balance + amount_eur, 2)
        
        tx = FinancialTransaction(
            timestamp=datetime.now(timezone.utc),
            operating_day=company.operating_day or 1,
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
    async def get_projected_fixed_costs(session: AsyncSession, days: int = 7) -> Dict[str, Any]:
        """
        Calcola i costi fissi previsti per la flotta di proprietà per il prossimo periodo.
        """
        ac_res = await session.execute(select(Aircraft).where(Aircraft.ownership == "OWNED"))
        owned_aircraft = ac_res.scalars().all()
        
        factor = days / 7.0
        details = []
        total_hangar = 0.0
        total_insurance = 0.0
        
        for ac in owned_aircraft:
            specs = CATEGORY_SPECS.get(ac.category, CATEGORY_SPECS["GA"])
            hangar = round(specs["hangar_weekly_eur"] * factor, 2)
            insurance = round(specs["insurance_weekly_eur"] * factor, 2)
            subtotal = round(hangar + insurance, 2)
            
            total_hangar += hangar
            total_insurance += insurance
            details.append({
                "aircraft_id": ac.id,
                "tail_number": ac.tail_number,
                "name": ac.name,
                "category": ac.category,
                "hangar_eur": hangar,
                "insurance_eur": insurance,
                "subtotal_eur": subtotal
            })
            
        return {
            "period_days": days,
            "owned_aircraft_count": len(owned_aircraft),
            "total_hangar_eur": round(total_hangar, 2),
            "total_insurance_eur": round(total_insurance, 2),
            "total_fixed_eur": round(total_hangar + total_insurance, 2),
            "aircraft_breakdown": details
        }

    @staticmethod
    async def advance_operating_cycle(session: AsyncSession, days: int = 7) -> Dict[str, Any]:
        """
        Avanza il giorno operativo e il calendario virtuale dell'azienda, addebitando
        i costi fissi (hangar e assicurazione) per tutti gli aerei di proprietà.
        """
        comp_res = await session.execute(select(Company).limit(1))
        company = comp_res.scalars().first()
        if not company:
            company = Company(cash_balance=175000.0, operating_day=1)
            session.add(company)
            await session.flush()
            
        old_day = company.operating_day or 1
        old_date = company.virtual_date or datetime.now(timezone.utc)
        
        # 1. Fetch owned aircraft
        ac_res = await session.execute(select(Aircraft).where(Aircraft.ownership == "OWNED"))
        owned_aircraft = ac_res.scalars().all()
        
        factor = days / 7.0
        total_deductions = 0.0
        deductions_list = []
        
        for ac in owned_aircraft:
            specs = CATEGORY_SPECS.get(ac.category, CATEGORY_SPECS["GA"])
            hangar_cost = round(specs["hangar_weekly_eur"] * factor, 2)
            insurance_cost = round(specs["insurance_weekly_eur"] * factor, 2)
            
            # Addebito Hangar
            if hangar_cost > 0:
                await EconomyService.record_transaction(
                    session=session,
                    category="FIXED_HANGAR",
                    title=f"Rimessaggio Hangar {ac.tail_number} ({days} gg)",
                    amount_eur=-hangar_cost,
                    description=f"Canone hangaraggio per {ac.name} presso {ac.current_icao} ({days} giorni simulati)",
                    aircraft_tail=ac.tail_number,
                    company=company
                )
                total_deductions += hangar_cost
                
            # Addebito Assicurazione
            if insurance_cost > 0:
                await EconomyService.record_transaction(
                    session=session,
                    category="FIXED_INSURANCE",
                    title=f"Polizza Corpi & RC {ac.tail_number} ({days} gg)",
                    amount_eur=-insurance_cost,
                    description=f"Copertura assicurativa Kasko/Corpi & RC Terzi {ac.name} ({days} giorni simulati)",
                    aircraft_tail=ac.tail_number,
                    company=company
                )
                total_deductions += insurance_cost
                
            deductions_list.append({
                "tail_number": ac.tail_number,
                "name": ac.name,
                "hangar_cost": hangar_cost,
                "insurance_cost": insurance_cost,
                "total": round(hangar_cost + insurance_cost, 2)
            })

        # 2. Advance operational timeline
        new_day = old_day + days
        new_date = old_date + timedelta(days=days)
        company.operating_day = new_day
        company.virtual_date = new_date
        
        await session.commit()
        await session.refresh(company)
        
        return {
            "advanced_days": days,
            "old_day": old_day,
            "new_day": new_day,
            "old_virtual_date": old_date.isoformat(),
            "new_virtual_date": new_date.isoformat(),
            "total_deductions_eur": round(total_deductions, 2),
            "new_cash_balance_eur": company.cash_balance,
            "deductions_by_aircraft": deductions_list
        }

    @staticmethod
    async def get_financial_statement(session: AsyncSession) -> Dict[str, Any]:
        """
        Genera il Rendiconto Finanziario Completo:
        - Stato Patrimoniale (Attivo Circolante, Flotta, Patrimonio Netto)
        - Conto Economico (Ricavi Lordi, Costi Operativi DOC, Manutenzione, Costi Fissi, Risultato d'Esercizio)
        - Previsioni Prossimo Ciclo Operativo
        """
        # 1. Company profile
        comp_res = await session.execute(select(Company).limit(1))
        company = comp_res.scalars().first()
        if not company:
            company = Company(cash_balance=175000.0, operating_day=1)
            session.add(company)
            await session.commit()
            
        # 2. Owned aircraft valuation
        ac_res = await session.execute(select(Aircraft).where(Aircraft.ownership == "OWNED"))
        owned_aircraft = ac_res.scalars().all()
        fleet_book_value = sum(ac.purchase_price_eur or 0.0 for ac in owned_aircraft)
        
        # 3. Aggregates from FinancialTransactions (or flight logs & maintenance if transactions are new)
        tx_res = await session.execute(select(FinancialTransaction))
        transactions = tx_res.scalars().all()
        
        revenue_flight = sum(t.amount_eur for t in transactions if t.category in ["REVENUE", "REVENUE_FLIGHT"] and t.amount_eur > 0)
        expense_fuel = abs(sum(t.amount_eur for t in transactions if t.category in ["FUEL", "EXPENSE_FUEL"]))
        expense_landing = abs(sum(t.amount_eur for t in transactions if t.category in ["LANDING_FEE", "EXPENSE_LANDING"]))
        expense_lease = abs(sum(t.amount_eur for t in transactions if t.category in ["LEASE", "EXPENSE_LEASE"]))
        expense_maint = abs(sum(t.amount_eur for t in transactions if t.category in ["MAINTENANCE", "EXPENSE_MAINTENANCE"]))
        expense_hangar = abs(sum(t.amount_eur for t in transactions if t.category in ["FIXED_HANGAR"]))
        expense_insurance = abs(sum(t.amount_eur for t in transactions if t.category in ["FIXED_INSURANCE"]))
        expense_purchases = abs(sum(t.amount_eur for t in transactions if t.category in ["AIRCRAFT_PURCHASE", "CAPITAL_PURCHASE"]))
        
        # If no transactions exist yet, calculate from existing flight logs & maintenance events to preserve history
        if not transactions:
            fl_res = await session.execute(select(FlightLog))
            flights = fl_res.scalars().all()
            revenue_flight = sum(f.revenue_usd or 0.0 for f in flights)
            expense_fuel = sum(f.fuel_cost_usd or 0.0 for f in flights)
            expense_landing = sum(f.landing_fee_usd or 0.0 for f in flights)
            expense_lease = sum(f.lease_cost_usd or 0.0 for f in flights)
            
            mv_res = await session.execute(select(MaintenanceEvent))
            events = mv_res.scalars().all()
            expense_maint = sum(m.cost_usd or 0.0 for m in events)
            
        direct_operating_costs = round(expense_fuel + expense_landing + expense_lease, 2)
        fixed_overheads = round(expense_hangar + expense_insurance, 2)
        total_expenses = round(direct_operating_costs + expense_maint + fixed_overheads, 2)
        net_profit = round(revenue_flight - total_expenses, 2)
        margin_pct = round((net_profit / revenue_flight * 100.0), 1) if revenue_flight > 0 else 0.0
        
        # Next cycle projection
        projections = await EconomyService.get_projected_fixed_costs(session, days=7)
        
        return {
            "operating_day": company.operating_day or 1,
            "virtual_date": (company.virtual_date or datetime.now(timezone.utc)).isoformat(),
            
            # Stato Patrimoniale (Balance Sheet)
            "balance_sheet": {
                "cash_balance_eur": company.cash_balance,
                "fleet_book_value_eur": round(fleet_book_value, 2),
                "total_net_worth_eur": round(company.cash_balance + fleet_book_value, 2),
                "owned_aircraft_count": len(owned_aircraft)
            },
            
            # Conto Economico (P&L Statement)
            "income_statement": {
                "gross_revenue_eur": round(revenue_flight, 2),
                "direct_operating_costs": {
                    "total_eur": direct_operating_costs,
                    "fuel_eur": round(expense_fuel, 2),
                    "landing_fees_eur": round(expense_landing, 2),
                    "aircraft_leases_eur": round(expense_lease, 2)
                },
                "maintenance_costs": {
                    "total_eur": round(expense_maint, 2)
                },
                "fixed_overheads": {
                    "total_eur": fixed_overheads,
                    "hangar_eur": round(expense_hangar, 2),
                    "insurance_eur": round(expense_insurance, 2)
                },
                "total_expenses_eur": total_expenses,
                "net_profit_eur": net_profit,
                "profit_margin_pct": margin_pct
            },
            
            # Previsioni Fisse Settimanali
            "upcoming_fixed_costs_7d": projections
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
                "formula": "Costo Carburante = Kg Carburante Bruciato × 1.75 €/kg",
                "notes": "Basato sulla densità standard ICAO di 0.80 kg/L e media prezzi IATA aeroporti europei."
            },
            "landing_fee_rules": {
                "formula": "Tassa Atterraggio = Tassa Base Aeroporto + (MTOW velivolo in Tonnellate × Quota/Tonnellata)",
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
