from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Company(Base):
    __tablename__ = "company"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="SkyOps Aviation")
    cash_balance = Column(Float, default=150000.0)  # Starting capital
    reputation = Column(Float, default=100.0)  # 0 to 100%
    virtual_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    simbrief_username = Column(String, nullable=True, default="")
    simbrief_pilot_id = Column(String, nullable=True, default="")

class Aircraft(Base):
    __tablename__ = "aircraft"
    
    id = Column(Integer, primary_key=True, index=True)
    tail_number = Column(String, unique=True, index=True)
    aircraft_type = Column(String, index=True)  # e.g. SF50, E550, B738, PH300
    name = Column(String)                       # e.g. "Cirrus Vision SF50 G2"
    category = Column(String, default="GA")     # "GA", "BIZJET", "AIRLINER"
    ownership = Column(String, default="OWNED") # "OWNED", "LEASED"
    
    current_icao = Column(String, default="LIRN") # Last airport parked
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Fuel State
    fuel_quantity_kg = Column(Float, default=450.0)
    fuel_capacity_kg = Column(Float, default=900.0)
    
    # Hours & Inspection
    airframe_hours = Column(Float, default=124.5)
    engine_hours = Column(Float, default=124.5)
    tbo_hours = Column(Float, default=3500.0)
    last_inspection_hours = Column(Float, default=100.0)
    
    # Health percentages (100% = Factory new, < 20% = Critical Failure risk)
    health_engine_pct = Column(Float, default=98.5)
    health_brakes_pct = Column(Float, default=95.0)
    health_tires_pct = Column(Float, default=94.0)
    health_airframe_pct = Column(Float, default=99.0)
    health_avionics_pct = Column(Float, default=100.0)
    
    # Economic rates
    hourly_lease_rate = Column(Float, default=0.0)
    hourly_maintenance_reserve = Column(Float, default=120.0) # $ / hour reserve
    
    is_in_flight = Column(Boolean, default=False)
    
    flights = relationship("FlightLog", back_populates="aircraft")
    jobs = relationship("Job", back_populates="aircraft")

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    job_type = Column(String) # "PASSENGER", "VIP", "CARGO", "MEDEVAC"
    
    origin_icao = Column(String, index=True)
    destination_icao = Column(String, index=True)
    distance_nm = Column(Float)
    
    pax_count = Column(Integer, default=0)
    cargo_kg = Column(Float, default=0.0)
    required_category = Column(String, default="GA") # "GA", "BIZJET", "AIRLINER"
    
    reward_usd = Column(Float)
    penalty_usd = Column(Float, default=0.0)
    status = Column(String, default="AVAILABLE") # "AVAILABLE", "ACCEPTED", "IN_PROGRESS", "COMPLETED", "FAILED"
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=True)
    aircraft = relationship("Aircraft", back_populates="jobs")

class FlightLog(Base):
    __tablename__ = "flight_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    
    origin_icao = Column(String)
    destination_icao = Column(String)
    
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    flight_duration_min = Column(Float, default=0.0)
    
    # Flight metrics
    distance_flown_nm = Column(Float, default=0.0)
    fuel_used_kg = Column(Float, default=0.0)
    max_g_force = Column(Float, default=1.0)
    min_g_force = Column(Float, default=1.0)
    touchdown_fpm = Column(Float, nullable=True)
    touchdown_g = Column(Float, nullable=True)
    touchdown_rating = Column(String, nullable=True) # "BUTTER", "GOOD", "HARD", "STRUCTURAL_DAMAGE"
    
    # Financial breakdown
    revenue_usd = Column(Float, default=0.0)
    fuel_cost_usd = Column(Float, default=0.0)
    landing_fee_usd = Column(Float, default=0.0)
    lease_cost_usd = Column(Float, default=0.0)
    maintenance_cost_usd = Column(Float, default=0.0)
    net_profit_usd = Column(Float, default=0.0)
    
    notes = Column(Text, nullable=True)
    status = Column(String, default="ACTIVE") # "ACTIVE", "COMPLETED", "ABORTED"
    
    aircraft = relationship("Aircraft", back_populates="flights")
    job = relationship("Job")

class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"
    
    id = Column(Integer, primary_key=True, index=True)
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"))
    event_type = Column(String) # "50H_INSPECTION", "100H_INSPECTION", "TIRE_REPLACE", "BRAKE_OVERHAUL", "ENGINE_TBO", "REPAIR_LANDING_DAMAGE"
    cost_usd = Column(Float)
    component = Column(String) # "ENGINE", "BRAKES", "TIRES", "AIRFRAME", "AVIONICS"
    health_restored_to = Column(Float, default=100.0)
    performed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(String, nullable=True)
