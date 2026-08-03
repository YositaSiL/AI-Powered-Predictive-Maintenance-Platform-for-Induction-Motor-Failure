import os
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.exceptions import InconsistentVersionWarning

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "Dataset" / "Astra_Case_cleaned.csv"
if not DATASET_PATH.exists():
    DATASET_PATH = PROJECT_ROOT / "Dataset" / "Astra_Case.csv"
SQLITE_DB_PATH = PROJECT_ROOT / "Backend" / "app" / "predictive_maintenance.db"
DEFAULT_POSTGRES_URL = "postgresql://postgres:sqlpresuniv03@localhost:5432/Final_Project"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_POSTGRES_URL)

# Model features expected by the trained RandomForest
MODEL_FEATURES = [
    "air_temperature",
    "process_temperature",
    "rotational_speed",
    "torque",
    "tool_wear",
    "pressure",
    "vibration",
    "electrical_current",
]


def _load_ml_model():
    """Load the trained ML model for failure probability prediction."""
    model_path = PROJECT_ROOT / "saved_models" / "maintenance_model.pkl"
    if not model_path.exists():
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InconsistentVersionWarning)
            model = joblib.load(model_path)
            if hasattr(model, "predict_proba"):
                return model
            return None
    except Exception:
        return None


_ML_MODEL = None


def _get_ml_model():
    global _ML_MODEL
    if _ML_MODEL is None:
        _ML_MODEL = _load_ml_model()
    return _ML_MODEL


def _compute_health_score(row):
    """Compute health score (0-100) from sensor data using heuristic formula."""
    temp = row.get("air_temperature", 300)
    process_temp = row.get("process_temperature", 310)
    vibration = row.get("vibration", 0)
    current = row.get("electrical_current", 0)
    pressure = row.get("pressure", 0)
    rotational_speed = row.get("rotational_speed", 1500)
    torque = row.get("torque", 0)

    temp_component = max(0, 100 - abs(temp - 300) * 0.5)
    process_temp_component = max(0, 100 - abs(process_temp - 310) * 0.5)
    vib_component = max(0, 100 - vibration * 15)
    current_component = max(0, 100 - abs(current - 10) * 2)
    pressure_component = max(0, 100 - abs(pressure - 6) * 5)
    speed_component = max(0, 100 - abs(rotational_speed - 1500) * 0.02)
    torque_component = max(0, 100 - torque * 1.5)

    score = (
        temp_component * 0.15
        + process_temp_component * 0.10
        + vib_component * 0.25
        + current_component * 0.15
        + pressure_component * 0.10
        + speed_component * 0.10
        + torque_component * 0.15
    )
    return round(max(0, min(100, score)), 2)


def _compute_failure_probability(row):
    """Compute failure probability using the ML model or heuristic fallback."""
    model = _get_ml_model()
    if model is not None:
        try:
            features = np.array([[row.get(f, 0) for f in MODEL_FEATURES]])
            prob = float(model.predict_proba(features)[0][1])
            return round(prob, 4)
        except Exception:
            pass

    # Heuristic fallback if model unavailable
    score = 0.0
    temp = row.get("air_temperature", 300)
    if temp > 305:
        score += 0.1
    if row.get("vibration", 0) > 2:
        score += 0.2
    if row.get("electrical_current", 0) > 12:
        score += 0.15
    if row.get("tool_wear", 0) > 200:
        score += 0.15
    if row.get("torque", 0) > 50:
        score += 0.1
    failure = row.get("machine_failure", 0)
    if failure == 1:
        score += 0.3
    return round(min(score, 1.0), 4)


def _risk_level_from_probability(prob):
    if prob >= 0.80:
        return "CRITICAL"
    if prob >= 0.60:
        return "HIGH"
    if prob >= 0.35:
        return "MEDIUM"
    return "LOW"


def _compute_rul(row):
    """Compute RUL from existing dataset rul or estimate from health score."""
    existing_rul = row.get("rul")
    if existing_rul is not None and not (isinstance(existing_rul, float) and np.isnan(existing_rul)):
        return float(existing_rul)
    health = _compute_health_score(row)
    return round(health * 0.3, 1)


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

    # Ensure motor_id is present
    if "motor_id" not in df.columns:
        if "product_id" in df.columns:
            df["motor_id"] = df["product_id"].astype(str)
        else:
            df["motor_id"] = [f"M{i:03d}" for i in range(1, len(df) + 1)]
    else:
        df["motor_id"] = df["motor_id"].astype(str)

    # Map rotational_speed if needed
    if "rotation_speed" not in df.columns and "rotational_speed" in df.columns:
        df["rotation_speed"] = df["rotational_speed"]

    # Compute derived health metrics for each row
    health_scores = []
    failure_probs = []
    risk_levels = []
    ruls = []

    for _, row in df.iterrows():
        hs = _compute_health_score(row)
        fp = _compute_failure_probability(row)
        rl = _risk_level_from_probability(fp)
        rul_val = _compute_rul(row)
        health_scores.append(hs)
        failure_probs.append(fp)
        risk_levels.append(rl)
        ruls.append(rul_val)

    df["health_score"] = health_scores
    df["failure_probability"] = failure_probs
    df["risk_level"] = risk_levels
    df["rul"] = ruls

    # Status column
    def _status(rl, mf):
        if mf == 1 or rl == "CRITICAL":
            return "Critical"
        if rl == "HIGH":
            return "Warning"
        if rl == "MEDIUM":
            return "Attention"
        return "Normal"

    df["status"] = df.apply(
        lambda row: _status(
            row["risk_level"],
            row.get("machine_failure", 0),
        ),
        axis=1,
    )

    return df, source
