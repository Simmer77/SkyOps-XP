import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.schema import Aircraft, Job, FlightLog, Company, CrewMember
from app.services.xp_connector import xp_connector
from app.services.maintenance import MaintenanceService
from app.services.economy import EconomyService
from app.services.dealerships import DealershipService

logger = logging.getLogger("SkyOps.Tracker")

class FlightTracker:
    def __init__(self):
        self.active_aircraft_id: Optional[int] = None
        self.active_job_id: Optional[int] = None
        self.active_flight_id: Optional[int] = None
        
        # Flight state
        self.phase = "OFFLINE" # "BOARDING", "TAXI_OUT", "ENROUTE", "TOUCHDOWN", "TAXI_IN", "COMPLETED"
        self.start_fuel_kg: float = 0.0
        self.current_fuel_kg: float = 0.0
        self.start_time: Optional[datetime] = None
        
        # Flight dynamics
        self.max_g: float = 1.0
        self.min_g: float = 1.0
        self.touchdown_fpm: Optional[float] = None
        self.touchdown_g: Optional[float] = None
        self.touchdown_rating: Optional[str] = None
        self.was_in_air: bool = False
        self.exclude_crew_cost: bool = False
        self.flight_rules: str = "IFR"
        self.tour_id: Optional[int] = None
        
        self.loop_task: Optional[asyncio.Task] = None
        self.last_failure_check = 0.0

    def start_flight(
        self,
        aircraft_id: int,
        job_id: Optional[int] = None,
        exclude_crew_cost: bool = False,
        flight_rules: str = "IFR",
        tour_id: Optional[int] = None
    ):
        """Initializes a new tracked flight session"""
        self.active_aircraft_id = aircraft_id
        self.active_job_id = job_id
        self.phase = "BOARDING"
        self.start_time = datetime.now(timezone.utc)
        self.max_g = 1.0
        self.min_g = 1.0
        self.touchdown_fpm = None
        self.touchdown_g = None
        self.touchdown_rating = None
        self.was_in_air = False
        self.exclude_crew_cost = bool(exclude_crew_cost)
        self.flight_rules = (flight_rules or "IFR").strip().upper()
        self.tour_id = tour_id
        
        t = xp_connector.telemetry
        self.start_fuel_kg = t.get("fuel_total_kg", 0.0)
        self.current_fuel_kg = self.start_fuel_kg
        logger.info(f"Flight session initialized for Aircraft #{aircraft_id}, Job #{job_id}")

    def update_cycle(self):
        """Called periodically (e.g. 5-10 times/sec) by background worker"""
        t = xp_connector.telemetry
        if not xp_connector.is_connected or not self.active_aircraft_id:
            return

        g_force = t.get("g_force", 1.0)
        if g_force > self.max_g:
            self.max_g = g_force
        if g_force < self.min_g:
            self.min_g = g_force
            
        on_ground = bool(t.get("on_ground", 1.0) > 0.5)
        ias = t.get("ias_kts", 0.0)
        gs = t.get("groundspeed_kts", 0.0)
        vs = t.get("vs_fpm", 0.0)
        self.current_fuel_kg = t.get("fuel_total_kg", self.current_fuel_kg)
        
        # State machine transitions
        if self.phase == "BOARDING":
            if gs > 3.0 and not on_ground: # already airborne or taking off
                self.phase = "ENROUTE"
                self.was_in_air = True
            elif gs > 3.0 and on_ground:
                self.phase = "TAXI_OUT"
                
        elif self.phase == "TAXI_OUT":
            if not on_ground or (ias > 55.0 and not on_ground):
                self.phase = "ENROUTE"
                self.was_in_air = True
                logger.info("🛫 Airborne! Phase changed to ENROUTE.")
                
        elif self.phase == "ENROUTE":
            # Landing detection: airborne -> ground transition
            if on_ground:
                self.phase = "TOUCHDOWN"
                self.touchdown_fpm = round(vs, 1)
                self.touchdown_g = round(g_force, 2)
                self._rate_touchdown(self.touchdown_fpm, self.touchdown_g)
                logger.info(f"🛬 Touchdown! FPM: {self.touchdown_fpm}, G: {self.touchdown_g} ({self.touchdown_rating})")
                
        elif self.phase == "TOUCHDOWN":
            if gs < 35.0:
                self.phase = "TAXI_IN"
                
        elif self.phase == "TAXI_IN":
            # Detect shutdown at parking (parking brake engaged and stopped or engine off)
            engine_running = t.get("engine_running", 0.0)
            parking_brake = t.get("parking_brake", 0.0)
            if gs < 1.0 and (parking_brake > 0.8 or engine_running < 0.1):
                logger.info("🅿️ Parked and secured. Ready for flight closing.")
                self.phase = "PARKED"

    def _rate_touchdown(self, fpm: float, g: float):
        abs_fpm = abs(fpm)
        if abs_fpm < 160 and g < 1.4:
            self.touchdown_rating = "BUTTER"
        elif abs_fpm < 300 and g < 1.8:
            self.touchdown_rating = "GOOD"
        elif abs_fpm < 550 and g < 2.3:
            self.touchdown_rating = "HARD"
        else:
            self.touchdown_rating = "STRUCTURAL_DAMAGE"

    async def finalize_flight(
        self,
        actual_arrival_icao: Optional[str] = None,
        diversion_reason: Optional[str] = None,
        exclude_crew_cost: Optional[bool] = None,
        flight_rules: Optional[str] = None,
        tour_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Finalizes active flight, saves records to DB, applies wear & finances.
        Supports diversion / emergency arrival at an alternate airport.
        """
        if not self.active_aircraft_id:
            return None
            
        end_time = datetime.now(timezone.utc)
        duration_hours = max(0.1, (end_time - (self.start_time or end_time)).total_seconds() / 3600.0)
        fuel_burned = max(0.0, self.start_fuel_kg - self.current_fuel_kg)
        
        async with AsyncSessionLocal() as session:
            # 1. Fetch Aircraft & Job & Company
            aircraft = await session.get(Aircraft, self.active_aircraft_id)
            if not aircraft:
                return None
                
            job = await session.get(Job, self.active_job_id) if self.active_job_id else None
            if not job:
                # Fallback: check if there's an IN_PROGRESS or ACCEPTED job assigned to this aircraft
                job_res = await session.execute(
                    select(Job).where(Job.aircraft_id == aircraft.id, Job.status.in_(["IN_PROGRESS", "ACCEPTED"])).order_by(Job.id.desc())
                )
                job = job_res.scalars().first()
            
            comp_res = await session.execute(select(Company).limit(1))
            company = comp_res.scalars().first()
            if not company:
                company = Company()
                session.add(company)
                await session.flush()
                
            orig_icao = job.origin_icao if job else aircraft.current_icao
            planned_dest = job.destination_icao if job else aircraft.current_icao
            final_dest = actual_arrival_icao.strip().upper() if (actual_arrival_icao and actual_arrival_icao.strip()) else planned_dest
            
            is_home_base = bool(company.home_base_icao and final_dest.upper() == company.home_base_icao.upper())

            # Distance & Rules & Tour & Salaried Crew Resolution
            xp_path = company.xp12_install_path if company else None
            dist_nm = (job.distance_nm if (job and job.distance_nm and job.distance_nm > 0) else None)
            if not dist_nm and orig_icao and final_dest and orig_icao != final_dest:
                dist_nm = DealershipService.distance_between_icaos_nm(orig_icao, final_dest, xp_path)
            dist_nm = dist_nm or 0.0

            pax_count = int(job.pax_count or 0) if job else 0
            eff_rules = (
                flight_rules.strip().upper()
                if (flight_rules and flight_rules.strip())
                else ((getattr(job, "flight_rules", None) if job else None) or self.flight_rules or "IFR")
            ).upper()
            is_ifr = (eff_rules != "VFR")
            eff_tour_id = tour_id if tour_id is not None else (self.tour_id if self.tour_id is not None else (getattr(job, "tour_id", None) if job else None))

            salaried_crew = (
                await session.execute(
                    select(CrewMember).where(CrewMember.category == aircraft.category, CrewMember.is_active == True)
                )
            ).scalars().first()
            has_salaried_crew = salaried_crew is not None

            # 2. Financial calculation (incl. Eurocontrol, Handling, Crew mode, Reputation Bonus/Penalties)
            job_reward = job.reward_usd if job else 0.0
            is_leased = (aircraft.ownership == "LEASED")
            effective_exclude_crew = (
                bool(exclude_crew_cost)
                if exclude_crew_cost is not None
                else bool(self.exclude_crew_cost or (job and getattr(job, "exclude_crew_cost", False)))
            )
            old_reputation = company.reputation if company.reputation is not None else 100.0
            financials = EconomyService.calculate_flight_financials(
                category=aircraft.category,
                fuel_burned_kg=fuel_burned,
                flight_hours=duration_hours,
                job_reward=job_reward,
                is_leased=is_leased,
                lease_rate_hourly=aircraft.hourly_lease_rate,
                is_home_base=is_home_base,
                exclude_crew_cost=effective_exclude_crew,
                mtow_kg=aircraft.mtow_kg or 0.0,
                distance_nm=dist_nm,
                pax_count=pax_count,
                is_ifr=is_ifr,
                has_salaried_crew=has_salaried_crew,
                company_reputation=old_reputation,
                touchdown_rating=self.touchdown_rating,
                max_g=self.max_g,
                min_g=self.min_g,
                origin_icao=orig_icao,
                destination_icao=final_dest
            )
            company.reputation = financials["new_reputation"]
            
            # 3. Calculate and apply wear
            wear = MaintenanceService.calculate_flight_wear(
                flight_hours=duration_hours,
                touchdown_fpm=self.touchdown_fpm,
                touchdown_g=self.touchdown_g,
                max_g=self.max_g,
                min_g=self.min_g
            )
            
            aircraft.health_engine_pct = max(0.0, aircraft.health_engine_pct - wear["engine"])
            aircraft.health_airframe_pct = max(0.0, aircraft.health_airframe_pct - wear["airframe"])
            aircraft.health_brakes_pct = max(0.0, aircraft.health_brakes_pct - wear["brakes"])
            aircraft.health_tires_pct = max(0.0, aircraft.health_tires_pct - wear["tires"])
            aircraft.health_avionics_pct = max(0.0, aircraft.health_avionics_pct - wear["avionics"])
            
            aircraft.airframe_hours += duration_hours
            aircraft.engine_hours += duration_hours
            aircraft.fuel_quantity_kg = self.current_fuel_kg
            aircraft.is_in_flight = False
            
            diversion_note = None
            if final_dest != planned_dest:
                diversion_note = f"Dirottato / Emergenza verso {final_dest} (pianificato: {planned_dest}). {diversion_reason or ''}".strip()

            aircraft.current_icao = final_dest
            if job:
                job.status = "COMPLETED"
            
            # 4. Save FlightLog
            log = FlightLog(
                flight_number=f"SO{aircraft.tail_number[-3:] if aircraft.tail_number else '100'}",
                aircraft_id=aircraft.id,
                job_id=job.id if job else None,
                origin_icao=orig_icao,
                destination_icao=final_dest,
                start_time=self.start_time,
                end_time=end_time,
                flight_duration_min=round(duration_hours * 60, 1),
                distance_flown_nm=round(dist_nm, 1),
                fuel_used_kg=round(fuel_burned, 1),
                max_g_force=round(self.max_g, 2),
                min_g_force=round(self.min_g, 2),
                touchdown_fpm=self.touchdown_fpm,
                touchdown_g=self.touchdown_g,
                touchdown_rating=self.touchdown_rating,
                revenue_usd=financials["gross_revenue"],
                fuel_cost_usd=financials["fuel_cost"],
                landing_fee_usd=financials["landing_fee"],
                lease_cost_usd=financials["lease_cost"],
                crew_cost_usd=financials["crew_cost"],
                nav_fee_eur=financials["nav_fee"],
                handling_fee_eur=financials["handling_fee"],
                reputation_delta=financials["reputation_delta"],
                reputation_bonus_eur=financials["reputation_bonus_eur"],
                penalty_eur=financials["penalty_eur"],
                flight_rules=eff_rules,
                pax_count=pax_count,
                tour_id=eff_tour_id,
                net_profit_usd=financials["net_profit"],
                notes=diversion_note,
                status="COMPLETED"
            )
            session.add(log)
            await session.flush()

            # 5. Record granular transactions in Financial Ledger (updates company.cash_balance atomically)
            dest = final_dest
            orig = orig_icao
            route_str = f"{orig} ➔ {dest}"

            if financials["gross_revenue"] > 0:
                bonus_note = ""
                if financials["reputation_bonus_eur"] > 0:
                    bonus_note = f" (incl. Bonus Qualità +{financials['reputation_bonus_pct']:.0f}% = +{financials['reputation_bonus_eur']:.2f} €)"
                elif financials["reputation_bonus_eur"] < 0:
                    bonus_note = f" (riduzione reputazione {financials['reputation_bonus_pct']:.0f}%)"
                await EconomyService.record_transaction(
                    session=session,
                    category="REVENUE",
                    title=f"Ricavo Volo {log.flight_number} ({route_str})",
                    amount_eur=financials["gross_revenue"],
                    description=f"Compenso contratto completato con {aircraft.tail_number}{bonus_note}",
                    aircraft_tail=aircraft.tail_number,
                    flight_id=log.id,
                    company=company
                )
            if financials["fuel_cost"] > 0:
                await EconomyService.record_transaction(
                    session=session,
                    category="FUEL",
                    title=f"Consumo Jet-A1 ({fuel_burned:.1f} kg)",
                    amount_eur=-financials["fuel_cost"],
                    description=f"Carburante bruciato rotta {route_str}",
                    aircraft_tail=aircraft.tail_number,
                    flight_id=log.id,
                    company=company
                )
            if financials["landing_fee"] > 0:
                discount_pct = financials.get("landing_fee_discount_pct", 0)
                fee_title = f"Tassa Atterraggio {dest} (Base Operativa -{discount_pct}%)" if is_home_base else f"Tassa Atterraggio {dest}"
                fee_desc = (
                    f"Tariffa residente Base Operativa {dest} (-{discount_pct}% su {aircraft.tail_number}, {aircraft.category})"
                    if is_home_base
                    else f"Tassa aeroportuale e assistenza a terra per {aircraft.tail_number} ({aircraft.category})"
                )
                await EconomyService.record_transaction(
                    session=session,
                    category="LANDING_FEE",
                    title=fee_title,
                    amount_eur=-financials["landing_fee"],
                    description=fee_desc,
                    aircraft_tail=aircraft.tail_number,
                    flight_id=log.id,
                    company=company
                )
            if financials["lease_cost"] > 0:
                await EconomyService.record_transaction(
                    session=session,
                    category="LEASE",
                    title=f"Canone Noleggio {aircraft.tail_number}",
                    amount_eur=-financials["lease_cost"],
                    description=f"Block time {duration_hours:.2f} ore a {aircraft.hourly_lease_rate:.2f} €/h",
                    aircraft_tail=aircraft.tail_number,
                    flight_id=log.id,
                    company=company
                )
            if financials["crew_cost"] > 0:
                await EconomyService.record_transaction(
                    session=session,
                    category="CREW",
                    title=f"Equipaggio Volo {log.flight_number} ({financials['crew_label']})",
                    amount_eur=-financials["crew_cost"],
                    description=f"Personale di bordo ({duration_hours:.2f} ore a € {financials['crew_hourly_rate_eur']:.0f}/h) su {aircraft.tail_number}",
                    aircraft_tail=aircraft.tail_number,
                    flight_id=log.id,
                    company=company
                )
            if financials["nav_fee"] > 0:
                await EconomyService.record_transaction(
                    session=session,
                    category="NAV_FEE",
                    title=f"Navigazione Eurocontrol {route_str}",
                    amount_eur=-financials["nav_fee"],
                    description=f"Tariffa di rotta IFR su {dist_nm:.0f} NM per {aircraft.tail_number}",
                    aircraft_tail=aircraft.tail_number,
                    flight_id=log.id,
                    company=company
                )
            if financials["handling_fee"] > 0:
                await EconomyService.record_transaction(
                    session=session,
                    category="HANDLING",
                    title=f"Catering & Handling ({pax_count} Pax)",
                    amount_eur=-financials["handling_fee"],
                    description=f"Servizi passeggeri, catering e imbarco per {route_str} ({aircraft.category})",
                    aircraft_tail=aircraft.tail_number,
                    flight_id=log.id,
                    company=company
                )
            if financials["penalty_eur"] > 0:
                await EconomyService.record_transaction(
                    session=session,
                    category="PENALTY",
                    title=f"Penale / Risarcimento Atterraggio ({self.touchdown_rating or 'HARD'})",
                    amount_eur=-financials["penalty_eur"],
                    description=f"Indennizzo passeggeri e ispezione straordinaria per atterraggio {self.touchdown_rating} ({self.touchdown_fpm} fpm)",
                    aircraft_tail=aircraft.tail_number,
                    flight_id=log.id,
                    company=company
                )

            await session.commit()
            
            # Reset tracker state
            result = {
                "flight_log_id": log.id,
                "flight_number": log.flight_number,
                "tail_number": aircraft.tail_number,
                "aircraft_name": aircraft.name,
                "origin_icao": orig_icao,
                "destination_icao": final_dest,
                "duration_min": log.flight_duration_min,
                "distance_nm": log.distance_flown_nm,
                "fuel_used_kg": log.fuel_used_kg,
                "flight_rules": eff_rules,
                "tour_id": eff_tour_id,
                "notes": diversion_note,
                "financials": financials,
                "wear": wear,
                "touchdown": {
                    "fpm": self.touchdown_fpm,
                    "g": self.touchdown_g,
                    "rating": self.touchdown_rating
                },
                "reputation": {
                    "old": old_reputation,
                    "delta": financials["reputation_delta"],
                    "new": company.reputation,
                },
                "new_cash_balance": company.cash_balance
            }
            
            self.phase = "OFFLINE"
            self.active_aircraft_id = None
            self.active_job_id = None
            self.exclude_crew_cost = False
            self.flight_rules = "IFR"
            self.tour_id = None
            return result

flight_tracker = FlightTracker()
