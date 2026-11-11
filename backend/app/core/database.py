from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Safe migration for existing SQLite database to add newly introduced columns
        from sqlalchemy import text
        new_cols = [
            ("year_manufactured", "INTEGER DEFAULT 2021"),
            ("purchase_date", "DATETIME"),
            ("purchase_price_eur", "FLOAT DEFAULT 0.0"),
            ("image_url", "TEXT DEFAULT ''"),
            ("engine_type", "TEXT DEFAULT 'Standard'"),
            ("avionics_system", "TEXT DEFAULT 'Standard Avionics'"),
            ("next_annual_inspection", "DATETIME"),
            ("next_50h_inspection_hours", "FLOAT DEFAULT 50.0"),
            ("next_100h_inspection_hours", "FLOAT DEFAULT 100.0"),
            ("manufacturer", "TEXT DEFAULT ''"),
            ("mtow_kg", "FLOAT DEFAULT 2700.0"),
            ("acquisition_mode", "TEXT DEFAULT 'OWNED_CASH'"),
            ("weekly_payment_eur", "FLOAT DEFAULT 0.0"),
            ("remaining_payments_weeks", "INTEGER DEFAULT 0"),
            ("financed_amount_remaining_eur", "FLOAT DEFAULT 0.0"),
        ]
        for col_name, col_type in new_cols:
            try:
                await conn.execute(text(f"ALTER TABLE aircraft ADD COLUMN {col_name} {col_type}"))
            except Exception:
                pass # Column already exists
                
        company_cols = [
            ("operating_day", "INTEGER DEFAULT 1"),
            ("home_base_icao", "TEXT DEFAULT 'LIRN'"),
            ("starting_capital_eur", "FLOAT DEFAULT 150000.0"),
            ("difficulty_level", "TEXT DEFAULT 'STANDARD'"),
            ("xp12_install_path", "TEXT DEFAULT ''"),
        ]
        for col_name, col_type in company_cols:
            try:
                await conn.execute(text(f"ALTER TABLE company ADD COLUMN {col_name} {col_type}"))
            except Exception:
                pass

        extra_migrations = [
            ("jobs", "exclude_crew_cost", "BOOLEAN DEFAULT 0"),
            ("flight_logs", "crew_cost_usd", "FLOAT DEFAULT 0.0"),
        ]
        for table_name, col_name, col_type in extra_migrations:
            try:
                await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
            except Exception:
                pass
