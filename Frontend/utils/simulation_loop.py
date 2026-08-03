"""
Simulation Loop Module - Contains the core simulation cycle logic for the dashboard.
Extracted from app.py to enable reuse across pages without circular imports.
"""
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from Frontend.utils.simulation import (
    clamp, safe_mean, linear_trend, simulate_next_record,
    get_recent_records
)
from Frontend.utils.feature_engineering import (
    compute_features
)
from Frontend.utils.prediction import (
    risk_level, degradation_level, failure_label, maintenance_window,
    dominant_signals, recommendation, estimate_realtime_failure_probability
)
from Frontend.utils.helper import (
    SHORT_WINDOW, MEDIUM_WINDOW, LONG_WINDOW, REPORT_INTERVAL_SECONDS,
    ALERT_COOLDOWN_SECONDS, get_dataset_machine_ids, init_session_state
)


def analyze_periodic(machine_id):
    """Periodic analysis producing health summary, failure estimation, action plan."""
    features = list(st.session_state.machine_data[machine_id]["features"])
    if len(features) < 10:
        return None

    latest_time = features[-1]["timestamp"]
    cutoff = latest_time - timedelta(seconds=LONG_WINDOW)
    features = [feature for feature in features if feature["timestamp"] >= cutoff]
    if len(features) < 10:
        return None

    latest = features[-1]
    avg_temp = safe_mean([feature["temperature"] for feature in features], latest["temperature"])
    avg_vib = safe_mean([feature["vibration"] for feature in features], latest["vibration"])
    avg_current = safe_mean([feature["current"] for feature in features], latest["current"])
    avg_pressure = safe_mean([feature["pressure"] for feature in features], latest["pressure"])
    avg_anomaly = safe_mean([feature["anomaly_score"] for feature in features], latest["anomaly_score"])
    avg_deg = safe_mean([feature["degradation_score"] for feature in features], latest["degradation_score"])

    temp_trend = linear_trend([feature["temperature"] for feature in features])
    vib_trend = linear_trend([feature["vibration"] for feature in features])
    current_trend = linear_trend([feature["current"] for feature in features])

    failure_score = (
        0.25 * (avg_anomaly / 100.0)
        + 0.30 * (avg_deg / 100.0)
        + 0.15 * clamp((avg_temp - 65) / 30, 0, 1)
        + 0.15 * clamp((avg_vib - 3.0) / 5, 0, 1)
        + 0.10 * clamp((avg_current - 16) / 15, 0, 1)
        + 0.05 * clamp((1.5 - avg_pressure) / 1.5, 0, 1)
    )
    failure_score += clamp(temp_trend * 2.0, 0, 0.08)
    failure_score += clamp(vib_trend * 3.0, 0, 0.10)
    failure_score += clamp(current_trend * 1.5, 0, 0.05)

    probability = clamp(failure_score, 0.0, 1.0)
    health = clamp(100 - (probability * 65 + avg_deg * 0.35), 0, 100)
    level = risk_level(probability)
    deg_level = degradation_level(avg_deg)
    signals = dominant_signals(latest, st.session_state.thresholds)
    rec = recommendation(latest, probability, deg_level, signals)

    return {
        "machine_id": machine_id,
        "analysis_time": datetime.now(),
        "health_score": round(health, 2),
        "failure_probability": round(probability, 4),
        "risk_level": level,
        "degradation_level": deg_level,
        "dominant_signals": signals,
        "recommendation": rec,
        "output_1_health_summary": {
            "machine_id": machine_id,
            "health_score": round(health, 2),
            "risk_level": level,
            "degradation_level": deg_level,
            "dominant_signals": signals,
        },
        "output_2_failure_estimation": {
            "machine_id": machine_id,
            "failure_probability": round(probability, 4),
            "estimated_status": failure_label(probability),
            "avg_anomaly_score": round(avg_anomaly, 2),
            "avg_degradation_score": round(avg_deg, 2),
            "trend": {
                "temperature_trend": round(temp_trend, 4),
                "vibration_trend": round(vib_trend, 4),
                "current_trend": round(current_trend, 4),
            },
        },
        "output_3_action_plan": {
            "machine_id": machine_id,
            "recommendation": rec,
            "priority": level,
            "maintenance_window": maintenance_window(probability),
        },
    }


def check_realtime_alert(machine_id, latest_feature):
    """Check if real-time alert should be triggered."""
    reasons = []
    fp = estimate_realtime_failure_probability(latest_feature)

    if latest_feature["temperature"] >= st.session_state.thresholds["temperature"]["critical"]:
        reasons.append(f"Critical temperature ({latest_feature['temperature']})")
    if latest_feature["vibration"] >= st.session_state.thresholds["vibration"]["critical"]:
        reasons.append(f"Critical vibration ({latest_feature['vibration']})")
    if latest_feature["current"] >= st.session_state.thresholds["current"]["critical"]:
        reasons.append(f"Critical current ({latest_feature['current']})")
    if latest_feature["pressure"] <= st.session_state.thresholds["pressure"]["critical_low"]:
        reasons.append(f"Critical low pressure ({latest_feature['pressure']})")
    if latest_feature["voltage"] <= st.session_state.thresholds["voltage"]["critical_low"]:
        reasons.append(f"Critical low voltage ({latest_feature['voltage']})")
    if latest_feature["rpm"] <= st.session_state.thresholds["rpm"]["critical_low"]:
        reasons.append(f"Critical low RPM ({latest_feature['rpm']})")
    if fp >= 0.80:
        reasons.append(f"Realtime failure probability critical ({fp:.2%})")

    if not reasons:
        return None

    level = "CRITICAL" if fp >= 0.80 or len(reasons) >= 2 else "WARNING"
    signals = dominant_signals(latest_feature, st.session_state.thresholds)
    rec = recommendation(latest_feature, fp, "EMERGENCY", signals)

    return {
        "machine_id": machine_id,
        "alert_time": latest_feature["timestamp"],
        "alert_level": level,
        "failure_probability": round(fp, 4),
        "trigger_reasons": reasons,
        "conclusion": f"Immediate alert for {machine_id} | failure_probability={fp:.2%} | status={level}",
        "immediate_actions": rec,
        "sensor_snapshot": {
            "temperature": latest_feature["temperature"],
            "vibration": latest_feature["vibration"],
            "current": latest_feature["current"],
            "pressure": latest_feature["pressure"],
            "voltage": latest_feature["voltage"],
            "rpm": latest_feature["rpm"],
            "anomaly_score": latest_feature["anomaly_score"],
            "degradation_score": latest_feature["degradation_score"],
        },
    }


def update_one_cycle():
    """Generate one simulation cycle for all machines."""
    machine_ids = get_dataset_machine_ids() or []
    if not machine_ids:
        return

    for machine_id in machine_ids:
        if machine_id not in st.session_state.machine_data:
            continue
        record = simulate_next_record(
            machine_id, st.session_state.machine_data,
            st.session_state.thresholds
        )
        st.session_state.machine_data[machine_id]["records"].append(record)
        feature = compute_features(
            machine_id, record, st.session_state.machine_data,
            st.session_state.thresholds, SHORT_WINDOW, MEDIUM_WINDOW
        )
        st.session_state.machine_data[machine_id]["features"].append(feature)

        alert = check_realtime_alert(machine_id, feature)
        if alert is not None:
            last_alert_time = st.session_state.machine_data[machine_id]["last_alert_time"]
            now = feature["timestamp"]
            allow_alert = False
            if last_alert_time is None:
                allow_alert = True
            else:
                elapsed = (now - last_alert_time).total_seconds()
                if elapsed >= ALERT_COOLDOWN_SECONDS:
                    allow_alert = True
            if allow_alert:
                st.session_state.machine_data[machine_id]["last_alert_time"] = now
                st.session_state.machine_data[machine_id]["last_realtime_alert"] = alert
                st.session_state.alert_log.insert(0, alert)

        records = st.session_state.machine_data[machine_id]["records"]
        last_report_time = st.session_state.machine_data[machine_id]["last_report_time"]
        if len(records) >= 1:
            if (last_report_time is None) or (
                (records[-1]["timestamp"] - last_report_time).total_seconds() >= REPORT_INTERVAL_SECONDS
            ):
                report = analyze_periodic(machine_id)
                if report:
                    st.session_state.machine_data[machine_id]["last_report"] = report
                    st.session_state.machine_data[machine_id]["last_report_time"] = records[-1]["timestamp"]
                    st.session_state.periodic_reports.insert(0, report)


def latest_record(machine_id):
    records = st.session_state.machine_data[machine_id]["records"]
    return records[-1] if records else None


def latest_feature(machine_id):
    features = st.session_state.machine_data[machine_id]["features"]
    return features[-1] if features else None


def latest_report(machine_id):
    return st.session_state.machine_data[machine_id]["last_report"]


def latest_alert(machine_id):
    return st.session_state.machine_data[machine_id]["last_realtime_alert"]


def make_machine_summary_df(machine_ids):
    rows = []
    for machine_id in machine_ids:
        record = latest_record(machine_id)
        feature = latest_feature(machine_id)
        report = latest_report(machine_id)
        if record is None or feature is None:
            continue
        realtime_fp = estimate_realtime_failure_probability(feature)
        rows.append({
            "Machine": machine_id,
            "Temperature": record["temperature"],
            "Vibration": record["vibration"],
            "Current": record["current"],
            "Pressure": record["pressure"],
            "Voltage": record["voltage"],
            "RPM": record["rpm"],
            "Anomaly Score": round(feature["anomaly_score"], 2),
            "Degradation Score": round(feature["degradation_score"], 2),
            "Realtime Failure Prob (%)": round(realtime_fp * 100, 2),
            "Periodic Risk": report["risk_level"] if report else "N/A",
            "Health Score": report["health_score"] if report else None,
        })
    return pd.DataFrame(rows)


def get_machine_history_df(machine_id):
    records = list(st.session_state.machine_data[machine_id]["records"])
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)

