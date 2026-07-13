import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:sqlpresuniv03@localhost:5432/Final_Project"
engine = create_engine(DATABASE_URL)

st.title("Live Sensor Monitoring")

sensor_df = pd.read_sql("SELECT * FROM motor_sensor_data ORDER BY timestamp DESC LIMIT 200", engine)
if not sensor_df.empty:
    sensor_df["timestamp"] = pd.to_datetime(sensor_df["timestamp"])
    st.dataframe(sensor_df[["motor_id", "temperature", "vibration", "electrical_current", "pressure", "rpm", "torque", "timestamp"]], use_container_width=True)
else:
    st.info("No sensor data available yet.")