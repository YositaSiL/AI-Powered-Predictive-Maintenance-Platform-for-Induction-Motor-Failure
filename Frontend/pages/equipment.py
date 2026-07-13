import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Frontend.utils.db_connection import load_dashboard_data

st.title("Equipment Monitoring")

df, source = load_dashboard_data()

if df.empty:
    st.info("No equipment data is available yet.")
    st.stop()

st.caption(f"Data source: {source}")

visible_columns = [
    col for col in [
        "motor_id",
        "type",
        "air_temperature",
        "process_temperature",
        "rotation_speed",
        "torque",
        "tool_wear",
        "vibration",
        "electrical_current",
        "pressure",
        "rul",
        "health_score",
        "failure_probability",
        "risk_level",
        "status",
    ]
    if col in df.columns
]

st.dataframe(df[visible_columns], use_container_width=True)
st.info(f"Total Records: {len(df)}")