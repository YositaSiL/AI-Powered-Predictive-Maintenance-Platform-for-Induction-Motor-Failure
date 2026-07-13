import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Frontend.utils.db_connection import load_dashboard_data

st.title("Motor Detail Page")

df, source = load_dashboard_data()

if df.empty:
    st.warning("No motor data is available yet.")
    st.stop()

motor_ids = [str(x) for x in df["motor_id"].astype(str).dropna().unique().tolist()]
selected_motor = st.selectbox("Select Motor", motor_ids, index=0)

latest = None
history = []

if st.button("Load Motor"):
    try:
        numeric_motor_id = int(str(selected_motor).split("-")[-1]) if str(selected_motor).replace(".", "", 1).isdigit() else None
    except ValueError:
        numeric_motor_id = None

    if numeric_motor_id is not None:
        try:
            response = requests.get(f"http://127.0.0.1:8000/motors/{numeric_motor_id}/latest", timeout=5)
            response.raise_for_status()
            data = response.json()
            latest = data.get("latest")
            history = data.get("history", [])
        except Exception:
            latest = None
            history = []

    if latest is None:
        row = df[df["motor_id"].astype(str) == str(selected_motor)].iloc[0]
        latest = {
            "temperature": row.get("air_temperature", 0),
            "vibration": row.get("vibration", 0),
            "electrical_current": row.get("electrical_current", 0),
            "rpm": row.get("rotation_speed", 0),
            "pressure": row.get("pressure", 0),
        }
        history = []

    if latest:
        st.caption(f"Data source: {source}")
        st.subheader(f"Motor {selected_motor} Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Temperature", f"{latest.get('temperature', 0):.2f}°C")
        col2.metric("Vibration", f"{latest.get('vibration', 0):.2f}")
        col3.metric("Current", f"{latest.get('electrical_current', 0):.2f} A")
        col4.metric("RPM", f"{latest.get('rpm', 0):.0f}")

        if history:
            latest_history = history[0]
            st.metric("Health Score", f"{latest_history.get('health_score', 0):.1f}")
            st.metric("Failure Probability", f"{latest_history.get('failure_probability', 0):.2f}")
            st.metric("RUL", f"{latest_history.get('rul', 0):.1f}")
            st.metric("Trend", latest_history.get("trend", "NORMAL"))
            st.info(latest_history.get("recommendation", "No recommendation"))

            st.subheader("Historical Trend")
            history_df = pd.DataFrame(history)
            history_df["timestamp"] = pd.to_datetime(history_df["timestamp"], errors="coerce")
            if not history_df.empty:
                st.line_chart(history_df.set_index("timestamp")["health_score"])
        else:
            st.info("No historical analysis is available yet. The page is currently using the local dataset fallback.")
    else:
        st.warning("No sensor data is available for this motor yet.")