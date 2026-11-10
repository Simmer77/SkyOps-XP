import httpx
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger("SkyOps.SimBrief")

class SimBriefService:
    BASE_URL = "https://www.simbrief.com/api/xml.fetcher.php"
    
    @classmethod
    async def fetch_latest_ofp(cls, username: Optional[str] = None, pilot_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches latest OFP from SimBrief using username or numeric Pilot ID (userid).
        Automatically detects if a numeric ID was passed inside the username parameter.
        """
        params = {"json": "1"}
        
        raw_pilot_id = pilot_id.strip() if pilot_id else ""
        raw_username = username.strip() if username else ""
        
        # Auto-detect if user entered numeric Pilot ID into the username field
        if raw_pilot_id:
            if raw_pilot_id.isdigit():
                params["userid"] = raw_pilot_id
            else:
                params["username"] = raw_pilot_id
        elif raw_username:
            if raw_username.isdigit():
                params["userid"] = raw_username
            else:
                params["username"] = raw_username
        else:
            raise ValueError("Devi fornire uno username o un Pilot ID di SimBrief")
            
        headers = {
            "User-Agent": "SkyOps-XP/1.0 (X-Plane 12 Flight Operations Platform)"
        }

        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            try:
                logger.info(f"Fetching SimBrief OFP with params: {params}")
                resp = await client.get(cls.BASE_URL, params=params)
                if resp.status_code != 200:
                    logger.error(f"SimBrief HTTP error: {resp.status_code} - {resp.text[:200]}")
                    return None
                
                data = resp.json()
                fetch_info = data.get("fetch", {})
                status = fetch_info.get("status", "")
                if status != "Success" and "Error" in status:
                    logger.error(f"SimBrief API error: {status}")
                    return None
                if "general" not in data:
                    logger.error(f"SimBrief API missing 'general' node. Status: {status}")
                    return None
                
                return cls._normalize_ofp(data)
            except Exception as e:
                logger.error(f"Failed to fetch SimBrief OFP: {e}")
                return None

    @staticmethod
    def _normalize_ofp(data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts clean, structured fields from SimBrief JSON structure"""
        params = data.get("params", {})
        general = data.get("general", {})
        origin = data.get("origin", {})
        destination = data.get("destination", {})
        alternate = data.get("alternate", {})
        weights = data.get("weights", {})
        fuel = data.get("fuel", {})
        times = data.get("times", {})
        aircraft = data.get("aircraft", {})
        
        # Safe string conversion (SimBrief turns empty XML tags into {})
        def to_s(v, default=""):
            if v is None or isinstance(v, (dict, list)):
                return default
            return str(v).strip()

        # Safe float conversion
        def to_f(v, default=0.0):
            if isinstance(v, (dict, list)):
                return default
            try:
                return float(v)
            except (ValueError, TypeError):
                return default
                
        def to_i(v, default=0):
            if isinstance(v, (dict, list)):
                return default
            try:
                return int(v)
            except (ValueError, TypeError):
                return default

        # Convert lbs to kg if SimBrief OFP was generated in imperial lbs
        units = to_s(params.get("units", "kgs")).lower()
        weight_factor = 0.45359237 if units == "lbs" else 1.0

        # Handle alternate when SimBrief returns a list of alternates vs single dict
        alt_icao = ""
        if isinstance(alternate, dict):
            alt_icao = to_s(alternate.get("icao_code", ""))
        elif isinstance(alternate, list) and len(alternate) > 0 and isinstance(alternate[0], dict):
            alt_icao = to_s(alternate[0].get("icao_code", ""))

        # Format time_generated nicely
        created_at = ""
        time_gen = to_i(params.get("time_generated", 0))
        if time_gen > 0:
            try:
                dt = datetime.fromtimestamp(time_gen, tz=timezone.utc)
                created_at = dt.strftime("%d/%m/%Y %H:%M UTC")
            except Exception:
                created_at = str(time_gen)
        else:
            created_at = to_s(general.get("release", ""))

        airline = to_s(general.get("icao_airline", ""))
        flt_num = to_s(general.get("flight_number", "101"))
        flight_number = f"{airline}{flt_num}".strip() or "SO101"

        return {
            "flight_number": flight_number,
            "aircraft_icao": to_s(aircraft.get("icaocode", "SF50")),
            "aircraft_name": to_s(aircraft.get("name", "Unknown Aircraft")),
            "origin_icao": to_s(origin.get("icao_code", "")),
            "origin_name": to_s(origin.get("name", "")),
            "destination_icao": to_s(destination.get("icao_code", "")),
            "destination_name": to_s(destination.get("name", "")),
            "alternate_icao": alt_icao,
            
            # Distance & Times
            "distance_nm": to_f(general.get("air_distance", 0.0)),
            "est_time_enroute_min": round(to_f(times.get("est_time_enroute", 0)) / 60.0, 1),
            "route": to_s(general.get("route", "")),
            
            # Payload & Passengers (always normalized to kg)
            "pax_count": to_i(weights.get("pax_count", 0)),
            "cargo_kg": round(to_f(weights.get("cargo", 0.0)) * weight_factor, 1),
            "payload_kg": round(to_f(weights.get("payload", 0.0)) * weight_factor, 1),
            "est_zfw_kg": round(to_f(weights.get("est_zfw", 0.0)) * weight_factor, 1),
            
            # Fuel (always normalized to kg)
            "block_fuel_kg": round(to_f(fuel.get("plan_ramp", 0.0)) * weight_factor, 1),
            "trip_fuel_kg": round(to_f(fuel.get("enroute_burn", 0.0)) * weight_factor, 1),
            "reserve_fuel_kg": round(to_f(fuel.get("reserve", 0.0)) * weight_factor, 1),
            
            # Timestamp & User ID
            "created_at": created_at,
            "user_id": to_s(params.get("user_id", "")),
            "units_original": units
        }
