from pathlib import Path
import sys

from fastapi import APIRouter
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.app.models.ml_model import model
from Backend.app.health_engine import calculate_health_score
from Backend.app.trend_engine import evaluate_trend
from Backend.app.rul_engine import calculate_rul

router = APIRouter()


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
    prediction = model.predict([[
        data.air_temperature,
        data.process_temperature,
        data.rotational_speed,
        data.torque,
        data.tool_wear,
        data.pressure,
        data.vibration,
        data.electrical_current
    ]])

    result = int(prediction[0])

    return {
        "machine_failure": result,
        "status": "FAILURE" if result == 1 else "NORMAL"
    }
