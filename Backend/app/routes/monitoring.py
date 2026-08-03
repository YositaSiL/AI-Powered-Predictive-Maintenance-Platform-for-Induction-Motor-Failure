from pathlib import Path
import sys
import random
import threading
import time
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.app.database import get_db
from Backend.app.models.monitoring import MotorSensorData, Alert, MotorAnalysisHistory
from Backend.app.health_engine import calculate_health_score
from Backend.app.rul_engine import calculate_rul
from Backend.app.trend_engine import evaluate_trend
from Backend.app.models.ml_model import model

router = APIRouter()

MOTOR_COUNT = 20
_MONITORING_THREAD = None
_MONITORING_THREAD_LOCK = threading.Lock()
_MONITORING_STOP_EVENT = threading.Event()


def is_monitoring_loop_running() -> bool:
    with _MONITORING_THREAD_LOCK:
        return _MONITORING_THREAD is not None and _MONITORING_THREAD.is_alive()


def start_monitoring_loop():
    global _MONITORING_THREAD
    with _MONITORING_THREAD_LOCK:
        if _MONITORING_THREAD is not None and _MONITORING_THREAD.is_alive():
            return {"status": "already_running", "motors": MOTOR_COUNT}
        _MONITORING_STOP_EVENT.clear()
        _MONITORING_THREAD = threading.Thread(target=_sensor_loop, daemon=True, name="monitoring-sim-loop")
        _MONITORING_THREAD.start()
        return {"status": "started", "motors": MOTOR_COUNT}


def stop_monitoring_loop():
    _MONITORING_STOP_EVENT.set()
    with _MONITORING_THREAD_LOCK:
        thread = _MONITORING_THREAD
        _MONITORING_THREAD = None
    if thread is not None:
        thread.join(timeout=2)
    return {"status": "stopped"}


def _build_sensor_payload(motor_id, base_time=None):
    base = 70 + (motor_id % 7) * 3
    volatility = (motor_id % 5) * 0.02
    return {
        "motor_id": motor_id,
        "temperature": round(base + random.uniform(0, 8) + volatility * 10, 2),
        "vibration": round(0.08 + random.uniform(0, 0.12) + volatility, 2),
        "electrical_current": round(20 + random.uniform(0, 6) + motor_id % 3, 2),
        "pressure": round(8.2 + random.uniform(0, 1.2), 2),
        "rpm": round(1450 + random.uniform(-80, 120) + motor_id % 4 * 20, 2),
        "torque": round(45 + random.uniform(0, 10) + motor_id % 3 * 2, 2),
        "timestamp": base_time or datetime.utcnow(),
    }


def _insert_sensor_reading(db: Session, payload: dict):
    record = MotorSensorData(**payload)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _generate_alerts(db: Session, motor_id: int, health_score: float, failure_probability: float):
    if health_score < 40:
        alert = Alert(
            motor_id=motor_id,
            alert_type="HEALTH",
            severity="CRITICAL",
            message="Health score dropped below safe threshold.",
            source="health_engine",
        )
        db.add(alert)
    if failure_probability > 0.8:
        alert = Alert(
            motor_id=motor_id,
            alert_type="FAILURE",
            severity="CRITICAL",
            message="Failure probability exceeded 80%.",
            source="failure_model",
        )
        db.add(alert)
    if db.new:
        db.commit()


def _analyze_motor(db: Session, motor_id: int):
    recent_records = (
        db.query(MotorSensorData)
        .filter(MotorSensorData.motor_id == motor_id)
        .order_by(MotorSensorData.timestamp.desc())
        .limit(30)
        .all()
    )
    recent_records = list(reversed(recent_records))

    if not recent_records:
        return

    latest = recent_records[-1]
    health_score = calculate_health_score(
        latest.temperature,
        latest.vibration,
        latest.electrical_current,
        latest.pressure,
        latest.rpm,
    )

    failure_probability = float(
    model.predict_proba([[
        latest.temperature,
        latest.temperature + 5,
        latest.rpm,
        latest.torque,
        20,
        latest.pressure,
        latest.vibration,
        latest.electrical_current,
    ]])[0][1]
)

    trend = evaluate_trend([
        {
            "temperature": item.temperature,
            "vibration": item.vibration,
            "electrical_current": item.electrical_current,
        }
        for item in recent_records
    ])

    recommendation = "Schedule inspection and lubrication" if health_score < 60 else "Continue routine monitoring"
    if trend["overall"] == "CRITICAL":
        recommendation = "Immediate maintenance intervention required"
    if failure_probability > 0.8:
        recommendation = "Shutdown and replace critical components"

    rul = calculate_rul(health_score, failure_probability, trend["overall"])

    history_record = MotorAnalysisHistory(
        motor_id=motor_id,
        health_score=health_score,
        failure_probability=failure_probability,
        rul=rul,
        trend=trend["overall"],
        recommendation=recommendation,
    )
    db.add(history_record)
    _generate_alerts(db, motor_id, health_score, failure_probability)
    db.commit()


def _sensor_loop():
    while not _MONITORING_STOP_EVENT.is_set():
        try:
            db = next(get_db())
            for motor_id in range(1, MOTOR_COUNT + 1):
                payload = _build_sensor_payload(motor_id)
                _insert_sensor_reading(db, payload)
                _analyze_motor(db, motor_id)
            time.sleep(1)
        except Exception:
            time.sleep(2)


@router.post("/monitoring/simulate")
def simulate_monitoring():
    return start_monitoring_loop()


@router.get("/dashboard-summary")
def dashboard_summary(db: Session = Depends(get_db)):
    total_motors = db.query(MotorSensorData.motor_id).distinct().count()
    latest_history = db.query(MotorAnalysisHistory).order_by(MotorAnalysisHistory.timestamp.desc()).all()
    if not latest_history:
        return {
            "total_motors": total_motors,
            "avg_health_score": 0,
            "avg_failure_probability": 0,
            "avg_rul": 0,
            "critical_alerts": 0,
        }

    health_scores = [item.health_score for item in latest_history]
    failure_probabilities = [item.failure_probability for item in latest_history]
    ruls = [item.rul for item in latest_history]
    critical_alerts = db.query(Alert).filter(Alert.severity == "CRITICAL").count()

    return {
        "total_motors": total_motors,
        "avg_health_score": round(sum(health_scores) / len(health_scores), 2),
        "avg_failure_probability": round(sum(failure_probabilities) / len(failure_probabilities), 2),
        "avg_rul": round(sum(ruls) / len(ruls), 2),
        "critical_alerts": critical_alerts,
    }


@router.get("/motors/{motor_id}/latest")
def latest_motor_data(motor_id: int, db: Session = Depends(get_db)):
    latest = (
        db.query(MotorSensorData)
        .filter(MotorSensorData.motor_id == motor_id)
        .order_by(MotorSensorData.timestamp.desc())
        .first()
    )
    history = (
        db.query(MotorAnalysisHistory)
        .filter(MotorAnalysisHistory.motor_id == motor_id)
        .order_by(MotorAnalysisHistory.timestamp.desc())
        .limit(10)
        .all()
    )
    return {
        "motor_id": motor_id,
        "latest": latest.__dict__ if latest else None,
        "history": [
            {
                "timestamp": item.timestamp.isoformat(),
                "health_score": item.health_score,
                "failure_probability": item.failure_probability,
                "rul": item.rul,
                "trend": item.trend,
                "recommendation": item.recommendation,
            }
            for item in history
        ],
    }
