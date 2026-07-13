import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POSTGRES_URL = "postgresql://postgres:sqlpresuniv03@localhost:5432/Final_Project"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_POSTGRES_URL)
SQLITE_DB_PATH = PROJECT_ROOT / "Backend" / "app" / "predictive_maintenance.db"


def _build_engine():
    if DATABASE_URL.startswith("postgresql"):
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return engine
        except Exception:
            sqlite_url = f"sqlite:///{SQLITE_DB_PATH}"
            return create_engine(sqlite_url, future=True)
    return create_engine(f"sqlite:///{SQLITE_DB_PATH}", future=True)


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from Backend.app.models.equipment import Equipment
    from Backend.app.models.monitoring import Alert, MotorAnalysisHistory, MotorSensorData

    Base.metadata.create_all(bind=engine)
    return True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()