import random
import logging
from typing import Dict, Any, Tuple, Optional
from app.services.xp_connector import xp_connector

logger = logging.getLogger("SkyOps.Maintenance")

# Realistic X-Plane 12 Datarefs for component failures
FAILURE_MAP = {
    "ENGINE": [
        ("sim/operation/failures/rel_engfai0", "Guasto completo motore 1"),
        ("sim/operation/failures/rel_oilp_0", "Perdita pressione olio motore"),
        ("sim/operation/failures/rel_genera0", "Avaria generatore / alternatore"),
    ],
    "BRAKES": [
        ("sim/operation/failures/rel_lbrak", "Avaria circuito freno sinistro"),
        ("sim/operation/failures/rel_rbrak", "Avaria circuito freno destro"),
    ],
    "TIRES": [
        ("sim/operation/failures/rel_l_tire", "Scoppio pneumatico carrello sinistro"),
        ("sim/operation/failures/rel_r_tire", "Scoppio pneumatico carrello destro"),
        ("sim/operation/failures/rel_nose_tire", "Cedimento pneumatico carrello anteriore"),
    ],
    "AVIONICS": [
        ("sim/operation/failures/rel_pitot", "Ghiaccio / Blocco tubo di Pitot"),
        ("sim/operation/failures/rel_gls", "Avaria ricevitore ILS / Glideslope"),
        ("sim/operation/failures/rel_transponder", "Avaria Transponder Mode-S"),
    ],
    "AIRFRAME": [
        ("sim/operation/failures/rel_flp_asym", "Asimmetria estensione Flaps"),
        ("sim/operation/failures/rel_ice_inlet", "Ingestione ghiaccio e stallo compressore"),
    ]
}

class MaintenanceService:
    @staticmethod
    def calculate_flight_wear(
        flight_hours: float,
        touchdown_fpm: Optional[float],
        touchdown_g: Optional[float],
        max_g: float,
        min_g: float
    ) -> Dict[str, float]:
        """
        Calculates percentage wear deduction for components based on flight metrics.
        Returns dict of deltas (e.g. {"engine": -0.8, "tires": -1.2, ...})
        """
        # Base hourly wear
        engine_wear = flight_hours * 0.45      # ~220 hours to reach 0% if unserviced
        airframe_wear = flight_hours * 0.15
        avionics_wear = flight_hours * 0.10
        
        # Brakes & Tires base wear
        brakes_wear = 0.4 + (flight_hours * 0.1)
        tires_wear = 0.5 + (flight_hours * 0.1)
        
        # Touchdown impact penalty
        if touchdown_fpm is not None:
            fpm = abs(touchdown_fpm)
            if fpm > 600: # Severe hard landing
                tires_wear += 25.0
                airframe_wear += 15.0
                logger.warning(f"Extreme hard landing ({fpm} fpm)! Severe airframe and tire wear applied.")
            elif fpm > 400: # Hard landing
                tires_wear += 8.0
                airframe_wear += 3.0
            elif fpm < 150: # Butter landing
                tires_wear += 0.2
                
        if touchdown_g is not None and touchdown_g > 2.0:
            excess_g = touchdown_g - 2.0
            airframe_wear += excess_g * 12.0
            tires_wear += excess_g * 15.0

        # In-flight over-G penalties
        if max_g > 2.8 or min_g < -0.5:
            airframe_wear += 10.0
            logger.warning(f"Over-G event recorded! (Max: {max_g:.2f}G, Min: {min_g:.2f}G)")

        return {
            "engine": round(engine_wear, 2),
            "airframe": round(airframe_wear, 2),
            "brakes": round(brakes_wear, 2),
            "tires": round(tires_wear, 2),
            "avionics": round(avionics_wear, 2),
        }

    @staticmethod
    def evaluate_in_flight_failures(aircraft: Any) -> Optional[Tuple[str, str]]:
        """
        Evaluates current health of components.
        If a component is heavily worn, there is a probability of triggering a failure in X-Plane.
        Returns (failure_dref, failure_description) if triggered, else None.
        """
        components = [
            ("ENGINE", aircraft.health_engine_pct),
            ("BRAKES", aircraft.health_brakes_pct),
            ("TIRES", aircraft.health_tires_pct),
            ("AVIONICS", aircraft.health_avionics_pct),
            ("AIRFRAME", aircraft.health_airframe_pct)
        ]
        
        for comp_name, health in components:
            # Below 35% health: failure risk grows rapidly
            if health < 35.0:
                risk_pct = (35.0 - health) * 0.02  # e.g. at 15% health -> ~0.4% chance per check tick
                if random.random() < risk_pct:
                    # Pick a failure for this component
                    failures = FAILURE_MAP.get(comp_name, [])
                    if failures:
                        dref, desc = random.choice(failures)
                        xp_connector.inject_failure(dref, mode=6)
                        return (dref, f"AVARIA SISTEMA: {desc} (Stato componente: {health:.1f}%)")
                        
        return None

    @staticmethod
    def get_service_costs() -> Dict[str, Dict[str, Any]]:
        """Returns standard maintenance service catalog"""
        return {
            "OIL_AND_FILTER": {
                "name": "Cambio Olio e Filtri (50h)",
                "cost_usd": 450.0,
                "engine_health_gain": 8.0,
                "notes": "Ispezione e lubrificazione base motore"
            },
            "INSPECTION_100H": {
                "name": "Ispezione Completa 100 Ore",
                "cost_usd": 2400.0,
                "engine_health_gain": 20.0,
                "avionics_health_gain": 15.0,
                "notes": "Tagliando programmato con controllo compressione e candele"
            },
            "TIRES_REPLACE": {
                "name": "Sostituzione Pneumatici Carrello",
                "cost_usd": 1200.0,
                "tires_health_gain": 100.0,
                "notes": "Gomme nuove per carrello principale e anteriore"
            },
            "BRAKES_OVERHAUL": {
                "name": "Revisione Dischi e Pastiglie Freni",
                "cost_usd": 1800.0,
                "brakes_health_gain": 100.0,
                "notes": "Sostituzione pastiglie e spurgo impianto idraulico"
            },
            "ANNUAL_INSPECTION": {
                "name": "Ispezione Annuale Strutturale FAA/EASA",
                "cost_usd": 4800.0,
                "airframe_health_gain": 25.0,
                "avionics_health_gain": 25.0,
                "notes": "Revisione certificata dell'intera cellula e comandi di volo"
            },
            "ENGINE_OVERHAUL": {
                "name": "Revisione Generale Motore (TBO)",
                "cost_usd": 38000.0,
                "engine_health_gain": 100.0,
                "notes": "Rigenerazione a ore zero del motore"
            }
        }
