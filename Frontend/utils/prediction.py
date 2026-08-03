"""
Prediction module - risk levels, failure probability estimation, recommendations.
Extracted from app.py for reuse across pages.
"""
import requests

from Frontend.utils.simulation import clamp, safe_mean
import streamlit as st


def risk_level(probability):
    if probability >= 0.80:
        return "CRITICAL"
    if probability >= 0.60:
        return "HIGH"
    if probability >= 0.35:
        return "MEDIUM"
    return "LOW"


def degradation_level(score):
    if score >= 75:
        return "SEVERE"
    if score >= 50:
        return "MODERATE"
    if score >= 25:
        return "EARLY"
    return "NORMAL"


def failure_label(probability):
    if probability >= 0.80:
        return "Failure risk imminent"
    if probability >= 0.60:
        return "High failure risk"
    if probability >= 0.35:
        return "Moderate degradation risk"
    return "Stable but keep monitoring"


def maintenance_window(probability):
    if probability >= 0.80:
        return "< 6 hours"
    if probability >= 0.60:
        return "< 24 hours"
    if probability >= 0.35:
        return "1-3 days"
    return "Preventive schedule normal"


def dominant_signals(latest, thresholds):
    """Determine dominant failure signals based on latest feature values."""
    signals = []
    if latest["temperature"] > thresholds["temperature"]["warning"] or latest.get("temp_trend_5m", 0) > 0.02:
        signals.append("temperature_rise")
    if latest["vibration"] > thresholds["vibration"]["warning"] or latest.get("vib_trend_5m", 0) > 0.01:
        signals.append("vibration_degradation")
    if latest["current"] > thresholds["current"]["warning"] or latest.get("current_std_5m", 0) > 2.5:
        signals.append("electrical_current_instability")
    if latest["pressure"] < thresholds["pressure"]["warning_low"]:
        signals.append("pressure_drop")
    if latest["voltage"] < thresholds["voltage"]["warning_low"]:
        signals.append("voltage_issue")
    if latest["rpm"] < thresholds["rpm"]["warning_low"]:
        signals.append("speed_drop")
    if not signals:
        signals.append("no_major_anomaly_detected")
    return signals


def recommendation(latest, failure_probability, deg_level, signals):
    """Generate maintenance recommendations based on signals and risk."""
    rec = []
    if "temperature_rise" in signals:
        rec.append("Check cooling / airflow / overload.")
    if "vibration_degradation" in signals:
        rec.append("Inspect bearing, shaft alignment, looseness, and rotor balance.")
    if "electrical_current_instability" in signals:
        rec.append("Inspect phase current, load imbalance, power supply, and winding insulation.")
    if "pressure_drop" in signals:
        rec.append("Inspect pressure and lubrication systems.")
    if "voltage_issue" in signals:
        rec.append("Evaluate supply voltage stability and panel condition.")
    if "speed_drop" in signals:
        rec.append("Inspect slip, coupling, mechanical load, and rotor condition.")

    if failure_probability >= 0.80:
        rec.append("Prioritize planned shutdown or emergency inspection.")
    elif failure_probability >= 0.60:
        rec.append("Schedule maintenance within 24 hours.")
    elif failure_probability >= 0.35:
        rec.append("Increase monitoring and prepare preventive maintenance.")
    else:
        rec.append("Continue routine monitoring.")

    if deg_level in ("MODERATE", "SEVERE", "EMERGENCY"):
        rec.append("Compare with 7-30 day history to validate degradation patterns.")
    return rec


def estimate_realtime_failure_probability(latest):
    """Estimate real-time failure probability from latest sensor features."""
    score = 0.0
    score += clamp((latest["temperature"] - 70) / 25, 0, 1) * 0.22
    score += clamp(latest.get("temp_trend_5m", 0) * 40, 0, 1) * 0.08
    score += clamp((latest["vibration"] - 4.0) / 4.0, 0, 1) * 0.22
    score += clamp(latest.get("vib_trend_5m", 0) * 60, 0, 1) * 0.08
    score += clamp((latest["current"] - 18) / 12, 0, 1) * 0.15
    score += clamp((latest.get("current_std_5m", 0) - 2.0) / 4.0, 0, 1) * 0.07
    score += clamp((1.2 - latest["pressure"]) / 1.2, 0, 1) * 0.08
    score += clamp((360 - latest["voltage"]) / 40, 0, 1) * 0.05
    score += clamp((1300 - latest["rpm"]) / 250, 0, 1) * 0.05
    score += (latest.get("anomaly_score", 0) / 100.0) * 0.10
    score += (latest.get("degradation_score", 0) / 100.0) * 0.10
    return clamp(score, 0.0, 1.0)


def _risk_status_from_probability(failure_probability: float):
    if failure_probability >= 0.85:
        return "FAILURE"
    if failure_probability >= 0.60:
        return "CRITICAL"
    if failure_probability >= 0.35:
        return "WARNING"
    return "NORMAL"


def _heuristic_failure_probability(payload):
    temperature = float(payload.get("air_temperature", 70.0))
    process_temperature = float(payload.get("process_temperature", 70.0))
    vibration = float(payload.get("vibration", 0.0))
    current = float(payload.get("electrical_current", 0.0))
    pressure = float(payload.get("pressure", 0.0))
    rotational_speed = float(payload.get("rotational_speed", 1500.0))
    torque = float(payload.get("torque", 0.0))
    tool_wear = float(payload.get("tool_wear", 0.0))

    score = 0.0
    if temperature > 305:
        score += 0.10
    if process_temperature > 310:
        score += 0.08
    if vibration > 2.0:
        score += 0.20
    if current > 12.0:
        score += 0.15
    if pressure < 2.5:
        score += 0.10
    if rotational_speed < 1400:
        score += 0.08
    if torque > 45.0:
        score += 0.10
    if tool_wear > 200:
        score += 0.15
    return clamp(score, 0.0, 1.0)


def predict_with_fallback(payload, backend_url="http://127.0.0.1:8000/predict", timeout=8):
    """Call the backend prediction API and fall back to a heuristic model when unavailable."""
    try:
        response = requests.post(backend_url, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        machine_failure = int(result.get("machine_failure", 0))
        status = str(result.get("status", "NORMAL"))
        failure_probability = float(result.get("failure_probability", 0.0))
        health_score = float(result.get("health_score", (1.0 - failure_probability) * 100.0))
        if not 0.0 <= failure_probability <= 1.0:
            raise ValueError("Invalid failure probability")
        if not 0.0 <= health_score <= 100.0:
            health_score = max(0.0, min(100.0, health_score))
        return {
            "machine_failure": machine_failure,
            "failure_probability": round(failure_probability, 6),
            "status": status,
            "health_score": round(health_score, 2),
            "used_fallback": False,
        }
    except Exception:
        failure_probability = _heuristic_failure_probability(payload)
        machine_failure = 1 if failure_probability >= 0.50 else 0
        health_score = round((1.0 - failure_probability) * 100.0, 2)
        return {
            "machine_failure": machine_failure,
            "failure_probability": round(failure_probability, 6),
            "status": _risk_status_from_probability(failure_probability),
            "health_score": round(health_score, 2),
            "used_fallback": True,
        }

