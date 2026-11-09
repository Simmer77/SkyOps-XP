import logging
from typing import Dict, Any, List
from app.core.config import settings

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
