"""
Shared helper utilities for the Predictive Maintenance dashboard.
Provides session initialization, data loading, and analysis functions.
"""
import random
from copy import deepcopy
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Time windows
SHORT_WINDOW = 15
MEDIUM_WINDOW = 30
LONG_WINDOW = 60
REPORT_INTERVAL_SECONDS = 60
ALERT_COOLDOWN_SECONDS = 20
HISTORY_LIMIT = 60 * 60

BASE_THRESHOLDS = {
    "temperature": {"warning": 75.0, "critical": 90.0},
    "vibration": {"warning": 4.5, "critical": 7.0},
    "current": {"warning": 20.0, "critical": 30.0},
    "pressure": {"warning_low": 1.2, "critical_low": 0.8},
    "voltage": {"warning_low": 360.0, "critical_low": 330.0},
    "rpm": {"warning_low": 1300, "critical_low": 1100},
}

ALL_RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "WARNING"]


@st.cache_data(show_spinner=False)
def get_dataset_machine_ids():
    """Load unique machine IDs from the dataset."""
    data_paths = [
        PROJECT_ROOT / "Dataset" / "Astra_Case_cleaned.csv",
        PROJECT_ROOT / "Dataset" / "Astra_Case.csv",
    ]
    for path in data_paths:
        if path.exists():
            try:
                df = pd.read_csv(path, usecols=["product_id"], dtype={"product_id": str})
                if "product_id" in df.columns and not df["product_id"].dropna().empty:
                    return df["product_id"].dropna().astype(str).unique().tolist()
            except Exception:
                continue
    try:
        from Frontend.utils.db_connection import load_dashboard_data
        db_df, _ = load_dashboard_data()
        if not db_df.empty and "product_id" in db_df.columns:
            return db_df["product_id"].dropna().astype(str).unique().tolist()
    except Exception:
        pass
    return []


def init_session_state(machine_ids):
    """Initialize session state for all machines."""
    if "initialized" in st.session_state:
        return

    st.session_state.initialized = True
    st.session_state.running = False
    st.session_state.auto_refresh = True
    st.session_state.refresh_interval = 1.0
    st.session_state.machine_data = {}
    st.session_state.alert_log = []
    st.session_state.periodic_reports = []
    st.session_state.thresholds = deepcopy(BASE_THRESHOLDS)

    for machine_id in machine_ids:
        st.session_state.machine_data[machine_id] = {
            "records": deque(maxlen=HISTORY_LIMIT),
            "features": deque(maxlen=HISTORY_LIMIT),
            "last_alert_time": None,
            "last_report_time": None,
            "last_report": None,
            "last_realtime_alert": None,
            "sim_state": {
                "temperature": random.uniform(50, 62),
                "vibration": random.uniform(1.2, 2.5),
                "current": random.uniform(10, 16),
                "pressure": random.uniform(1.8, 2.5),
                "voltage": random.uniform(375, 395),
                "rpm": random.uniform(1450, 1490),
                "degradation_factor": random.uniform(0.002, 0.01),
            },
        }


@st.cache_data(show_spinner=False)
def load_cleaned_dataset():
    """Load the Astra_Case dataset."""
    data_path = PROJECT_ROOT / "Dataset" / "Astra_Case_cleaned.csv"
    if not data_path.exists():
        data_path = PROJECT_ROOT / "Dataset" / "Astra_Case.csv"
    df = pd.read_csv(data_path)
    return df, data_path.name

