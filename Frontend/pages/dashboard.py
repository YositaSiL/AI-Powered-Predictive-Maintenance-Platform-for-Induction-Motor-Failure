import streamlit as st
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:sqlpresuniv03@localhost:5432/Final_Project"
engine = create_engine(DATABASE_URL)

st.title("Astra Otoparts Executive Dashboard")

sensor_df = pd.read_sql("SELECT * FROM motor_sensor_data ORDER BY timestamp DESC LIMIT 400", engine)
analysis_df = pd.read_sql("SELECT * FROM motor_analysis_history ORDER BY timestamp DESC LIMIT 200", engine)
alerts_df = pd.read_sql("SELECT * FROM alerts ORDER BY generated_at DESC LIMIT 100", engine)

if not sensor_df.empty:
    sensor_df["timestamp"] = pd.to_datetime(sensor_df["timestamp"])
    sensor_df = sensor_df.sort_values("timestamp")

if not analysis_df.empty:
    analysis_df["timestamp"] = pd.to_datetime(analysis_df["timestamp"])
    analysis_df = analysis_df.sort_values("timestamp")

if not alerts_df.empty:
    alerts_df["generated_at"] = pd.to_datetime(alerts_df["generated_at"])

summary = {
    "total_motors": sensor_df["motor_id"].nunique() if not sensor_df.empty else 20,
    "avg_health_score": round(analysis_df["health_score"].mean(), 2) if not analysis_df.empty else 0,
    "avg_failure_probability": round(analysis_df["failure_probability"].mean() * 100, 2) if not analysis_df.empty else 0,
    "avg_rul": round(analysis_df["rul"].mean(), 2) if not analysis_df.empty else 0,
    "critical_alerts": int(alerts_df[alerts_df["severity"] == "CRITICAL"].shape[0]) if not alerts_df.empty else 0,
}

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Motors", summary["total_motors"])
col2.metric("Avg Health Score", f"{summary['avg_health_score']:.1f}")
col3.metric("Avg Failure Probability", f"{summary['avg_failure_probability']:.1f}%")
col4.metric("Avg RUL", f"{summary['avg_rul']:.1f} days")
col5.metric("Critical Alerts", summary["critical_alerts"])

st.markdown("---")

left, right = st.columns(2)
with left:
    st.subheader("Health Score Trend")
    if not analysis_df.empty:
        fig = px.line(analysis_df, x="timestamp", y="health_score", markers=True, title="Health Score Over Time")
        st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Failure Probability Trend")
    if not analysis_df.empty:
        fig = px.line(analysis_df, x="timestamp", y="failure_probability", markers=True, title="Failure Probability Trend")
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Latest Recommendations")
if not analysis_df.empty:
    st.dataframe(analysis_df[["motor_id", "health_score", "failure_probability", "rul", "trend", "recommendation"]].head(20), use_container_width=True)

st.subheader("Active Alerts")
if not alerts_df.empty:
    st.dataframe(alerts_df[["motor_id", "alert_type", "severity", "message", "generated_at"]], use_container_width=True)
else:
    st.info("No alerts generated yet.")