import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.app.routes.prediction import PredictRequest, _build_feature_frame
from Frontend.utils.prediction import predict_with_fallback


def test_build_feature_frame_uses_expected_model_columns():
    payload = PredictRequest(
        air_temperature=65.0,
        process_temperature=75.0,
        rotational_speed=1500,
        torque=22.0,
        tool_wear=180,
        pressure=2.1,
        vibration=3.2,
        electrical_current=16.0,
    )

    frame = _build_feature_frame(payload)

    assert list(frame.columns) == [
        "air_temperature",
        "process_temperature",
        "rotational_speed",
        "torque",
        "tool_wear",
        "pressure",
        "vibration",
        "electrical_current",
    ]
    assert frame.iloc[0].to_dict()["air_temperature"] == pytest.approx(65.0)


def test_predict_with_fallback_returns_valid_result_when_backend_is_unavailable(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise ConnectionError("offline")

    monkeypatch.setattr("Frontend.utils.prediction.requests.post", raise_connection_error)

    payload = {
        "air_temperature": 65.0,
        "process_temperature": 75.0,
        "rotational_speed": 1500,
        "torque": 22.0,
        "tool_wear": 180,
        "pressure": 2.1,
        "vibration": 3.2,
        "electrical_current": 16.0,
    }

    result = predict_with_fallback(payload, backend_url="http://127.0.0.1:1/predict")

    assert result["machine_failure"] in {0, 1}
    assert result["status"] in {"NORMAL", "WARNING", "CRITICAL", "FAILURE"}
    assert 0.0 <= result["failure_probability"] <= 1.0
    assert 0.0 <= result["health_score"] <= 100.0
