"""
Feature engineering module - computes features, anomaly scores, degradation scores.
Extracted from app.py for reuse across pages.
"""
from datetime import timedelta

import streamlit as st

from Frontend.utils.simulation import clamp, safe_mean, safe_std, linear_trend, get_recent_records


def compute_features(machine_id, current_record, machine_data, thresholds, short_window, medium_window):
    """Compute engineered features from recent sensor history."""
    recent_1m = get_recent_records(machine_id, short_window, machine_data)
    recent_5m = get_recent_records(machine_id, medium_window, machine_data)

    temp_1m = [record["temperature"] for record in recent_1m]
    temp_5m = [record["temperature"] for record in recent_5m]
    vib_1m = [record["vibration"] for record in recent_1m]
    vib_5m = [record["vibration"] for record in recent_5m]
    cur_1m = [record["current"] for record in recent_1m]
    cur_5m = [record["current"] for record in recent_5m]
    prs_5m = [record["pressure"] for record in recent_5m]
    volt_5m = [record["voltage"] for record in recent_5m]
    rpm_5m = [record["rpm"] for record in recent_5m]

    feature = {
        "timestamp": current_record["timestamp"],
        "machine_id": machine_id,
        "temperature": current_record["temperature"],
        "vibration": current_record["vibration"],
        "current": current_record["current"],
        "pressure": current_record["pressure"],
        "voltage": current_record["voltage"],
        "rpm": current_record["rpm"],
        "temp_avg_1m": safe_mean(temp_1m, current_record["temperature"]),
        "temp_avg_5m": safe_mean(temp_5m, current_record["temperature"]),
        "temp_trend_5m": linear_trend(temp_5m),
        "vib_avg_1m": safe_mean(vib_1m, current_record["vibration"]),
        "vib_avg_5m": safe_mean(vib_5m, current_record["vibration"]),
        "vib_trend_5m": linear_trend(vib_5m),
        "current_avg_1m": safe_mean(cur_1m, current_record["current"]),
        "current_avg_5m": safe_mean(cur_5m, current_record["current"]),
        "current_std_5m": safe_std(cur_5m),
        "pressure_avg_5m": safe_mean(prs_5m, current_record["pressure"]),
        "voltage_avg_5m": safe_mean(volt_5m, current_record["voltage"]),
        "rpm_avg_5m": safe_mean(rpm_5m, current_record["rpm"]),
    }
    feature["anomaly_score"] = compute_anomaly_score(feature, thresholds)
    feature["degradation_score"] = compute_degradation_score(feature, thresholds)
    return feature


def compute_anomaly_score(feature, thresholds):
    """Compute anomaly score based on threshold violations."""
    score = 0.0
    if feature["temperature"] > thresholds["temperature"]["warning"]:
        score += min((feature["temperature"] - thresholds["temperature"]["warning"]) * 1.2, 20)
    if feature["vibration"] > thresholds["vibration"]["warning"]:
        score += min((feature["vibration"] - thresholds["vibration"]["warning"]) * 6.0, 25)
    if feature["current"] > thresholds["current"]["warning"]:
        score += min((feature["current"] - thresholds["current"]["warning"]) * 2.0, 15)
    if feature["pressure"] < thresholds["pressure"]["warning_low"]:
        score += min((thresholds["pressure"]["warning_low"] - feature["pressure"]) * 12.0, 15)
    if feature["voltage"] < thresholds["voltage"]["warning_low"]:
        score += min((thresholds["voltage"]["warning_low"] - feature["voltage"]) * 0.1, 10)
    if feature["rpm"] < thresholds["rpm"]["warning_low"]:
        score += min((thresholds["rpm"]["warning_low"] - feature["rpm"]) * 0.03, 10)
    if feature.get("temp_trend_5m", 0) > 0.01:
        score += min(feature["temp_trend_5m"] * 50, 10)
    if feature.get("vib_trend_5m", 0) > 0.005:
        score += min(feature["vib_trend_5m"] * 100, 10)
    if feature.get("current_std_5m", 0) > 2.0:
        score += min((feature["current_std_5m"] - 2.0) * 2.5, 10)
    return clamp(score, 0, 100)


def compute_degradation_score(feature, thresholds):
    """Compute degradation score from long-term feature averages."""
    score = 0.0
    score += clamp((feature.get("temp_avg_5m", feature["temperature"]) - 55) * 1.0, 0, 20)
    score += clamp(feature.get("temp_trend_5m", 0) * 100, 0, 10)
    score += clamp((feature.get("vib_avg_5m", feature["vibration"]) - 2.5) * 5.0, 0, 25)
    score += clamp(feature.get("vib_trend_5m", 0) * 150, 0, 15)
    score += clamp((feature.get("current_avg_5m", feature["current"]) - 14) * 1.2, 0, 10)
    score += clamp((feature.get("current_std_5m", 0) - 1.0) * 4.0, 0, 10)
    if feature.get("pressure_avg_5m", feature["pressure"]) < 1.4:
        score += clamp((1.4 - feature["pressure_avg_5m"]) * 10, 0, 10)
    if feature.get("voltage_avg_5m", feature["voltage"]) < 370:
        score += clamp((370 - feature["voltage_avg_5m"]) * 0.15, 0, 5)
    if feature.get("rpm_avg_5m", feature["rpm"]) < 1400:
        score += clamp((1400 - feature["rpm_avg_5m"]) * 0.02, 0, 5)
    score += feature.get("anomaly_score", 0) * 0.2
    return clamp(score, 0, 100)

