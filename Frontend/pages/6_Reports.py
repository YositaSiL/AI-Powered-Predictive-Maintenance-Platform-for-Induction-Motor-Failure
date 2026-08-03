"""
Reports Page - Generate and export daily, weekly, monthly reports.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Frontend.utils.db_connection import load_dashboard_data
from Frontend.utils.charts import gauge_chart

st.set_page_config(page_title="Reports - Predictive Maintenance", layout="wide")

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
        <div class="hero-title">Reports & Analytics</div>
        <div class="hero-subtitle">Generate comprehensive maintenance and health analysis reports</div>
        <div class="hero-badges">
            <span class="hero-badge blue">● Analytics</span>
            <span class="hero-badge green">● Export Ready</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

df, source = load_dashboard_data()

# Report period selector
st.markdown("### Report Configuration")
col1, col2, col3 = st.columns(3)
with col1:
    report_type = st.selectbox("Report Type", ["Daily Report", "Weekly Report", "Monthly Report", "Health Summary", "Failure Analysis", "Maintenance Summary"])
with col2:
    date_range = st.date_input("Date Range", [datetime.now() - timedelta(days=7), datetime.now()])
with col3:
    export_format = st.selectbox("Export Format", ["CSV", "JSON"])

generate_report = st.button("Generate Report", use_container_width=True, type="primary")

if generate_report and not df.empty:
    st.markdown("---")

    # Report Header
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-title">{report_type}</div>
            <div class="hero-subtitle">
                Period: {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')} |
                Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} |
                Source: {source}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Summary Stats
    st.markdown("### Executive Summary")
    total_motors = df["motor_id"].nunique() if "motor_id" in df.columns else 0
    avg_health = df["health_score"].mean() if "health_score" in df.columns else 0
    avg_failure = df["failure_probability"].mean() if "failure_probability" in df.columns else 0
    avg_rul = df["rul"].mean() if "rul" in df.columns else 0

    kpi_c = st.columns(4)
    kpi_c[0].markdown(
        f'<div class="metric-card info"><div class="metric-title">Total Motors</div><div class="metric-value">{total_motors}</div></div>',
        unsafe_allow_html=True,
    )
    kpi_c[1].markdown(
        f'<div class="metric-card healthy"><div class="metric-title">Avg Health Score</div><div class="metric-value">{avg_health:.2f}</div></div>',
        unsafe_allow_html=True,
    )
    kpi_c[2].markdown(
        f'<div class="metric-card warning"><div class="metric-title">Avg Failure Prob</div><div class="metric-value">{avg_failure:.2%}</div></div>',
        unsafe_allow_html=True,
    )
    kpi_c[3].markdown(
        f'<div class="metric-card info"><div class="metric-title">Avg RUL</div><div class="metric-value">{avg_rul:.1f} Days</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Health Distribution
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### Health Score Distribution")
        if "health_score" in df.columns:
            fig = px.histogram(df, x="health_score", nbins=20, title="Health Score Distribution",
                             color_discrete_sequence=["#3b82f6"])
            fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font={"color": "#cbd5e1"})
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("### Risk Level Distribution")
        if "risk_level" in df.columns:
            risk_counts = df["risk_level"].value_counts().reset_index()
            risk_counts.columns = ["Risk Level", "Count"]
            fig = px.pie(risk_counts, names="Risk Level", values="Count",
                        color_discrete_sequence=["#00ff88", "#ffd700", "#ff8c00", "#ff4444"])
            fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font={"color": "#cbd5e1"})
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Failure Analysis
    st.markdown("### Failure Analysis")
    if "machine_failure" in df.columns:
        failure_counts = df["machine_failure"].value_counts().reset_index()
        failure_counts.columns = ["Failure", "Count"]
        fig = px.bar(failure_counts, x="Failure", y="Count", title="Machine Failure Distribution",
                    color_discrete_sequence=["#3b82f6"])
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font={"color": "#cbd5e1"})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Full Data Table
    st.markdown("### Report Data")
    display_cols = [c for c in ["motor_id", "type", "air_temperature", "process_temperature",
                                "rotational_speed", "torque", "tool_wear", "pressure",
                                "vibration", "electrical_current", "health_score",
                                "failure_probability", "rul", "risk_level"]
                   if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

    # Export
    csv_data = df.to_csv(index=False).encode("utf-8")
    json_data = df.to_json(orient="records").encode("utf-8")

    export_col1, export_col2 = st.columns(2)
    with export_col1:
        st.download_button("📥 Download CSV", data=csv_data, file_name=f"report_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
    with export_col2:
        st.download_button("📥 Download JSON", data=json_data, file_name=f"report_{datetime.now().strftime('%Y%m%d')}.json", mime="application/json", use_container_width=True)

else:
    st.info("Configure report settings and click 'Generate Report' to create a report.")

