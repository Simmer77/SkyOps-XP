import random
import math
from typing import List, Dict, Any

# Popular airport coordinates & reference data for European and North American routes
AIRPORT_COORDS = {
    # Italy
    "LIRN": ("Napoli Capodichino", 40.8860, 14.2908, "LIRN"),
    "LIRF": ("Roma Fiumicino", 41.8003, 12.2389, "LIRF"),
    "LIRA": ("Roma Ciampino", 41.7994, 12.5949, "LIRA"),
    "LIMC": ("Milano Malpensa", 45.6306, 8.7281, "LIMC"),
    "LIML": ("Milano Linate", 45.4451, 9.2767, "LIML"),
    "LIPZ": ("Venezia Tessera", 45.5053, 12.3519, "LIPZ"),
    "LICC": ("Catania Fontanarossa", 37.4668, 15.0664, "LICC"),
    "LICJ": ("Palermo Punta Raisi", 38.1760, 13.0910, "LICJ"),
    "LIEO": ("Olbia Costa Smeralda", 40.8987, 9.5176, "LIEO"),
    "LIEE": ("Cagliari Elmas", 39.2515, 9.0543, "LIEE"),
    "LIPX": ("Verona Villafranca", 45.3957, 10.8885, "LIPX"),
    "LIPE": ("Bologna Borgo Panigale", 44.5354, 11.2887, "LIPE"),
    "LIRZ": ("Perugia San Francesco", 43.0959, 12.5132, "LIRZ"),
    "LIMP": ("Parma Giuseppe Verdi", 44.8239, 10.2955, "LIMP"),
    "LIBD": ("Bari Palese", 41.1389, 16.7606, "LIBD"),
    "LFMN": ("Nice Côte d'Azur", 43.6653, 7.2150, "LFMN"),
    "LSGG": ("Geneva Cointrin", 46.2381, 6.1089, "LSGG"),
    "LSZH": ("Zurich", 47.4647, 8.5492, "LSZH"),
    "LOWI": ("Innsbruck", 47.2602, 11.3440, "LOWI"),
    # USA (East Coast / Cirrus / Vision Jet playground)
    "MD47": ("Windsock Field MD", 39.3800, -77.2100, "MD47"),
    "KDCA": ("Washington Reagan", 38.8512, -77.0377, "KDCA"),
    "KIAD": ("Washington Dulles", 38.9445, -77.4558, "KIAD"),
    "KLGA": ("New York LaGuardia", 40.7769, -73.8740, "KLGA"),
    "KJFK": ("New York JFK", 40.6398, -73.7789, "KJFK"),
    "KBOS": ("Boston Logan", 42.3656, -71.0096, "KBOS"),
    "KMIA": ("Miami International", 25.7959, -80.2870, "KMIA"),
    "KPBI": ("Palm Beach", 26.6832, -80.0956, "KPBI"),
    "KTEB": ("Teterboro VIP", 40.8501, -74.0608, "KTEB"),
}

JOB_TYPES = [
    {
        "type": "VIP",
        "title": "Trasporto Passeggeri VIP",
        "base_rate_nm": 18.5,
        "pax_range": (1, 5),
        "cargo_range": (50, 150),
        "categories": ["GA", "BIZJET"]
    },
    {
        "type": "CARGO",
        "title": "Spedizione Cargo Urgente Ricambi",
        "base_rate_nm": 14.0,
        "pax_range": (0, 0),
        "cargo_range": (200, 800),
        "categories": ["GA", "BIZJET", "AIRLINER"]
    },
    {
        "type": "MEDEVAC",
        "title": "Volo Sanitario Urgente",
        "base_rate_nm": 22.0,
        "pax_range": (2, 3),
        "cargo_range": (80, 150),
        "categories": ["GA", "BIZJET"]
    },
    {
        "type": "PASSENGER",
        "title": "Volo Navetta Charter",
        "base_rate_nm": 28.0,
        "pax_range": (6, 160),
        "cargo_range": (500, 4500),
        "categories": ["BIZJET", "AIRLINER"]
    }
]

def calculate_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3440.065 # Earth radius in nautical miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

class JobGenerator:
    @staticmethod
    def generate_jobs_for_airport(origin_icao: str, category: str = "GA", count: int = 5) -> List[Dict[str, Any]]:
        """
        Generates 4-5 realistic jobs originating from the given airport.
        """
        origin_icao = origin_icao.upper()
        if origin_icao not in AIRPORT_COORDS:
            # Fallback if unknown airport
            ref_lat, ref_lon = 41.8003, 12.2389
        else:
            _, ref_lat, ref_lon, _ = AIRPORT_COORDS[origin_icao]
            
        # Filter possible destinations
        dest_candidates = [
            (icao, data) for icao, data in AIRPORT_COORDS.items()
            if icao != origin_icao
        ]
        
        # Calculate distances
        distances = []
        for icao, (name, lat, lon, _) in dest_candidates:
            dist = calculate_distance_nm(ref_lat, ref_lon, lat, lon)
            # Filter realistic range for flight
            if 30 <= dist <= 1200:
                distances.append((icao, name, dist))
                
        if not distances:
            # Fallback destinations if far
            distances = [(k, v[0], 250.0) for k, v in list(AIRPORT_COORDS.items())[:5] if k != origin_icao]
            
        random.shuffle(distances)
        selected_destinations = distances[:count]
        
        jobs = []
        for icao, name, dist in selected_destinations:
            # Match job type to category
            matching_templates = [t for t in JOB_TYPES if category in t["categories"]]
            if not matching_templates:
                matching_template = JOB_TYPES[0]
            else:
                matching_template = random.choice(matching_templates)
                
            pax = random.randint(matching_template["pax_range"][0], matching_template["pax_range"][1])
            cargo = round(random.uniform(matching_template["cargo_range"][0], matching_template["cargo_range"][1]), 0)
            
            # Calculate dynamic reward based on distance and urgency/type
            rate = matching_template["base_rate_nm"] * random.uniform(0.9, 1.25)
            if category == "AIRLINER":
                reward = round(dist * rate * max(1, pax * 0.4), 0)
            else:
                reward = round(dist * rate + (pax * 120) + (cargo * 1.5), 0)
                
            jobs.append({
                "title": f"{matching_template['title']} verso {name} ({icao})",
                "job_type": matching_template["type"],
                "origin_icao": origin_icao,
                "destination_icao": icao,
                "distance_nm": dist,
                "pax_count": pax,
                "cargo_kg": cargo,
                "required_category": category,
                "reward_usd": max(350.0, reward),
                "penalty_usd": round(reward * 0.15, 0),
                "status": "AVAILABLE"
            })
            
        return jobs
