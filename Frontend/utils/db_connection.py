import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "Dataset" / "Astra_Case.csv"
SQLITE_DB_PATH = PROJECT_ROOT / "Backend" / "app" / "predictive_maintenance.db"
DEFAULT_POSTGRES_URL = "postgresql://postgres:sqlpresuniv03@localhost:5432/Final_Project"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_POSTGRES_URL)


def _build_postgres_engine():
    return create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


def _build_sqlite_engine():
    SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{SQLITE_DB_PATH}", future=True)


def get_engine():
    try:
        engine = _build_postgres_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return engine, "postgresql"
    except Exception:
        return _build_sqlite_engine(), "sqlite"


def load_data():
    engine, source = get_engine()
    try:
        table_df = pd.read_sql("SELECT * FROM astra_case", engine)
        if not table_df.empty:
            return table_df, source
    except Exception:
        pass

    df = pd.read_csv(DATASET_PATH)
    try:
        df.to_sql("astra_case", engine, if_exists="replace", index=False)
        return pd.read_sql("SELECT * FROM astra_case", engine), source
    except Exception:
        return df, "csv"


def load_dashboard_data():
    df, source = load_data()
    if df.empty:
        return pd.DataFrame(), source

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for column in ["product_id", "type", "motor_id"]:
        if column not in df.columns and "product_id" in df.columns:
            df["motor_id"] = df["product_id"]

    if "motor_id" not in df.columns and "product_id" in df.columns:
        df["motor_id"] = df["product_id"]
    if "motor_id" not in df.columns:
        df["motor_id"] = [f"M{i:03d}" for i in range(1, len(df) + 1)]

    rename_map = {
        "product_id": "product_id",
        "type": "type",
        "rotational_speed": "rotation_speed",
        "electrical_current": "electrical_current",
        "air_temperature": "air_temperature",
        "process_temperature": "process_temperature",
        "tool_wear": "tool_wear",
        "machine_failure": "machine_failure",
        "rul": "rul",
    }
    for old_name, new_name in rename_map.items():
        if old_name in df.columns and new_name not in df.columns:
            df[new_name] = df[old_name]

    return df, source