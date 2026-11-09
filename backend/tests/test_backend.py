import asyncio
from app.core.database import init_db, AsyncSessionLocal
from app.main import seed_initial_data
from app.models.schema import Aircraft, Company
from sqlalchemy.future import select
from app.services.job_generator import JobGenerator
from app.services.maintenance import MaintenanceService
from app.services.economy import EconomyService

async def main():
    print("1. Initializing DB...")
    await init_db()
    
    print("2. Seeding initial fleet and company...")
    await seed_initial_data()
    
    async with AsyncSessionLocal() as session:
        comp_res = await session.execute(select(Company))
        company = comp_res.scalars().first()
        print(f"Company: {company.name}, Balance: ${company.cash_balance:,.2f}")
        
        fleet_res = await session.execute(select(Aircraft))
        fleet = fleet_res.scalars().all()
        print(f"Fleet count: {len(fleet)}")
        for ac in fleet:
            print(f"  - [{ac.category}] {ac.tail_number} ({ac.name}) @ {ac.current_icao} | Fuel: {ac.fuel_quantity_kg:.1f}kg | Engine: {ac.health_engine_pct}%")

    print("\n3. Testing Job Generator for MD47 (Cirrus base)...")
    jobs = JobGenerator.generate_jobs_for_airport("MD47", "GA", count=4)
    for j in jobs:
        print(f"  - [{j['job_type']}] {j['title']} | Dist: {j['distance_nm']} nm | Reward: ${j['reward_usd']:,.2f}")

    print("\n4. Testing Financials & Maintenance calculation...")
    fin = EconomyService.calculate_flight_financials(
        category="GA",
        fuel_burned_kg=120.0,
        flight_hours=1.5,
        job_reward=1850.0
    )
    print(f"  - Financials: Revenue ${fin['gross_revenue']} - Fuel ${fin['fuel_cost']} - Landing ${fin['landing_fee']} = Net Profit ${fin['net_profit']}")
    
    wear = MaintenanceService.calculate_flight_wear(
        flight_hours=1.5,
        touchdown_fpm=-120.0, # Butter!
        touchdown_g=1.1,
        max_g=1.3,
        min_g=0.9
    )
    print(f"  - Wear applied: {wear}")
    print("\nBackend test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
