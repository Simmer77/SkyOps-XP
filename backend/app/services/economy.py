import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger("SkyOps.Economy")

# Category weights and standard fees
CATEGORY_SPECS = {
    "GA": {
        "avg_mtow_tonnes": 2.5,
        "hangar_weekly_usd": 150.0,
        "insurance_weekly_usd": 200.0,
        "base_landing_fee": 25.0
    },
    "BIZJET": {
        "avg_mtow_tonnes": 8.5,
        "hangar_weekly_usd": 400.0,
        "insurance_weekly_usd": 650.0,
        "base_landing_fee": 75.0
    },
    "AIRLINER": {
        "avg_mtow_tonnes": 75.0,
        "hangar_weekly_usd": 1800.0,
        "insurance_weekly_usd": 2500.0,
        "base_landing_fee": 320.0
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
        Calculates complete financial statement for a flight.
        """
        specs = CATEGORY_SPECS.get(category, CATEGORY_SPECS["GA"])
        
        # 1. Fuel cost
        fuel_cost = round(fuel_burned_kg * settings.DEFAULT_FUEL_PRICE_USD_PER_KG, 2)
        
        # 2. Landing fee
        landing_fee = round(specs["base_landing_fee"] + (specs["avg_mtow_tonnes"] * settings.AVG_LANDING_FEE_PER_TONNE_USD), 2)
        
        # 3. Lease cost if rented
        lease_cost = round(flight_hours * lease_rate_hourly, 2) if is_leased else 0.0
        
        # 4. Total expenses & net profit
        total_expenses = fuel_cost + landing_fee + lease_cost
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
        """Calculates hangar and insurance costs for elapsed virtual days"""
        specs = CATEGORY_SPECS.get(category, CATEGORY_SPECS["GA"])
        factor = days / 7.0
        hangar = round(specs["hangar_weekly_usd"] * factor, 2)
        insurance = round(specs["insurance_weekly_usd"] * factor, 2)
        return {
            "hangar_usd": hangar,
            "insurance_usd": insurance,
            "total_fixed_usd": round(hangar + insurance, 2)
        }
