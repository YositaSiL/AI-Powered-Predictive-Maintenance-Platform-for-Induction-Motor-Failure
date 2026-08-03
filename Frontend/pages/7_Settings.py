"""
AI-Powered Predictive Maintenance Platform
Settings Page
Configure monitoring thresholds, system preferences,
and application behaviour.
"""

import sys
from pathlib import Path
from copy import deepcopy
from datetime import datetime

import streamlit as st

# ==========================================================
# PROJECT SETUP
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Frontend.utils.helper import BASE_THRESHOLDS
from Frontend.utils.db_connection import load_dashboard_data

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Settings - Predictive Maintenance",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================================
# LOAD CSS
# ==========================================================

css_path = PROJECT_ROOT / "Frontend" / "styles" / "streamlit.css"

if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

# ==========================================================
# FETCH DYNAMIC DATA
# ==========================================================

try:
    df, _ = load_dashboard_data()
    dataset_size = f"{len(df):,} Records" if not df.empty else "No Data"
except:
    dataset_size = "1,000 Records (Simulated)"

# ==========================================================
# SESSION STATE INITIALIZATION
# ==========================================================

if "thresholds" not in st.session_state:
    st.session_state.thresholds = deepcopy(BASE_THRESHOLDS)

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 1.0

if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

# Initialize threshold widget keys to match session_state values
threshold_info = {
    "temperature": {"unit": "°C", "step": 0.5},
    "vibration": {"unit": "mm/s", "step": 0.1},
    "current": {"unit": "A", "step": 0.5},
    "pressure": {"unit": "Bar", "step": 0.05},
    "voltage": {"unit": "V", "step": 1.0},
    "rpm": {"unit": "RPM", "step": 10.0},
}
LOW_THRESHOLD_PARAMS = {"pressure", "voltage", "rpm"}

for param in threshold_info:
    current = st.session_state.thresholds.get(param, {})

    if f"in_warn_{param}" not in st.session_state:
        st.session_state[f"in_warn_{param}"] = float(current.get("warning", 70.0))

    if f"in_crit_{param}" not in st.session_state:
        st.session_state[f"in_crit_{param}"] = float(current.get("critical", 80.0))

    if param in LOW_THRESHOLD_PARAMS:
        if f"in_warn_low_{param}" not in st.session_state:
            st.session_state[f"in_warn_low_{param}"] = float(current.get("warning_low", 0.0))

        if f"in_crit_low_{param}" not in st.session_state:
            st.session_state[f"in_crit_low_{param}"] = float(current.get("critical_low", 0.0))

# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="sidebar-logo-text">
                Astra Otoparts
            </div>
            <div class="sidebar-logo-sub">
                Predictive Maintenance Platform
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

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
    st.markdown("### System Status")
    st.success("Monitoring Engine Online")
    st.info(f"Last Update\n\n{datetime.now().strftime('%d %b %Y %H:%M:%S')}")

# ==========================================================
# HERO
# ==========================================================

st.markdown(
    """
<div class="hero-card">
    <div class="hero-title">
        System Settings
    </div>
    <div class="hero-subtitle">
        Configure monitoring thresholds, application preferences, simulation behaviour, and predictive maintenance parameters.
    </div>
    <br>
    <div class="hero-badges">
        <span class="hero-badge green">● Monitoring Active</span>
        <span class="hero-badge blue">● AI Prediction Enabled</span>
        <span class="hero-badge orange">● Threshold Management</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ==========================================================
# PAGE INTRODUCTION
# ==========================================================

st.markdown("## System Configuration")

st.caption(
    """
Use this page to configure the monitoring system.
Changes made here affect:
• Sensor Warning Thresholds
• Critical Thresholds
• Dashboard Refresh Behaviour
• Simulation Mode

These settings allow maintenance engineers to adapt the platform to different machine operating conditions without modifying code.
"""
)
st.markdown("---")

# ==========================================================
# MONITORING THRESHOLD CONFIGURATION
# ==========================================================

st.markdown("## Monitoring Thresholds")
st.caption(
    """
Configure Warning and Critical limits for each monitored sensor.
These values are used by the AI engine to classify machine condition.
"""
)

rows = [
    ["temperature", "vibration"],
    ["current", "pressure"],
    ["voltage", "rpm"],
]

for row in rows:
    col1, col2 = st.columns(2)
    for col, param in zip([col1, col2], row):
        info = threshold_info[param]
        
        with col:
            st.markdown(
                f"""
                <div class="section-card" style="background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 15px;">
                    <h3 style="margin-top: 0; margin-bottom: 5px; color: #f8fafc; font-size: 1.1rem;">{param.title()}</h3>
                    <p style="margin: 0; color: #94a3b8; font-size: 0.85rem;">Adjust monitoring thresholds.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            warning = st.number_input(
                f"{param.title()} Warning ({info['unit']})",
                min_value=0.0, step=info["step"],
                key=f"in_warn_{param}",
            )

            critical = st.number_input(
                f"{param.title()} Critical ({info['unit']})",
                min_value=0.0, step=info["step"],
                key=f"in_crit_{param}",
            )

            warning_low, critical_low = None, None
            if param in LOW_THRESHOLD_PARAMS:
                warning_low = st.number_input(
                    f"{param.title()} Warning Low ({info['unit']})",
                    min_value=0.0, step=info["step"],
                    key=f"in_warn_low_{param}",
                )

                critical_low = st.number_input(
                    f"{param.title()} Critical Low ({info['unit']})",
                    min_value=0.0, step=info["step"],
                    key=f"in_crit_low_{param}",
                )
            
            if param in LOW_THRESHOLD_PARAMS:
                st.markdown(f"""
                <div style="background-color: #0f172a; padding: 10px; border-radius: 5px; font-size: 13px; color: #cbd5e1; margin-top: 5px; border: 1px solid #334155;">
                    <strong style="color: #f8fafc;">Preview Range:</strong><br>
                    <b>&lt; {critical_low}</b> {info['unit']} (Crit Low)<br>
                    <b>{critical_low} - {warning_low}</b> {info['unit']} (Warn Low)<br>
                    <b>{warning_low} - {warning}</b> {info['unit']} (Normal)<br>
                    <b>{warning} - {critical}</b> {info['unit']} (Warn High)<br>
                    <b>&gt; {critical}</b> {info['unit']} (Crit High)
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #0f172a; padding: 10px; border-radius: 5px; font-size: 13px; color: #cbd5e1; margin-top: 5px; border: 1px solid #334155;">
                    <strong style="color: #f8fafc;">Preview Range:</strong><br>
                    <b>&lt; {warning}</b> {info['unit']} (Normal)<br>
                    <b>{warning} - {critical}</b> {info['unit']} (Warning)<br>
                    <b>&gt; {critical}</b> {info['unit']} (Critical)
                </div>
                """, unsafe_allow_html=True)

            st.write("")

st.markdown("---")

# ==========================================================
# APPLICATION SETTINGS
# ==========================================================

st.markdown("## Application Settings")

app_left, app_right = st.columns(2)

with app_left:
    st.markdown("### Monitoring")
    st.session_state.auto_refresh = st.toggle(
        "Enable Auto Refresh",
        value=st.session_state.auto_refresh,
    )
    st.session_state.demo_mode = st.toggle(
        "Demo Mode",
        value=st.session_state.demo_mode,
    )

with app_right:
    st.markdown("### Refresh")
    st.session_state.refresh_interval = st.slider(
        "Refresh Interval (seconds)",
        min_value=0.5,
        max_value=10.0,
        value=float(st.session_state.refresh_interval),
        step=0.5,
    )

st.markdown("---")

# ==========================================================
# SYSTEM INFORMATION
# ==========================================================

st.markdown("## System Information")

info1, info2, info3, info4 = st.columns(4)

with info1:
    st.metric("Dataset", dataset_size)

with info2:
    st.metric("Database", "SQLite / PostgreSQL")

with info3:
    st.metric("Version", "1.0.0")

with info4:
    st.metric("Last Update", datetime.now().strftime("%d %b %Y"))

st.markdown("---")

# ==========================================================
# SAVE CONFIGURATION
# ==========================================================

st.markdown("## Save Configuration")

save1, save2 = st.columns(2)

with save1:
    if st.button("Save All Settings", use_container_width=True, type="primary"):
        for param in threshold_info:
            if param not in st.session_state.thresholds:
                st.session_state.thresholds[param] = {}
                
            st.session_state.thresholds[param]["warning"] = st.session_state[f"in_warn_{param}"]
            st.session_state.thresholds[param]["critical"] = st.session_state[f"in_crit_{param}"]
            
            if param in LOW_THRESHOLD_PARAMS:
                st.session_state.thresholds[param]["warning_low"] = st.session_state[f"in_warn_low_{param}"]
                st.session_state.thresholds[param]["critical_low"] = st.session_state[f"in_crit_low_{param}"]
                
        st.success("All configuration and thresholds have been saved successfully.")

with save2:
    if st.button("Restore Default Thresholds", use_container_width=True):
        st.session_state.thresholds = deepcopy(BASE_THRESHOLDS)
        
        for param in threshold_info:
            current = BASE_THRESHOLDS.get(param, {})
            
            st.session_state[f"in_warn_{param}"] = float(current.get("warning", 70.0))
            st.session_state[f"in_crit_{param}"] = float(current.get("critical", 80.0))
            
            if param in LOW_THRESHOLD_PARAMS:
                st.session_state[f"in_warn_low_{param}"] = float(current.get("warning_low", 0.0))
                st.session_state[f"in_crit_low_{param}"] = float(current.get("critical_low", 0.0))
                
        st.success("Default thresholds restored. Widget updated.")
        st.rerun()

st.markdown("---")

# ==========================================================
# SYSTEM TOOLS
# ==========================================================

st.markdown("## System Tools")

tool1, tool2 = st.columns(2)

with tool1:
    if st.button("Restart Simulation", use_container_width=True):
        st.info("Simulation state has been refreshed.")

with tool2:
    if st.button("Reset Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key != "initialized":
                del st.session_state[key]
        st.rerun()

st.markdown("---")

# ==========================================================
# ADVANCED CONFIGURATION
# ==========================================================

with st.expander("Advanced Configuration", expanded=False):
    st.caption("Current threshold configuration used by the prediction engine.")
    st.json(st.session_state.thresholds)