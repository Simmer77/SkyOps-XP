import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.models.schema import Company, Aircraft
from app.services.xp_connector import xp_connector
from app.services.flight_tracker import flight_tracker
from app.services.maintenance import MaintenanceService
from app.api import fleet, jobs, simbrief, flights, system, finances, company

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SkyOps.Main")

background_tasks = set()

async def xp_telemetry_loop():
    """Background async worker handling UDP receive & flight state machine"""
    logger.info("Starting background X-Plane UDP loop...")
    xp_connector.start()
    
    # Request subscriptions periodically
    sub_counter = 0
    failure_check_counter = 0
    
    while xp_connector.is_running:
        try:
            # 1. Non-blocking read incoming UDP packets
            xp_connector.read_incoming()
            
            # 2. Re-subscribe to datarefs every 5 seconds (or on reconnect)
            sub_counter += 1
            if sub_counter >= 50:
                sub_counter = 0
                xp_connector.subscribe_all(freq_hz=5)
                
            # 3. Step flight tracker state machine
            flight_tracker.update_cycle()
            
            # 4. In-flight component failure evaluations (every 10s during ENROUTE)
            if flight_tracker.phase == "ENROUTE" and flight_tracker.active_aircraft_id:
                failure_check_counter += 1
                if failure_check_counter >= 100:
                    failure_check_counter = 0
                    async with AsyncSessionLocal() as session:
                        ac = await session.get(Aircraft, flight_tracker.active_aircraft_id)
                        if ac:
                            failure = MaintenanceService.evaluate_in_flight_failures(ac)
                            if failure:
                                logger.warning(f"⚠️ In-flight failure triggered: {failure[1]}")
                                
            await asyncio.sleep(0.05) # 20 Hz loop
        except Exception as e:
            logger.error(f"Error in telemetry loop: {e}")
            await asyncio.sleep(0.5)

async def seed_initial_data():
    """Populates company and starter fleet based on user's hangar"""
    async with AsyncSessionLocal() as session:
        # Check company
        res = await session.execute(select(Company).limit(1))
        company = res.scalars().first()
        if not company:
            company = Company(
                name="AeroSky Executive Ops",
                cash_balance=175000.0,
                reputation=100.0,
                simbrief_username=""
            )
            session.add(company)
            
        # Check aircraft
        ac_res = await session.execute(select(Aircraft).limit(1))
        if not ac_res.scalars().first():
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            starter_fleet = [
                Aircraft(
                    tail_number="N516SF",
                    aircraft_type="SF50",
                    name="Cirrus Vision SF50 G2",
                    category="GA",
                    ownership="OWNED",
                    current_icao="MD47",
                    fuel_capacity_kg=907.0,
                    fuel_quantity_kg=591.0,
                    airframe_hours=64.2,
                    engine_hours=64.2,
                    year_manufactured=2022,
                    purchase_date=now - timedelta(days=240),
                    purchase_price_eur=2450000.0,
                    image_url="https://images.unsplash.com/photo-1540962351504-03099e0a754b?auto=format&fit=crop&w=800&q=80",
                    engine_type="1x Williams International FJ33-5A Turbofan (1.846 lbf)",
                    avionics_system="Cirrus Perspective+ by Garmin (G3000 Touch)",
                    next_50h_inspection_hours=100.0,
                    next_100h_inspection_hours=150.0,
                    next_annual_inspection=now + timedelta(days=185),
                    health_engine_pct=98.0,
                    health_brakes_pct=96.0,
                    health_tires_pct=94.0,
                    health_airframe_pct=99.0,
                    health_avionics_pct=100.0
                ),
                Aircraft(
                    tail_number="I-ECLI",
                    aircraft_type="E550",
                    name="Eclipse 550 NG",
                    category="BIZJET",
                    ownership="OWNED",
                    current_icao="LIPZ",
                    fuel_capacity_kg=1140.0,
                    fuel_quantity_kg=750.0,
                    airframe_hours=142.0,
                    engine_hours=142.0,
                    year_manufactured=2018,
                    purchase_date=now - timedelta(days=410),
                    purchase_price_eur=1650000.0,
                    image_url="https://images.unsplash.com/photo-1519074069444-1ba4ea16e6f9?auto=format&fit=crop&w=800&q=80",
                    engine_type="2x Pratt & Whitney Canada PW610F Turbofan (900 lbf)",
                    avionics_system="Avio IFIS Dual FMS Integrated Flight Deck",
                    next_50h_inspection_hours=150.0,
                    next_100h_inspection_hours=200.0,
                    next_annual_inspection=now + timedelta(days=92),
                    health_engine_pct=95.0,
                    health_brakes_pct=91.0,
                    health_tires_pct=89.0,
                    health_airframe_pct=97.0,
                    health_avionics_pct=99.0
                ),
                Aircraft(
                    tail_number="I-PHEN",
                    aircraft_type="E55P",
                    name="Embraer Phenom 300",
                    category="BIZJET",
                    ownership="OWNED",
                    current_icao="LIRN",
                    fuel_capacity_kg=2450.0,
                    fuel_quantity_kg=1600.0,
                    airframe_hours=210.5,
                    engine_hours=210.5,
                    year_manufactured=2020,
                    purchase_date=now - timedelta(days=320),
                    purchase_price_eur=8950000.0,
                    image_url="https://images.unsplash.com/photo-1583863788434-e58a36330cf0?auto=format&fit=crop&w=800&q=80",
                    engine_type="2x Pratt & Whitney Canada PW535E Turbofan (3.360 lbf)",
                    avionics_system="Prodigy Touch Flight Deck (Garmin G3000)",
                    next_50h_inspection_hours=250.0,
                    next_100h_inspection_hours=300.0,
                    next_annual_inspection=now + timedelta(days=240),
                    health_engine_pct=93.0,
                    health_brakes_pct=88.0,
                    health_tires_pct=87.0,
                    health_airframe_pct=96.0,
                    health_avionics_pct=98.0
                ),
                Aircraft(
                    tail_number="I-BOEI",
                    aircraft_type="B738",
                    name="Boeing 737-800X (Zibo)",
                    category="AIRLINER",
                    ownership="LEASED",
                    current_icao="LIRF",
                    fuel_capacity_kg=20800.0,
                    fuel_quantity_kg=8500.0,
                    hourly_lease_rate=1850.0,
                    airframe_hours=1840.0,
                    engine_hours=1840.0,
                    year_manufactured=2015,
                    purchase_date=now,
                    purchase_price_eur=44000000.0,
                    image_url="https://images.unsplash.com/photo-1569154941061-e231b4725ef1?auto=format&fit=crop&w=800&q=80",
                    engine_type="2x CFM International CFM56-7B26 High-Bypass Turbofan",
                    avionics_system="Rockwell Collins / Honeywell CDS Electronic Flight Bag",
                    next_50h_inspection_hours=1850.0,
                    next_100h_inspection_hours=1900.0,
                    next_annual_inspection=now + timedelta(days=120),
                    health_engine_pct=96.0,
                    health_brakes_pct=92.0,
                    health_tires_pct=91.0,
                    health_airframe_pct=98.0,
                    health_avionics_pct=97.0
                )
            ]
            for ac in starter_fleet:
                session.add(ac)
                
        await session.commit()
        logger.info("Database initialized with starter fleet and company profile.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    loop_task = asyncio.create_task(xp_telemetry_loop())
    background_tasks.add(loop_task)
    yield
    # Shutdown
    xp_connector.stop()
    for task in background_tasks:
        task.cancel()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Operations & Economy Platform for X-Plane 12 with SimBrief Integration",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fleet.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(simbrief.router, prefix="/api")
app.include_router(flights.router, prefix="/api")
app.include_router(finances.router, prefix="/api")
app.include_router(company.router, prefix="/api")
app.include_router(system.router, prefix="/api")

# Serve static uploaded images
from fastapi.staticfiles import StaticFiles
import os

uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static/uploads"))
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Serve Frontend static assets if built

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../SkyOps-XP/frontend/dist"))
if not os.path.exists(frontend_dist):
    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))

if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.VERSION,
            "status": "online",
            "docs": "/docs"
        }

