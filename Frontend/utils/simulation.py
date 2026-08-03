"""
Simulation module - handles sensor data simulation for the predictive maintenance platform.
Extracted from app.py to enable reuse across pages.
"""
import math
import random
from collections import deque
from datetime import datetime, timedelta
from statistics import mean

import streamlit as st


def clamp(value, low, high):
    return max(low, min(value, high))


def safe_mean(values, default=0.0):
    return mean(values) if values else default


def safe_std(values):
    if not values or len(values) < 2:
        return 0.0
    average = mean(values)
    variance = sum((x - average) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def linear_trend(values):
    n = len(values)
    if n < 2:
        return 0.0
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n
    numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
    denominator = sum((xi - x_mean) ** 2 for xi in x)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def simulate_next_record(machine_id, machine_data, thresholds, demo_mode=True):
    """Simulate the next sensor reading for a given machine."""
    state = machine_data[machine_id]["sim_state"]
    now = datetime.now()

    state["temperature"] += random.uniform(-0.2, 0.8) + state["degradation_factor"] * 5
    state["vibration"] += random.uniform(-0.05, 0.15) + state["degradation_factor"] * 2
    state["current"] += random.uniform(-0.15, 0.25) + state["degradation_factor"] * 2
    state["pressure"] += random.uniform(-0.04, 0.02) - state["degradation_factor"] * 0.8
    state["voltage"] += random.uniform(-2.0, 2.0)
    state["rpm"] += random.uniform(-5, 3) - state["degradation_factor"] * 8

    abnormal_prob = 0.03 if demo_mode else 0.002
    if random.random() < abnormal_prob:
        state["temperature"] += random.uniform(12, 22)
        state["vibration"] += random.uniform(1.5, 4.0)
        state["current"] += random.uniform(4, 9)
        state["pressure"] -= random.uniform(0.2, 0.6)

    state["temperature"] = clamp(state["temperature"], 35, 110)
    state["vibration"] = clamp(state["vibration"], 0.2, 12)
    state["current"] = clamp(state["current"], 3, 40)
    state["pressure"] = clamp(state["pressure"], 0.2, 5.0)
    state["voltage"] = clamp(state["voltage"], 300, 420)
    state["rpm"] = clamp(state["rpm"], 800, 1500)

    return {
        "timestamp": now,
        "machine_id": machine_id,
        "temperature": round(state["temperature"], 2),
        "vibration": round(state["vibration"], 3),
        "current": round(state["current"], 2),
        "pressure": round(state["pressure"], 2),
        "voltage": round(state["voltage"], 2),
        "rpm": round(state["rpm"], 2),
    }


def get_recent_records(machine_id, seconds, machine_data):
    """Get records from the last N seconds."""
    records = machine_data[machine_id]["records"]
    if not records:
        return []
    cutoff = records[-1]["timestamp"] - timedelta(seconds=seconds)
    return [record for record in records if record["timestamp"] >= cutoff]

