"""
Sensor Monitoring Page - Live sensor data visualization and monitoring.
Multi-parameter monitoring for temperature, vibration, current, pressure, voltage, RPM.
"""
import sys
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Frontend.utils.simulation import (
    clamp, safe_mean, linear_trend, simulate_next_record, get_recent_records
)
from Frontend.utils.feature_engineering import (
    compute_features, compute_anomaly_score, compute_degradation_score
)
from Frontend.utils.prediction import (
    risk_level, degradation_level, failure_label, maintenance_window,
    dominant_signals, recommendation, estimate_realtime_failure_probability
)
from Frontend.utils.helper import (
    SHORT_WINDOW, MEDIUM_WINDOW, LONG_WINDOW, REPORT_INTERVAL_SECONDS,
    ALERT_COOLDOWN_SECONDS, HISTORY_LIMIT, BASE_THRESHOLDS, ALL_RISK_LEVELS,
    get_dataset_machine_ids, init_session_state, load_cleaned_dataset
)
from Frontend.utils.charts import gauge_chart

st.set_page_config(page_title="Sensor Monitoring - Predictive Maintenance", layout="wide")

css_path = PROJECT_ROOT / "Frontend" / "styles" / "streamlit.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

MACHINE_IDS = get_dataset_machine_ids() or []
init_session_state(MACHINE_IDS)

# Seed initial data
if "sensor_seeded" not in st.session_state:
    from Frontend.app import update_one_cycle
    for _ in range(5):
        update_one_cycle()
    st.session_state.sensor_seeded = True

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">Sensor Monitoring Center</div>
        <div class="hero-subtitle">Real-time multi-parameter monitoring of induction motors | Temperature, Vibration, Current, Pressure, Voltage, RPM</div>
        <div class="hero-badges">
            <span class="hero-badge green">● Live Data</span>
            <span class="hero-badge blue">● Real-time Streaming</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar controls
with st.sidebar:
    # Navigation
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

    st.markdown('<div class="sidebar-section-title">Sensor Controls</div>', unsafe_allow_html=True)

    available_machines = MACHINE_IDS if MACHINE_IDS else []
    selected_machine = st.selectbox(
        "Select Motor", available_machines, index=0 if available_machines else 0,
        key="sensor_motor_select"
    )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Start", use_container_width=True, key="sensor_start"):
            st.session_state.running = True
    with col2:
        if st.button("⏹ Stop", use_container_width=True, key="sensor_stop"):
            st.session_state.running = False

    if st.button("⚡ Generate Cycle", use_container_width=True, key="sensor_gen_cycle"):
        from Frontend.app import update_one_cycle
        update_one_cycle()

    auto_refresh = st.checkbox("Auto Refresh", value=True, key="sensor_autorefresh")
    st.session_state.auto_refresh = auto_refresh

# Run simulation if active
if st.session_state.get("running", False):
    from Frontend.app import update_one_cycle
    update_one_cycle()

# Get latest data for selected machine
machine_data = st.session_state.get("machine_data", {})
records = list(machine_data.get(selected_machine, {}).get("records", []))
features = list(machine_data.get(selected_machine, {}).get("features", []))

if not records:
    st.warning("No sensor data available yet. Start monitoring or generate a cycle.")
    st.stop()

latest_record = records[-1] if records else None
latest_feature = features[-1] if features else None

# --- KPI ROW ---
st.markdown("### Live Sensor Readings")
kpi_cols = st.columns(6)
kpi_cols[0].metric("🌡️ Temperature", f"{latest_record['temperature']:.1f} °C",
                    delta=f"{latest_record['temperature'] - 70:.1f} °C")
kpi_cols[1].metric("📳 Vibration", f"{latest_record['vibration']:.3f} mm/s",
                    delta=f"{latest_record['vibration'] - 2.5:.2f}")
kpi_cols[2].metric("⚡ Current", f"{latest_record['current']:.2f} A",
                    delta=f"{latest_record['current'] - 15:.1f}")
kpi_cols[3].metric("🔧 Pressure", f"{latest_record['pressure']:.2f} bar",
                    delta=f"{latest_record['pressure'] - 2.0:.2f}")
kpi_cols[4].metric("🔋 Voltage", f"{latest_record['voltage']:.1f} V",
                    delta=f"{latest_record['voltage'] - 380:.0f}")
kpi_cols[5].metric("⚙️ RPM", f"{latest_record['rpm']:.0f}",
                    delta=f"{latest_record['rpm'] - 1480:.0f}")

st.markdown("---")

# --- SENSOR TRENDS ---
st.markdown("### Real-time Sensor Trends")
if len(records) > 1:
    history_df = pd.DataFrame(records)
    history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])

    col_left, col_right = st.columns(2)

    with col_left:
        fig_temp = px.line(history_df, x="timestamp", y="temperature",
                          title="Temperature Trend (°C)",
                          color_discrete_sequence=["#ff4444"])
        fig_temp.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              font={"color": "#cbd5e1", "size": 10},
                              xaxis={"gridcolor": "rgba(148,163,184,0.1)"},
                              yaxis={"gridcolor": "rgba(148,163,184,0.1)",
                                     "range": [30, 120]})
        fig_temp.add_hline(y=75, line_dash="dash", line_color="#ffd700",
                          annotation_text="Warning")
        fig_temp.add_hline(y=90, line_dash="dash", line_color="#ff4444",
                          annotation_text="Critical")
        st.plotly_chart(fig_temp, use_container_width=True, key="sensor_temp_chart")

        fig_current = px.line(history_df, x="timestamp", y="current",
                             title="Current Trend (A)",
                             color_discrete_sequence=["#06b6d4"])
        fig_current.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="rgba(0,0,0,0)",
                                  font={"color": "#cbd5e1", "size": 10},
                                  xaxis={"gridcolor": "rgba(148,163,184,0.1)"},
                                  yaxis={"gridcolor": "rgba(148,163,184,0.1)",
                                         "range": [0, 45]})
        fig_current.add_hline(y=20, line_dash="dash", line_color="#ffd700",
                             annotation_text="Warning")
        fig_current.add_hline(y=30, line_dash="dash", line_color="#ff4444",
                             annotation_text="Critical")
        st.plotly_chart(fig_current, use_container_width=True, key="sensor_current_chart")

        fig_voltage = px.line(history_df, x="timestamp", y="voltage",
                             title="Voltage Trend (V)",
                             color_discrete_sequence=["#8b5cf6"])
        fig_voltage.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="rgba(0,0,0,0)",
                                  font={"color": "#cbd5e1", "size": 10},
                                  xaxis={"gridcolor": "rgba(148,163,184,0.1)"},
                                  yaxis={"gridcolor": "rgba(148,163,184,0.1)",
                                         "range": [300, 420]})
        fig_voltage.add_hline(y=360, line_dash="dash", line_color="#ffd700",
                             annotation_text="Warning Low")
        st.plotly_chart(fig_voltage, use_container_width=True, key="sensor_voltage_chart")

    with col_right:
        fig_vib = px.line(history_df, x="timestamp", y="vibration",
                         title="Vibration Trend (mm/s)",
                         color_discrete_sequence=["#ffd700"])
        fig_vib.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              font={"color": "#cbd5e1", "size": 10},
                              xaxis={"gridcolor": "rgba(148,163,184,0.1)"},
                              yaxis={"gridcolor": "rgba(148,163,184,0.1)",
                                     "range": [0, 12]})
        fig_vib.add_hline(y=4.5, line_dash="dash", line_color="#ffd700",
                         annotation_text="Warning")
        fig_vib.add_hline(y=7.0, line_dash="dash", line_color="#ff4444",
                         annotation_text="Critical")
        st.plotly_chart(fig_vib, use_container_width=True, key="sensor_vib_chart")

        fig_pressure = px.line(history_df, x="timestamp", y="pressure",
                              title="Pressure Trend (bar)",
                              color_discrete_sequence=["#ff8c00"])
        fig_pressure.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)",
                                   plot_bgcolor="rgba(0,0,0,0)",
                                   font={"color": "#cbd5e1", "size": 10},
                                   xaxis={"gridcolor": "rgba(148,163,184,0.1)"},
                                   yaxis={"gridcolor": "rgba(148,163,184,0.1)",
                                          "range": [0, 5]})
        fig_pressure.add_hline(y=1.2, line_dash="dash", line_color="#ffd700",
                              annotation_text="Warning Low")
        st.plotly_chart(fig_pressure, use_container_width=True, key="sensor_pressure_chart")

        fig_rpm = px.line(history_df, x="timestamp", y="rpm",
                         title="RPM Trend",
                         color_discrete_sequence=["#00ff88"])
        fig_rpm.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              font={"color": "#cbd5e1", "size": 10},
                              xaxis={"gridcolor": "rgba(148,163,184,0.1)"},
                              yaxis={"gridcolor": "rgba(148,163,184,0.1)",
                                     "range": [800, 1550]})
        fig_rpm.add_hline(y=1300, line_dash="dash", line_color="#ffd700",
                         annotation_text="Warning Low")
        st.plotly_chart(fig_rpm, use_container_width=True, key="sensor_rpm_chart")

st.markdown("---")

# --- ANOMALY & DEGRADATION SCORES ---
st.markdown("### Health Analytics")
if latest_feature:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(gauge_chart(latest_feature.get("anomaly_score", 0),
                                    "Anomaly Score", 100), use_container_width=True, key="sensor_anomaly_gauge")
    with col2:
        st.plotly_chart(gauge_chart(latest_feature.get("degradation_score", 0),
                                    "Degradation Score", 100), use_container_width=True, key="sensor_degradation_gauge")
    with col3:
        fp = estimate_realtime_failure_probability(latest_feature)
        st.plotly_chart(gauge_chart(fp * 100, "Failure Probability", 100, "%"),
                       use_container_width=True, key="sensor_fp_gauge")

st.markdown("---")

# --- COMBINED OVERVIEW ---
st.markdown("### Multi-Parameter Comparison")
if len(records) > 1:
    # Normalize all parameters to 0-100 for comparison
    compare_df = history_df.tail(50).copy()
    for param, (min_val, max_val) in [
        ("temperature", (30, 120)),
        ("vibration", (0, 12)),
        ("current", (0, 45)),
        ("pressure", (0, 5)),
        ("voltage", (300, 420)),
        ("rpm", (800, 1550)),
    ]:
        compare_df[f"{param}_norm"] = (
            (compare_df[param] - min_val) / (max_val - min_val) * 100
        ).clip(0, 100)

    fig_compare = go.Figure()
    colors = {"temperature": "#ff4444", "vibration": "#ffd700",
              "current": "#06b6d4", "pressure": "#ff8c00",
              "voltage": "#8b5cf6", "rpm": "#00ff88"}
    for param in ["temperature", "vibration", "current", "pressure", "voltage", "rpm"]:
        fig_compare.add_trace(go.Scatter(
            x=compare_df["timestamp"],
            y=compare_df[f"{param}_norm"],
            mode="lines",
            name=param.title(),
            line=dict(color=colors[param], width=1.5),
        ))
    fig_compare.update_layout(
        title="Normalized Sensor Parameters (0-100%)",
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#cbd5e1", "size": 10},
        xaxis={"gridcolor": "rgba(148,163,184,0.1)"},
        yaxis={"gridcolor": "rgba(148,163,184,0.1)", "range": [0, 100]},
        hovermode="x unified",
        legend=dict(font={"color": "#cbd5e1", "size": 10}),
    )
    st.plotly_chart(fig_compare, use_container_width=True, key="sensor_compare_chart")

st.markdown("---")

# --- SENSOR DATA TABLE ---
st.markdown("### Historical Sensor Data")
if records:
    display_df = pd.DataFrame(records[-100:])
    display_df["timestamp"] = pd.to_datetime(display_df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- THRESHOLD LEGEND ---
st.markdown("### Threshold Reference")
thresh = st.session_state.get("thresholds", BASE_THRESHOLDS)
legend_data = []
for param, levels in thresh.items():
    for level, value in levels.items():
        legend_data.append({"Parameter": param.title(), "Threshold": level.title(),
                           "Value": value})
st.dataframe(pd.DataFrame(legend_data), use_container_width=True, hide_index=True)

# Auto refresh
if st.session_state.get("running", False) and st.session_state.get("auto_refresh", False):
    time.sleep(st.session_state.get("refresh_interval", 1.0))
    st.rerun()

