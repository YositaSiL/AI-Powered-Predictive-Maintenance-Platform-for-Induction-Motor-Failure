"""
Machine Prediction Page - AI-powered failure prediction and health assessment.
"""
import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Frontend.utils.charts import gauge_chart
from Frontend.utils.prediction import predict_with_fallback

st.set_page_config(page_title="Machine Prediction - Predictive Maintenance", layout="wide")

css_path = PROJECT_ROOT / "Frontend" / "styles" / "streamlit.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="sidebar-logo-text">Astra Otoparts</div>
            <div class="sidebar-logo-sub">Predictive Maintenance Platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-section-title">Navigation</div>', unsafe_allow_html=True)
    st.page_link("app.py", label="Dashboard", use_container_width=True)
    st.page_link("pages/1_Sensor_Monitoring.py", label="Sensor Monitoring", use_container_width=True)
    st.page_link("pages/2_Machine_Prediction.py", label="Machine Prediction", use_container_width=True)
    st.page_link("pages/3_Machines.py", label="Machines", use_container_width=True)
    st.page_link("pages/4_Alerts.py", label="Alerts", use_container_width=True)
    st.page_link("pages/5_Maintenance.py", label="Maintenance", use_container_width=True)
    st.page_link("pages/6_Reports.py", label="Reports", use_container_width=True)
    st.page_link("pages/7_Settings.py", label="Settings", use_container_width=True)
    st.page_link("pages/8_About.py", label="About", use_container_width=True)
    st.markdown("---")

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">AI Prediction Center</div>
        <div class="hero-subtitle">Predict machine failure probability, health condition, and maintenance recommendations</div>
        <div class="hero-badges">
            <span class="hero-badge blue">● AI-Powered</span>
            <span class="hero-badge green">● Random Forest Model</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Input Section
st.markdown("### Sensor Input Parameters")

col1, col2 = st.columns(2)

with col1:
    air_temperature = st.number_input("Air Temperature (°C)", value=60.0, step=0.5)
    process_temperature = st.number_input("Process Temperature (°C)", value=70.0, step=0.5)
    rotational_speed = st.number_input("Rotational Speed (RPM)", value=1500, step=10)
    torque = st.number_input("Torque (Nm)", value=20.0, step=0.5)

with col2:
    tool_wear = st.number_input("Tool Wear", value=200, step=1)
    pressure = st.number_input("Pressure (bar)", value=2.0, step=0.1)
    vibration = st.number_input("Vibration (mm/s)", value=3.0, step=0.1)
    electrical_current = st.number_input("Electrical Current (A)", value=15.0, step=0.5)

PREDICT_URL = "http://127.0.0.1:8000/predict"

if st.button("Run Prediction", use_container_width=True, type="primary"):
    payload = {
        "air_temperature": air_temperature,
        "process_temperature": process_temperature,
        "rotational_speed": int(rotational_speed),
        "torque": torque,
        "tool_wear": int(tool_wear),
        "pressure": pressure,
        "vibration": vibration,
        "electrical_current": electrical_current,
    }

    with st.spinner("Analyzing machine condition..."):
        result = predict_with_fallback(payload, backend_url=PREDICT_URL)
        machine_failure = result.get("machine_failure", 0)
        status = result.get("status", "NORMAL")
        failure_probability = float(result.get("failure_probability", 0.0))
        health_score = float(result.get("health_score", (1.0 - failure_probability) * 100.0))
        rul = round((health_score / 100.0) * 90, 2) if status != "FAILURE" else 10

        if result.get("used_fallback"):
            st.info("Backend prediction service was unavailable, so a local heuristic fallback was used.")

        # Status Banner
        if machine_failure == 1:
            st.error("⚠️ Potential Failure Detected")
        else:
            st.success("✅ Machine Operating Normally")

        # Gauges
        st.markdown("### Prediction Results")
        g1, g2, g3 = st.columns(3)
        with g1:
            st.plotly_chart(gauge_chart(health_score, "Health Score", 100), use_container_width=True, key="pred_health_gauge")
        with g2:
            st.plotly_chart(
                gauge_chart(failure_probability * 100, "Failure Probability", 100, "%"),
                use_container_width=True,
                key="pred_failure_gauge"
            )
        with g3:
            st.plotly_chart(
                gauge_chart(rul, "Estimated RUL", max_value=max(100, int(rul) + 20)),
                use_container_width=True,
                key="pred_rul_gauge"
            )

        st.markdown("---")

        # Result Metrics
        metrics_cols = st.columns(4)
        metrics_cols[0].metric("Status", status)
        metrics_cols[1].metric("Failure Probability", f"{failure_probability:.4f}")
        metrics_cols[2].metric("Health Score", f"{health_score:.2f}%")
        metrics_cols[3].metric("RUL", f"{rul} Days")

        # Recommendation
        st.markdown("### Maintenance Recommendation")
        if machine_failure == 1:
            st.warning("""
            - Inspect bearing condition
            - Check shaft alignment
            - Verify lubrication system
            - Schedule maintenance immediately
            """)
        else:
            st.success("""
            - Continue routine monitoring
            - Follow preventive maintenance schedule
            - Review sensor trends weekly
            """)

        st.markdown("---")
        st.markdown("### Raw Model Output")
        st.json(result)
else:
    st.info("Adjust sensor input parameters and click 'Run Prediction' to analyze.")

st.markdown("---")
st.markdown("### Model Input Features")
st.write("The prediction model evaluates: Air Temperature, Process Temperature, Rotational Speed, Torque, Tool Wear, Pressure, Vibration, Electrical Current")

