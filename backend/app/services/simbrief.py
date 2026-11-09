import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("SkyOps.SimBrief")

class SimBriefService:
    BASE_URL = "https://www.simbrief.com/api/xml.fetcher.php"
    
    @classmethod
    async def fetch_latest_ofp(cls, username: Optional[str] = None, pilot_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches latest OFP from SimBrief using username or pilot_id.
        Returns parsed, normalized flight plan dictionary.
        """
        params = {"json": "1"}
        if pilot_id and pilot_id.strip():
            params["userid"] = pilot_id.strip()
        elif username and username.strip():
            params["username"] = username.strip()
        else:
            raise ValueError("Devi fornire uno username o un Pilot ID di SimBrief")
            
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(cls.BASE_URL, params=params)
                if resp.status_code != 200:
                    logger.error(f"SimBrief HTTP error: {resp.status_code}")
                    return None
                
                data = resp.json()
                if "fetch" in data and data["fetch"].get("status") == "Error":
                    logger.error(f"SimBrief API error: {data['fetch'].get('status')}")
                    return None
                
                return cls._normalize_ofp(data)
            except Exception as e:
                logger.error(f"Failed to fetch SimBrief OFP: {e}")
                return None

    @staticmethod
    def _normalize_ofp(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts clean, structured fields from SimBrief JSON structure"""
        general = data.get("general", {})
        origin = data.get("origin", {})
        destination = data.get("destination", {})
        alternate = data.get("alternate", {})
        weights = data.get("weights", {})
        fuel = data.get("fuel", {})
        times = data.get("times", {})
        aircraft = data.get("aircraft", {})
        
        # Safe float conversion
        def to_f(v, default=0.0):
            try:
                return float(v)
            except (ValueError, TypeError):
                return default
                
        def to_i(v, default=0):
            try:
                return int(v)
            except (ValueError, TypeError):
                return default

        return {
            "flight_number": f"{general.get('icao_airline', '')}{general.get('flight_number', '101')}".strip(),
            "aircraft_icao": aircraft.get("icaocode", "SF50"),
            "aircraft_name": aircraft.get("name", "Unknown Aircraft"),
            "origin_icao": origin.get("icao_code", ""),
            "origin_name": origin.get("name", ""),
            "destination_icao": destination.get("icao_code", ""),
            "destination_name": destination.get("name", ""),
            "alternate_icao": alternate.get("icao_code", "") if isinstance(alternate, dict) else "",
            
            # Distance & Times
            "distance_nm": to_f(general.get("air_distance", 0.0)),
            "est_time_enroute_min": round(to_f(times.get("est_time_enroute", 0)) / 60.0, 1),
            "route": general.get("route", ""),
            
            # Payload & Passengers
            "pax_count": to_i(weights.get("pax_count", 0)),
            "cargo_kg": to_f(weights.get("cargo", 0.0)),
            "payload_kg": to_f(weights.get("payload", 0.0)),
            "est_zfw_kg": to_f(weights.get("est_zfw", 0.0)),
            
            # Fuel
            "block_fuel_kg": to_f(fuel.get("plan_ramp", 0.0)),
            "trip_fuel_kg": to_f(fuel.get("enroute_burn", 0.0)),
            "reserve_fuel_kg": to_f(fuel.get("reserve", 0.0)),
            
            # Raw timestamp
            "created_at": str(general.get("release", ""))
        }
