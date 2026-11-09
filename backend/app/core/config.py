import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "SkyOps XP"
    VERSION: str = "1.0.0"
    
    # X-Plane 12 Network Configuration
    XP_IP: str = os.getenv("XP_IP", "127.0.0.1")
    XP_UDP_PORT: int = int(os.getenv("XP_UDP_PORT", "49000"))
    XP_LISTEN_PORT: int = int(os.getenv("XP_LISTEN_PORT", "49005"))
    XP_WEB_API_PORT: int = int(os.getenv("XP_WEB_API_PORT", "8086"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///skyops.db")
    
    # SimBrief
    SIMBRIEF_API_URL: str = "https://www.simbrief.com/api/xml.fetcher.php"
    
    # Economics
    DEFAULT_FUEL_PRICE_USD_PER_KG: float = 1.65  # ~$5.00/gal Jet-A
    AVG_LANDING_FEE_PER_TONNE_USD: float = 8.50
    VIRTUAL_DAYS_PER_FLIGHT: int = 3  # Time advancement per flight

settings = Settings()
