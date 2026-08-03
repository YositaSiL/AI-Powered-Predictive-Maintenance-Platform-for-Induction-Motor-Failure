from pathlib import Path
import sys

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.app.models.ml_model import model

router = APIRouter()

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


def _build_feature_frame(data: "PredictRequest") -> pd.DataFrame:
    feature_row = {
        "air_temperature": float(data.air_temperature),
        "process_temperature": float(data.process_temperature),
        "rotational_speed": float(data.rotational_speed),
        "torque": float(data.torque),
        "tool_wear": float(data.tool_wear),
        "pressure": float(data.pressure),
        "vibration": float(data.vibration),
        "electrical_current": float(data.electrical_current),
    }
    return pd.DataFrame([feature_row], columns=MODEL_FEATURES)


def _risk_status_from_probability(failure_probability: float):
    # Map probability to operational levels (for better presentation).
    if failure_probability >= 0.85:
        return "FAILURE"
    if failure_probability >= 0.60:
        return "CRITICAL"
    if failure_probability >= 0.35:
        return "WARNING"
    return "NORMAL"


def _health_score_from_probability(failure_probability: float) -> float:
    # 0% failure -> 100 health, 100% failure -> 0 health
    return round((1.0 - failure_probability) * 100.0, 2)



class PredictRequest(BaseModel):
    air_temperature: float
    process_temperature: float
    rotational_speed: int
    torque: float
    tool_wear: int
    pressure: float
    vibration: float
    electrical_current: float


@router.post("/predict")
def predict(data: PredictRequest):
    feature_frame = _build_feature_frame(data)

    # Prefer probability-based scoring for multi-level demo.
    # RandomForestClassifier supports predict_proba.
    failure_probability = float(model.predict_proba(feature_frame)[0][1])

    # Keep binary output too (useful for debugging + compatibility).
    prediction = model.predict(feature_frame)
    result = int(prediction[0])

    status = _risk_status_from_probability(failure_probability)
    health_score = _health_score_from_probability(failure_probability)

    return {
        "machine_failure": result,
        "failure_probability": round(failure_probability, 6),
        "status": status,
        "health_score": health_score,
    }
