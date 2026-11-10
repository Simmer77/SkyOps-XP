import os
import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("SkyOps.Dealerships")

# Fast coordinate cache for major global hubs, Italian bases, and all Manufacturer Dealerships
AIRPORT_CACHE: Dict[str, Tuple[str, float, float]] = {
    # Europe Dealership & Delivery Centers
    "EHGG": ("Groningen Eelde (NL) — Cirrus European Delivery Center", 53.1250, 6.5833),
    "LPCS": ("Cascais Tires (PT) — Embraer Executive Europe", 38.7255, -9.3552),
    "LFBO": ("Toulouse Blagnac (FR) — Airbus Final Assembly & Delivery", 43.6291, 1.3638),
    "EDDF": ("Frankfurt am Main (DE) — Boeing Europe Support Hub", 50.0379, 8.5622),
    "LSZH": ("Zürich Kloten (CH) — Textron Aviation (Cessna/Beech) Europe", 47.4647, 8.5492),
    "EDFE": ("Frankfurt Egelsbach (DE) — GA & Executive Center", 49.9608, 8.6414),
    "LFGI": ("Dijon Darois (FR) — Fabbrica Robin Aircraft", 47.4106, 4.9711),
    "EDMA": ("Augsburg (DE) — Piper Germany / European Hub", 48.4252, 10.9317),
    "LEMD": ("Madrid Barajas (ES) — Centro Broker & MRO MD-80 Europe", 40.4719, -3.5626),
    "LFPB": ("Paris Le Bourget (FR) — European Business Aviation Hub", 48.9694, 2.4414),
    "LSZC": ("Buochs (CH) — Pilatus Aircraft Factory", 46.9744, 8.3969),
    "LOAN": ("Wiener Neustadt Ost (AT) — Diamond Aircraft Factory", 47.8433, 16.2601),
    "LFBT": ("Tarbes-Lourdes-Pyrénées (FR) — Daher TBM Factory", 43.1787, 0.0064),
    "LIAU": ("Capua Oreste Salomone (IT) — Fabbrica Tecnam", 41.1167, 14.1833),
    "LFBD": ("Bordeaux Mérignac (FR) — Dassault Falcon Assembly", 44.8283, -0.7156),
    "EGLF": ("Farnborough (UK) — Gulfstream & Executive Europe", 51.2758, -0.7763),
    "ESSL": ("Linköping Saab (SE) — Saab Aircraft Factory", 58.4022, 15.6806),
    "EGKK": ("London Gatwick (UK) — UK Regional & De Havilland Hub", 51.1481, -0.1903),

    # North America Dealership & Factory Centers
    "KDLH": ("Duluth Intl, MN (USA) — Cirrus Aircraft Factory", 46.8421, -92.1936),
    "KMLB": ("Melbourne Orlando, FL (USA) — Embraer Executive Factory", 28.1028, -80.6453),
    "KBFM": ("Mobile Brookley, AL (USA) — Airbus US Manufacturing", 30.6268, -88.0681),
    "KBFI": ("Seattle Boeing Field, WA (USA) — Boeing Delivery Center", 47.5300, -122.3019),
    "KICT": ("Wichita Eisenhower, KS (USA) — Cessna & Beechcraft HQ", 37.6499, -97.4331),
    "KVRB": ("Vero Beach, FL (USA) — Piper Aircraft Factory", 27.6556, -80.4179),
    "KRDM": ("Redmond Roberts Field, OR (USA) — Lancair Factory", 44.2541, -121.1500),
    "KUAO": ("Aurora State, OR (USA) — Van's Aircraft Factory", 45.2473, -122.7700),
    "KLGB": ("Long Beach, CA (USA) — McDonnell Douglas Delivery Hub", 33.8177, -118.1516),
    "KTEB": ("Teterboro, NJ (USA) — North America Broker Hub", 40.8501, -74.0608),
    "CYHU": ("Montréal Saint-Hubert (CA) — Regional GA Center", 45.5175, -73.4169),
    "CYXU": ("London Intl, ON (CA) — Diamond Aircraft North America", 43.0331, -81.1511),
    "CYUL": ("Montréal Trudeau (CA) — Bombardier Final Assembly", 45.4706, -73.7408),
    "CYYZ": ("Toronto Pearson (CA) — De Havilland Canada Hub", 43.6777, -79.6248),
    "KSAV": ("Savannah/Hilton Head, GA (USA) — Gulfstream Aerospace HQ", 32.1276, -81.2021),
    "KBJC": ("Broomfield Rocky Mountain, CO (USA) — Pilatus US", 39.9088, -105.1172),
    "KSEF": ("Sebring Regional, FL (USA) — Tecnam North America", 27.4564, -81.3424),
    "KERV": ("Kerrville Municipal, TX (USA) — Mooney Aircraft Factory", 29.9767, -99.0855),
    "KPMP": ("Pompano Beach, FL (USA) — Daher TBM Service US", 26.2471, -80.1111),
    "KMIA": ("Miami International, FL (USA) — ATR Americas Hub", 25.7959, -80.2870),

    # South America
    "SBSJ": ("São José dos Campos (BR) — Sede Centrale Embraer", -23.2289, -45.8617),
    "SBJD": ("Jundiaí SP (BR) — Cirrus Brasil Hub", -23.1817, -46.9436),
    "SBSP": ("São Paulo Congonhas (BR) — South America Executive Hub", -23.6261, -46.6564),
    "SCEL": ("Santiago Arturo Merino (CL) — South America Airline Hub", -33.3930, -70.7858),

    # Asia / Middle East
    "WSSL": ("Singapore Seletar (SG) — Asia GA & BizJet Hub", 1.4169, 103.8678),
    "WSSS": ("Singapore Changi (SG) — Asia Airline Delivery Hub", 1.3644, 103.9915),
    "ZBTJ": ("Tianjin Binhai (CN) — Airbus Final Assembly Asia", 39.1244, 117.3461),
    "OMDW": ("Dubai Al Maktoum (AE) — Middle East Executive Hub", 24.8964, 55.1614),

    # Oceania
    "YSCN": ("Camden Sydney (AU) — Cirrus & GA Australia Hub", -34.0403, 150.6872),
    "YSSY": ("Sydney Kingsford Smith (AU) — Oceania Airline Hub", -33.9461, 151.1772),

    # Africa
    "FALA": ("Lanseria Johannesburg (ZA) — Africa GA & Executive Hub", -25.9385, 27.9261),
    "FAOR": ("Johannesburg OR Tambo (ZA) — Africa Airline Hub", -26.1392, 28.2460),

    # Common Italian & European User Bases
    "LIRN": ("Napoli Capodichino", 40.8860, 14.2908),
    "LIRF": ("Roma Fiumicino", 41.8003, 12.2389),
    "LIRA": ("Roma Ciampino", 41.7994, 12.5949),
    "LIMC": ("Milano Malpensa", 45.6306, 8.7281),
    "LIML": ("Milano Linate", 45.4451, 9.2767),
    "LIME": ("Bergamo Orio al Serio", 45.6739, 9.7042),
    "LIMF": ("Torino Caselle", 45.2008, 7.6496),
    "LIPZ": ("Venezia Tessera", 45.5053, 12.3519),
    "LIPX": ("Verona Villafranca", 45.3957, 10.8885),
    "LIPE": ("Bologna Marconi", 44.5354, 11.2887),
    "LIRQ": ("Firenze Peretola", 43.8100, 11.2051),
    "LIRP": ("Pisa Galileo Galilei", 43.6839, 10.3927),
    "LICC": ("Catania Fontanarossa", 37.4668, 15.0664),
    "LICJ": ("Palermo Punta Raisi", 38.1760, 13.0910),
    "LIEO": ("Olbia Costa Smeralda", 40.8987, 9.5176),
    "LIEE": ("Cagliari Elmas", 39.2515, 9.0543),
    "LIBD": ("Bari Palese", 41.1389, 16.7606),
    "LFMN": ("Nice Côte d'Azur", 43.6653, 7.2150),
    "LSGG": ("Geneva Cointrin", 46.2381, 6.1089),
    "LOWI": ("Innsbruck", 47.2602, 11.3440),
    "EGLL": ("London Heathrow", 51.4700, -0.4543),
    "EHAM": ("Amsterdam Schiphol", 52.3105, 4.7683),
    "MD47": ("Windsock Field MD", 39.3800, -77.2100),
}

# Dealership mapping: (Manufacturer keyword, Continent) -> ICAO
MANUFACTURER_DEALERSHIPS: Dict[str, Dict[str, str]] = {
    "cirrus": {"EU": "EHGG", "NA": "KDLH", "SA": "SBJD", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "embraer": {"EU": "LPCS", "NA": "KMLB", "SA": "SBSJ", "AS": "WSSL", "OC": "YSSY", "AF": "FALA"},
    "airbus": {"EU": "LFBO", "NA": "KBFM", "SA": "SCEL", "AS": "ZBTJ", "OC": "YSSY", "AF": "FAOR"},
    "boeing": {"EU": "EDDF", "NA": "KBFI", "SA": "SCEL", "AS": "WSSS", "OC": "YSSY", "AF": "FAOR"},
    "cessna": {"EU": "LSZH", "NA": "KICT", "SA": "SBSP", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "beechcraft": {"EU": "LSZH", "NA": "KICT", "SA": "SBSP", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "robin": {"EU": "LFGI", "NA": "CYHU", "SA": "SBJD", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "piper": {"EU": "EDMA", "NA": "KVRB", "SA": "SBJD", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "lancair": {"EU": "EDFE", "NA": "KRDM", "SA": "SBSP", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "van": {"EU": "LFPB", "NA": "KUAO", "SA": "SBJD", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "mcdonnell": {"EU": "LEMD", "NA": "KLGB", "SA": "SCEL", "AS": "WSSS", "OC": "YSSY", "AF": "FAOR"},
    "pilatus": {"EU": "LSZC", "NA": "KBJC", "SA": "SBSP", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "diamond": {"EU": "LOAN", "NA": "CYXU", "SA": "SBJD", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "daher": {"EU": "LFBT", "NA": "KPMP", "SA": "SBSP", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "socata": {"EU": "LFBT", "NA": "KPMP", "SA": "SBSP", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "tecnam": {"EU": "LIAU", "NA": "KSEF", "SA": "SBJD", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "bombardier": {"EU": "LFPB", "NA": "CYUL", "SA": "SBSP", "AS": "OMDW", "OC": "YSSY", "AF": "FALA"},
    "canadair": {"EU": "LFPB", "NA": "CYUL", "SA": "SBSP", "AS": "OMDW", "OC": "YSSY", "AF": "FALA"},
    "dassault": {"EU": "LFBD", "NA": "KTEB", "SA": "SBSP", "AS": "OMDW", "OC": "YSSY", "AF": "FALA"},
    "gulfstream": {"EU": "EGLF", "NA": "KSAV", "SA": "SBSP", "AS": "OMDW", "OC": "YSSY", "AF": "FALA"},
    "atr": {"EU": "LFBO", "NA": "KMIA", "SA": "SCEL", "AS": "WSSS", "OC": "YSSY", "AF": "FAOR"},
    "havilland": {"EU": "EGKK", "NA": "CYYZ", "SA": "SCEL", "AS": "WSSS", "OC": "YSSY", "AF": "FAOR"},
    "mooney": {"EU": "EDFE", "NA": "KERV", "SA": "SBJD", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "saab": {"EU": "ESSL", "NA": "CYUL", "SA": "SCEL", "AS": "WSSS", "OC": "YSSY", "AF": "FAOR"},
    "fokker": {"EU": "EHAM", "NA": "KTEB", "SA": "SCEL", "AS": "WSSS", "OC": "YSSY", "AF": "FAOR"},
    "quest": {"EU": "LFBT", "NA": "KICT", "SA": "SBJD", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
    "kodiak": {"EU": "LFBT", "NA": "KICT", "SA": "SBJD", "AS": "WSSL", "OC": "YSCN", "AF": "FALA"},
}

CONTINENT_NAMES = {
    "EU": "Europa",
    "NA": "Nord America",
    "SA": "Sud America",
    "AS": "Asia & Medio Oriente",
    "OC": "Oceania",
    "AF": "Africa"
}


NEGATIVE_AIRPORT_CACHE = set()

class DealershipService:
    @staticmethod
    def get_continent_from_icao(icao: str) -> str:
        if not icao:
            return "EU"
        c = icao.strip().upper()[0]
        if c in ("L", "E", "B", "U"):
            return "EU"
        if c in ("K", "C", "M", "P", "T"):
            return "NA"
        if c == "S":
            return "SA"
        if c in ("R", "Z", "V", "W", "O"):
            return "AS"
        if c in ("Y", "N", "A"):
            return "OC"
        if c in ("H", "F", "D", "G"):
            return "AF"
        return "EU"

    @staticmethod
    def resolve_airport_coords(icao: str, xp12_path: Optional[str] = None) -> Optional[Tuple[str, float, float]]:
        """
        Strictly resolves airport name and exact coordinates from cache or X-Plane 12 apt.dat.
        Returns None if the ICAO cannot be verified.
        """
        if not icao:
            return None
        code = icao.strip().upper()
        if code in AIRPORT_CACHE:
            return AIRPORT_CACHE[code]
        if code in NEGATIVE_AIRPORT_CACHE:
            return None

        target_xp = xp12_path
        if not target_xp:
            from app.services.xp_scanner import XP12ScannerService
            target_xp = XP12ScannerService.detect_xp12_path()

        # Scan X-Plane 12's Global Airports/Earth nav data/apt.dat if available
        if target_xp:
            apt_dat = Path(target_xp) / "Global Scenery" / "Global Airports" / "Earth nav data" / "apt.dat"
            if apt_dat.exists() and apt_dat.is_file():
                try:
                    found_header = False
                    ap_name = code
                    lat = None
                    lon = None
                    with open(apt_dat, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if not found_header:
                                if line.startswith("1 ") and f" {code} " in line:
                                    parts = line.strip().split(None, 5)
                                    if len(parts) >= 5 and parts[4] == code:
                                        found_header = True
                                        ap_name = parts[5] if len(parts) > 5 else code
                            else:
                                if line.startswith("1 "):
                                    break
                                if line.startswith("1302 datum_lat "):
                                    lat = float(line.split()[2])
                                elif line.startswith("1302 datum_lon "):
                                    lon = float(line.split()[2])
                                if lat is not None and lon is not None:
                                    AIRPORT_CACHE[code] = (ap_name, lat, lon)
                                    return AIRPORT_CACHE[code]
                except Exception as e:
                    logger.warning(f"Error reading apt.dat for {code}: {e}")

        NEGATIVE_AIRPORT_CACHE.add(code)
        return None

    @staticmethod
    def get_airport_coords(icao: str, xp12_path: Optional[str] = None) -> Tuple[str, float, float]:
        """Looks up airport name and coordinates from memory cache or X-Plane 12 apt.dat with continent fallback"""
        resolved = DealershipService.resolve_airport_coords(icao, xp12_path)
        if resolved:
            return resolved

        code = (icao or "LIRN").strip().upper()
        cont = DealershipService.get_continent_from_icao(code)
        fallbacks = {
            "EU": (code, 46.5, 10.5),
            "NA": (code, 39.5, -95.0),
            "SA": (code, -23.5, -46.5),
            "AS": (code, 25.0, 105.0),
            "OC": (code, -33.8, 151.0),
            "AF": (code, -26.0, 28.0),
        }
        return fallbacks.get(cont, (code, 41.8, 12.2))

    @staticmethod
    def distance_between_icaos_nm(icao1: str, icao2: str, xp12_path: Optional[str] = None) -> Optional[float]:
        c1 = DealershipService.resolve_airport_coords(icao1, xp12_path)
        c2 = DealershipService.resolve_airport_coords(icao2, xp12_path)
        if not c1 or not c2:
            return None
        return DealershipService._haversine_nm(c1[1], c1[2], c2[1], c2[2])

    @staticmethod
    def distance_from_live_pos_nm(lat: float, lon: float, target_icao: str, xp12_path: Optional[str] = None) -> Optional[float]:
        if lat == 0.0 and lon == 0.0:
            return None
        coords = DealershipService.resolve_airport_coords(target_icao, xp12_path)
        if not coords:
            return None
        return DealershipService._haversine_nm(lat, lon, coords[1], coords[2])

    @staticmethod
    def _haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r_nm = 3440.065
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(r_nm * c, 1)

    @classmethod
    def get_dealership_for_aircraft(
        cls,
        manufacturer: str,
        category: str,
        home_base_icao: str,
        xp12_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determines the real-world regional dealership airport in the user's continent
        and computes distance + realistic one-time ferry delivery cost to home_base_icao.
        """
        base_code = (home_base_icao or "LIRN").strip().upper()
        continent = cls.get_continent_from_icao(base_code)
        cont_label = CONTINENT_NAMES.get(continent, "Europa")
        
        manuf_lower = (manufacturer or "").lower()
        dealer_icao = None
        for key, mapping in MANUFACTURER_DEALERSHIPS.items():
            if key in manuf_lower:
                dealer_icao = mapping.get(continent)
                break
                
        # Generic category hub fallback by continent
        if not dealer_icao:
            generic_hubs = {
                "EU": {"GA": "EDFE", "BIZJET": "LFPB", "AIRLINER": "EDDF"},
                "NA": {"GA": "KICT", "BIZJET": "KTEB", "AIRLINER": "KBFI"},
                "SA": {"GA": "SBJD", "BIZJET": "SBSP", "AIRLINER": "SCEL"},
                "AS": {"GA": "WSSL", "BIZJET": "OMDW", "AIRLINER": "WSSS"},
                "OC": {"GA": "YSCN", "BIZJET": "YSSY", "AIRLINER": "YSSY"},
                "AF": {"GA": "FALA", "BIZJET": "FALA", "AIRLINER": "FAOR"},
            }
            dealer_icao = generic_hubs.get(continent, generic_hubs["EU"]).get(category, "LFPB")

        dealer_name, d_lat, d_lon = cls.get_airport_coords(dealer_icao, xp12_path)
        base_name, b_lat, b_lon = cls.get_airport_coords(base_code, xp12_path)
        
        dist_nm = cls._haversine_nm(d_lat, d_lon, b_lat, b_lon)
        
        # Calculate realistic one-time Ferry Delivery Cost
        if dist_nm < 15.0 or dealer_icao == base_code:
            ferry_fee = 0.0
        else:
            rates = {
                "GA": (250.0, 1.40),       # € 250 pilot briefing + € 1.40 / NM
                "BIZJET": (550.0, 3.20),   # € 550 ferry crew + € 3.20 / NM
                "AIRLINER": (950.0, 6.50)  # € 950 airline ferry crew + € 6.50 / NM
            }
            base_fee, per_nm = rates.get(category, rates["GA"])
            ferry_fee = round(base_fee + (dist_nm * per_nm), 2)

        return {
            "continent": continent,
            "continent_label": cont_label,
            "home_base_icao": base_code,
            "home_base_name": base_name,
            "dealership_icao": dealer_icao,
            "dealership_name": dealer_name,
            "distance_nm": dist_nm,
            "ferry_delivery_fee_eur": ferry_fee
        }
