"""
Alerts Page - Professional Alert Center for monitoring all machine alerts.
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Frontend.utils.db_connection import load_dashboard_data

st.set_page_config(page_title="Alerts - Predictive Maintenance", layout="wide")

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
        <div class="hero-title">Alert Center</div>
        <div class="hero-subtitle">Centralized monitoring and management of all machine alerts</div>
        <div class="hero-badges">
            <span class="hero-badge green">● Active Monitoring</span>
            <span class="hero-badge red">● Real-time Alerts</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

df, source = load_dashboard_data()

# Status summary
st.markdown("### Alert Status Overview")
filter_cols = st.columns(3)
with filter_cols[0]:
    severity_filter = st.multiselect(
        "Severity", ["CRITICAL", "WARNING", "INFO"],
        default=["CRITICAL", "WARNING"]
    )
with filter_cols[1]:
    motor_options = []
    motor_filter = []
    if not df.empty and "motor_id" in df.columns:
        motor_options = sorted(df["motor_id"].astype(str).unique().tolist())
        default_motor_ids = motor_options[:5] if len(motor_options) > 5 else motor_options
        motor_filter = st.multiselect("Motor ID", motor_options, default=default_motor_ids)
    else:
        st.multiselect("Motor ID", motor_options, default=[], disabled=True)
with filter_cols[2]:
    alert_type_filter = st.multiselect(
        "Alert Type", ["HEALTH", "FAILURE", "SENSOR", "MAINTENANCE"],
        default=["HEALTH", "FAILURE"]
    )

# Simulated alert data based on dataset health scores
alerts_data = []
if not df.empty:
    for _, row in df.head(50).iterrows():
        health = row.get("health_score", row.get("rul", 50))
        failure_prob = row.get("failure_probability", 0)
        motor_id = str(row.get("motor_id", "Unknown"))

        if isinstance(health, (int, float)) and health < 40:
            severity = "CRITICAL"
            alert_type = "HEALTH"
            message = f"Health score critically low: {health:.1f}"
        elif isinstance(failure_prob, (int, float)) and failure_prob > 0.7:
            severity = "CRITICAL"
            alert_type = "FAILURE"
            message = f"Failure probability exceeded: {failure_prob:.2%}"
        elif isinstance(health, (int, float)) and health < 60:
            severity = "WARNING"
            alert_type = "HEALTH"
            message = f"Health score below threshold: {health:.1f}"
        else:
            continue

        if severity in severity_filter and motor_id in motor_filter and alert_type in alert_type_filter:
            alerts_data.append({
                "Motor ID": motor_id,
                "Severity": severity,
                "Alert Type": alert_type,
                "Message": message,
                "Status": "Active" if severity == "CRITICAL" else "Acknowledged",
            })

# KPI cards for alert summary
critical_count = sum(1 for a in alerts_data if a["Severity"] == "CRITICAL")
warning_count = sum(1 for a in alerts_data if a["Severity"] == "WARNING")
info_count = sum(1 for a in alerts_data if a["Severity"] == "INFO")

kpi_c = st.columns(4)
kpi_c[0].markdown(
    f'<div class="metric-card critical"><div class="metric-title">Total Alerts</div><div class="metric-value">{len(alerts_data)}</div><div class="metric-sub">All active alerts</div></div>',
    unsafe_allow_html=True,
)
kpi_c[1].markdown(
    f'<div class="metric-card critical"><div class="metric-title">Critical</div><div class="metric-value">{critical_count}</div><div class="metric-sub">Immediate attention</div></div>',
    unsafe_allow_html=True,
)
kpi_c[2].markdown(
    f'<div class="metric-card warning"><div class="metric-title">Warning</div><div class="metric-value">{warning_count}</div><div class="metric-sub">Needs review</div></div>',
    unsafe_allow_html=True,
)
kpi_c[3].markdown(
    f'<div class="metric-card info"><div class="metric-title">Info</div><div class="metric-value">{info_count}</div><div class="metric-sub">Informational</div></div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# Alert Table
st.markdown("### Alert Log")
if alerts_data:
    alert_df = pd.DataFrame(alerts_data)
    # Color-code severity
    def highlight_severity(val):
        if val == "CRITICAL":
            return "color: #ff4444; font-weight: 700"
        elif val == "WARNING":
            return "color: #ffd700; font-weight: 600"
        return "color: #00ff88"
    
    styled_df = alert_df.style.map(highlight_severity, subset=["Severity"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Export CSV
    csv_data = alert_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Export Alerts to CSV",
        data=csv_data,
        file_name="alerts_export.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.success("✅ No alerts matching current filters.")

st.markdown("---")

# Alert summary by motor
if alerts_data:
    st.markdown("### Alerts by Motor")
    motor_alert_counts = alert_df.groupby("Motor ID").size().reset_index(name="Count")
    st.dataframe(motor_alert_counts, use_container_width=True, hide_index=True)
