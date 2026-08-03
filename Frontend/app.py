"""
AI-Powered Predictive Maintenance Platform for Induction Motor Failure
Main Dashboard (Home Page)

Astra Otoparts - Enterprise Predictive Maintenance Platform
"""
import sys
import time
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Frontend.utils.prediction import (
    risk_level, degradation_level, failure_label, maintenance_window,
    dominant_signals, recommendation, estimate_realtime_failure_probability
)
from Frontend.utils.helper import (
    LONG_WINDOW, ALERT_COOLDOWN_SECONDS, ALL_RISK_LEVELS,
    get_dataset_machine_ids, init_session_state, load_cleaned_dataset
)
from Frontend.utils.charts import gauge_chart
from Frontend.utils.components import (
    hero_card, metric_card, section_card, empty_state,
    status_badge, asset_card, alert_banner
)
from Frontend.utils.simulation_loop import (
    update_one_cycle, analyze_periodic, check_realtime_alert,
    latest_record, latest_feature, latest_report, latest_alert,
    make_machine_summary_df, get_machine_history_df
)

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Astra Otoparts - Predictive Maintenance Platform",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# LOAD CUSTOM CSS
# =========================================================
def load_custom_css():
    css_path = PROJECT_ROOT / "Frontend" / "styles" / "streamlit.css"
    try:
        if css_path.exists():
            css = css_path.read_text(encoding="utf-8")
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception:
        pass

load_custom_css()

# =========================================================
# GET MACHINE IDS
# =========================================================
MACHINE_IDS = get_dataset_machine_ids() or []
if not MACHINE_IDS:
    st.warning(
        "No product_id values found in dataset. The 'Select motor' dropdown "
        "may be empty. Please check the 'product_id' column and CSV format."
    )

# =========================================================
# INIT SESSION STATE
# =========================================================
init_session_state(MACHINE_IDS)

# =========================================================
# DATASET INSPECTION
# =========================================================

def show_dataset_inspection(df, filename):
    """Display dataset inspection section (preserved from original)."""
    container = st.container()
    with container:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title"><span class="title-accent"></span> Dataset Inspection & Visualization</div>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        duplicate_count = int(df.duplicated().sum())
        missing_count = int(df.isna().sum().sum())
        product_count = int(df["product_id"].nunique()) if "product_id" in df.columns else "N/A"
        failure_rate = float(df["machine_failure"].mean() * 100) if "machine_failure" in df.columns else None

        col1.metric("Dataset file", filename)
        col2.metric("Total rows", len(df))
        col3.metric("Duplicate rows", duplicate_count)
        col4.metric("Missing values", missing_count)

        extra1, extra2, extra3, extra4 = st.columns(4)
        extra1.metric("Unique products", product_count)
        if failure_rate is not None:
            extra2.metric("Failure rate", f"{failure_rate:.2f}%")
        else:
            extra2.metric("Failure rate", "N/A")
        extra3.metric("Columns", len(df.columns))
        extra4.metric("Sample rows", 10)

        if duplicate_count > 0 or missing_count > 0:
            st.warning("Dataset has duplicates or missing values. Please inspect and clean if necessary.")
        else:
            st.success("Dataset is clean of duplicates and missing values.")

        st.markdown("### Statistics Summary")
        numeric_cols = [c for c in df.columns if df[c].dtype.kind in "biufc"]
        st.dataframe(
            df[numeric_cols].describe().T.reset_index().rename(columns={"index": "feature"}),
            use_container_width=True,
        )

        st.markdown("### Main Visualizations")
        chart_cols = ["air_temperature", "process_temperature", "tool_wear", "vibration"]
        row1, row2 = st.columns(2)
        with row1:
            if "air_temperature" in df.columns and "process_temperature" in df.columns:
                fig = px.scatter(
                    df, x="air_temperature", y="process_temperature",
                    color="machine_failure" if "machine_failure" in df.columns else None,
                    title="Air Temperature vs Process Temperature", opacity=0.8,
                )
                st.plotly_chart(fig, use_container_width=True)
            if "tool_wear" in df.columns:
                fig = px.histogram(df, x="tool_wear", nbins=30, title="Tool Wear Distribution")
                st.plotly_chart(fig, use_container_width=True)
        with row2:
            if "air_temperature" in df.columns:
                fig = px.histogram(df, x="air_temperature", nbins=30, title="Air Temperature Distribution")
                st.plotly_chart(fig, use_container_width=True)
            if "machine_failure" in df.columns:
                failure_counts = df["machine_failure"].value_counts().reset_index()
                failure_counts.columns = ["machine_failure", "count"]
                fig = px.bar(
                    failure_counts, x="machine_failure", y="count",
                    title="Machine Failure Distribution",
                    labels={"machine_failure": "Failure", "count": "Count"},
                )
                st.plotly_chart(fig, use_container_width=True)

        if "type" in df.columns:
            st.markdown("### Product Type Distribution")
            type_counts = df["type"].value_counts().reset_index()
            type_counts.columns = ["type", "count"]
            fig = px.bar(type_counts, x="type", y="count", title="Count Per Product Type", text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Sample Data")
        st.dataframe(df.head(10), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# INITIAL SEED
# =========================================================
if "seeded" not in st.session_state:
    for _ in range(3):
        update_one_cycle()
    st.session_state.seeded = True

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    # Company Logo / Brand
    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="sidebar-logo-text">Astra Otoparts</div>
            <div class="sidebar-logo-sub">Predictive Maintenance Platform</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation
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

    # Control Panel
    st.markdown('<div class="sidebar-section-title">Control Panel</div>', unsafe_allow_html=True)

    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("▶ Start", use_container_width=True):
            st.session_state.running = True
    with col_stop:
        if st.button("⏹ Stop", use_container_width=True):
            st.session_state.running = False

    col_gen, col_reset = st.columns(2)
    with col_gen:
        if st.button("⚡ 1 Cycle", use_container_width=True):
            update_one_cycle()
    with col_reset:
        if st.button("↺ Reset", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("---")

    # Threshold Settings
    with st.expander("Threshold Settings", expanded=False):
        for param, levels in st.session_state.thresholds.items():
            for level, value in levels.items():
                step = 0.1 if "warning" in level or "critical" in level else 1.0
                new_value = st.number_input(
                    f"{param} {level}",
                    value=float(value),
                    step=step,
                    key=f"side_{param}_{level}",
                )
                st.session_state.thresholds[param][level] = new_value

    st.markdown("---")

    # Filters
    st.markdown('<div class="sidebar-section-title">Filters</div>', unsafe_allow_html=True)
    selected_machines = st.multiselect(
        "Filter by motor", options=MACHINE_IDS, default=MACHINE_IDS,
        key="sidebar_machine_filter"
    )
    selected_risk_levels = st.multiselect(
        "Filter by risk level", options=ALL_RISK_LEVELS, default=ALL_RISK_LEVELS,
        key="sidebar_risk_filter"
    )
    show_auto_refresh = st.checkbox("Auto refresh", value=True, key="sidebar_autorefresh")
    st.session_state.auto_refresh = show_auto_refresh

    available_machines = [m for m in selected_machines] if selected_machines else MACHINE_IDS
    if not available_machines:
        available_machines = MACHINE_IDS
    selected_machine = st.selectbox(
        "Select motor", available_machines, index=0,
        key="sidebar_motor_select"
    )
    st.session_state.selected_machine = selected_machine

    st.markdown("---")

    # CSV Export
    history_export_df = []
    for machine_id in available_machines:
        records = list(st.session_state.machine_data[machine_id]["records"])
        if records:
            history_export_df.extend(records)

    if history_export_df:
        export_df = pd.DataFrame(history_export_df)
        csv_data = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export CSV",
            data=csv_data,
            file_name="motor_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("No historical data yet.")

    # Dataset Inspection Toggle
    st.markdown("---")
    show_dataset = st.checkbox("Show Dataset Inspection", value=True, key="sidebar_show_dataset")

# =========================================================
# RUN SIMULATION IF ACTIVE
# =========================================================
if st.session_state.running:
    update_one_cycle()

# =========================================================
# MAIN DASHBOARD CONTENT
# =========================================================

# --- HEADER / HERO ---
hero_status = "success"
hero_msg = "All systems operating normally"
recent_alerts = [
    a for a in st.session_state.alert_log
    if a["machine_id"] in available_machines and a["alert_level"] in selected_risk_levels
]
if recent_alerts:
    top_alert = recent_alerts[0]
    hero_msg = f"Alert: {top_alert['machine_id']} - {top_alert['alert_level']} (Failure Prob: {top_alert['failure_probability']*100:.2f}%)"
    hero_status = "error"

st.markdown(
    f"""
    <div class="hero-card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap;">
            <div>
                <div class="hero-title">Predictive Maintenance Dashboard</div>
                <div class="hero-subtitle">Multi-parameter monitoring and predictive analysis for induction motors | Temperature, Vibration, Current, Pressure, Voltage, RPM</div>
                <div class="hero-badges">
                    <span class="hero-badge green">● System Online</span>
                    <span class="hero-badge blue">● {len(available_machines)} Motors Active</span>
                    {"<span class='hero-badge yellow'>● Warnings Active</span>" if any(a['alert_level']=='WARNING' for a in recent_alerts) else ""}
                    {"<span class='hero-badge red'>● Critical Alerts</span>" if any(a['alert_level']=='CRITICAL' for a in recent_alerts) else ""}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#64748b;font-size:0.75rem;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                <div style="color:#94a3b8;font-size:0.7rem;">Live Monitoring</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Alert banner
if recent_alerts:
    top_alert = recent_alerts[0]
    st.error(
        f"🚨 REALTIME ALERT | {top_alert['machine_id']} | Level: {top_alert['alert_level']} | "
        f"Failure Probability: {top_alert['failure_probability'] * 100:.2f}% | {top_alert['conclusion']}"
    )
else:
    st.success("✅ No critical alert at the moment.")

# --- TOP KPI ROW ---
summary_df = make_machine_summary_df(available_machines)

kpi_cols = st.columns(5)
if not summary_df.empty:
    machine_count = len(summary_df)
    healthy_count = len(summary_df[summary_df["Health Score"] >= 75]) if "Health Score" in summary_df.columns else 0
    warning_count = len(summary_df[(summary_df["Health Score"] >= 50) & (summary_df["Health Score"] < 75)]) if "Health Score" in summary_df.columns else 0
    critical_count = len(summary_df[summary_df["Health Score"] < 50]) if "Health Score" in summary_df.columns else 0
    failure_count = len(summary_df[summary_df["Realtime Failure Prob (%)"] >= 80])

    with kpi_cols[0]:
        st.markdown(
            f"""
            <div class="metric-card healthy">
                <div class="metric-title">Total Machines</div>
                <div class="metric-value">{machine_count}</div>
                <div class="metric-sub">Monitored assets</div>
            </div>
            """, unsafe_allow_html=True
        )
    with kpi_cols[1]:
        st.markdown(
            f"""
            <div class="metric-card healthy">
                <div class="metric-title">Healthy</div>
                <div class="metric-value">{healthy_count}</div>
                <div class="metric-sub">≥ 75 Health Score</div>
            </div>
            """, unsafe_allow_html=True
        )
    with kpi_cols[2]:
        st.markdown(
            f"""
            <div class="metric-card warning">
                <div class="metric-title">Warning</div>
                <div class="metric-value">{warning_count}</div>
                <div class="metric-sub">50-74 Health Score</div>
            </div>
            """, unsafe_allow_html=True
        )
    with kpi_cols[3]:
        st.markdown(
            f"""
            <div class="metric-card critical">
                <div class="metric-title">Critical</div>
                <div class="metric-value">{critical_count}</div>
                <div class="metric-sub">{"< 50 Health Score"}</div>
            </div>
            """, unsafe_allow_html=True
        )
    with kpi_cols[4]:
        st.markdown(
            f"""
            <div class="metric-card critical">
                <div class="metric-title">Failure Risk</div>
                <div class="metric-value">{failure_count}</div>
                <div class="metric-sub">≥ 80% Probability</div>
            </div>
            """, unsafe_allow_html=True
        )
else:
    for idx, (label, sub) in enumerate([("Total Machines", "Monitored assets"), ("Healthy", "≥ 75 Score"),
                                          ("Warning", "50-74 Score"), ("Critical", "< 50 Score"),
                                          ("Failure Risk", "≥ 80% Prob")]):
        with kpi_cols[idx]:
            st.markdown(
                f"""
                <div class="metric-card info">
                    <div class="metric-title">{label}</div>
                    <div class="metric-value">0</div>
                    <div class="metric-sub">{sub}</div>
                </div>
                """, unsafe_allow_html=True
            )

# --- SECOND ROW: GAUGES & DISTRIBUTION ---
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title"><span class="title-accent"></span> System Health Overview</div>', unsafe_allow_html=True)

gauge_cols = st.columns(4)
if not summary_df.empty and selected_machine:
    record = latest_record(selected_machine)
    feature = latest_feature(selected_machine)
    report = latest_report(selected_machine)

    if record and feature:
        realtime_fp = estimate_realtime_failure_probability(feature)
        health_score = report["health_score"] if report else 0

        with gauge_cols[0]:
            st.plotly_chart(gauge_chart(health_score, "Health Score", 100), use_container_width=True, key="dashboard_health_gauge")
        with gauge_cols[1]:
            st.plotly_chart(
                gauge_chart(realtime_fp * 100, "Failure Probability", 100, "%"),
                use_container_width=True,
                key="dashboard_failure_gauge"
            )
        with gauge_cols[2]:
            rul_value = report["output_3_action_plan"]["maintenance_window"] if report else "N/A"
            if isinstance(rul_value, str):
                st.markdown(
                    f"""
                    <div class="metric-card info" style="text-align:center;padding:2rem 1rem;">
                        <div class="metric-title">Remaining Useful Life</div>
                        <div style="font-size:1.2rem;font-weight:700;color:#f8fafc;margin-top:0.5rem;">{rul_value}</div>
                        <div class="metric-sub">Estimated maintenance window</div>
                    </div>
                    """, unsafe_allow_html=True
                )
        with gauge_cols[3]:
            # Risk Distribution Pie
            if not summary_df.empty and "Periodic Risk" in summary_df.columns:
                risk_counts = summary_df["Periodic Risk"].value_counts().reset_index()
                risk_counts.columns = ["Risk", "Count"]
                fig = px.pie(
                    risk_counts, names="Risk", values="Count",
                    title="Risk Distribution",
                    color_discrete_sequence=["#00ff88", "#ffd700", "#ff8c00", "#ff4444"],
                )
                fig.update_layout(
                    height=220, margin=dict(l=10, r=10, t=30, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font={"color": "#cbd5e1", "size": 9},
                    showlegend=True,
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True, key="dashboard_risk_pie")
st.markdown('</div>', unsafe_allow_html=True)

# --- THIRD ROW: TOP RISK, HEALTH TREND, RECENT ALERTS ---
row3_cols = st.columns([1, 1, 1])

with row3_cols[0]:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><span class="title-accent"></span> Top Risk Machines</div>', unsafe_allow_html=True)
    if not summary_df.empty and "Realtime Failure Prob (%)" in summary_df.columns:
        top_risk = summary_df.nlargest(5, "Realtime Failure Prob (%)")[
            ["Machine", "Realtime Failure Prob (%)", "Health Score"]
        ]
        for _, row in top_risk.iterrows():
            risk_pct = row["Realtime Failure Prob (%)"]
            badge_class = "critical" if risk_pct >= 80 else "warning" if risk_pct >= 50 else "healthy"
            st.markdown(
                f"""
                <div class="asset-card" style="border-left-color:{'#ff4444' if risk_pct>=80 else '#ffd700' if risk_pct>=50 else '#00ff88'};">
                    <div class="asset-title">{row['Machine']}</div>
                    <div class="asset-text">
                        <span class="status-badge {badge_class}">{risk_pct:.1f}% Failure Prob</span>
                        {' ' + str(row['Health Score']) if pd.notna(row['Health Score']) else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
    else:
        st.info("No data available.")
    st.markdown('</div>', unsafe_allow_html=True)

with row3_cols[1]:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><span class="title-accent"></span> Health Score Trend</div>', unsafe_allow_html=True)
    if selected_machine:
        history_df = get_machine_history_df(selected_machine)
        if not history_df.empty:
            history_df = history_df.copy()
            history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])
            fig = px.line(
                history_df, x="timestamp", y="temperature",
                title="Temperature Trend",
                color_discrete_sequence=["#3b82f6"],
            )
            fig.update_layout(
                height=200, margin=dict(l=10, r=10, t=25, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#cbd5e1", "size": 10},
                xaxis={"gridcolor": "rgba(148,163,184,0.1)", "zeroline": False},
                yaxis={"gridcolor": "rgba(148,163,184,0.1)", "zeroline": False},
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trend data.")
    st.markdown('</div>', unsafe_allow_html=True)

with row3_cols[2]:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title"><span class="title-accent"></span> Recent Alerts</div>', unsafe_allow_html=True)
    filtered_alerts = [
        a for a in st.session_state.alert_log
        if a["machine_id"] in available_machines and a["alert_level"] in selected_risk_levels
    ]
    if filtered_alerts:
        for alert in filtered_alerts[:5]:
            alert_class = "critical" if alert["alert_level"] == "CRITICAL" else "warning"
            st.markdown(
                f"""
                <div class="asset-card" style="border-left-color:{'#ff4444' if alert['alert_level']=='CRITICAL' else '#ffd700'};">
                    <div class="asset-title">{alert['machine_id']}</div>
                    <div class="asset-text">
                        <span class="status-badge {alert_class}">{alert['alert_level']}</span>
                        {' ' + ' | '.join(alert['trigger_reasons'][:2])}
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
    else:
        st.success("No alerts for current filters.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- MACHINE SUMMARY TABLE ---
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title"><span class="title-accent"></span> Real-Time Machine Summary</div>', unsafe_allow_html=True)
if not summary_df.empty:
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
else:
    st.info("No data available yet. Start monitoring or generate a cycle.")
st.markdown('</div>', unsafe_allow_html=True)

# --- MOTOR DETAIL SECTION ---
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown(
    f'<div class="section-title"><span class="title-accent"></span> Motor Detail: {selected_machine}</div>',
    unsafe_allow_html=True,
)

record = latest_record(selected_machine)
feature = latest_feature(selected_machine)
report = latest_report(selected_machine)
alert = latest_alert(selected_machine)

if record is None or feature is None:
    st.warning("No data available for this motor yet.")
else:
    realtime_fp = estimate_realtime_failure_probability(feature)
    health_score = report["health_score"] if report else 0

    # Gauges
    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(gauge_chart(health_score, "Health Score", 100), use_container_width=True, key="motor_health_gauge")
    with g2:
        st.plotly_chart(
            gauge_chart(realtime_fp * 100, "Failure Probability", 100, "%"),
            use_container_width=True,
            key="motor_failure_gauge"
        )
    with g3:
        st.plotly_chart(
            gauge_chart(feature["degradation_score"], "Degradation Score", 100),
            use_container_width=True,
            key="motor_degradation_gauge"
        )

    # Sensor Snapshot
    st.markdown("### Sensor Snapshot")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Temperature", f"{record['temperature']} °C")
    m2.metric("Vibration", f"{record['vibration']}")
    m3.metric("Current", f"{record['current']} A")
    m4.metric("Pressure", f"{record['pressure']}")
    m5.metric("Voltage", f"{record['voltage']} V")
    m6.metric("RPM", f"{record['rpm']}")

    # Analysis Outputs
    st.markdown("### Analysis Outputs")
    out1, out2, out3 = st.columns(3)
    with out1:
        st.markdown("##### 1) Health Summary")
        if report:
            st.json(report["output_1_health_summary"])
        else:
            st.info("Periodic report not available yet.")
    with out2:
        st.markdown("##### 2) Failure Estimation")
        if report:
            st.json(report["output_2_failure_estimation"])
        else:
            st.json({
                "machine_id": selected_machine,
                "realtime_failure_probability": round(realtime_fp, 4),
                "estimated_status": failure_label(realtime_fp),
                "anomaly_score": round(feature["anomaly_score"], 2),
                "degradation_score": round(feature["degradation_score"], 2),
            })
    with out3:
        st.markdown("##### 3) Action Plan")
        if report:
            st.json(report["output_3_action_plan"])
        else:
            temp_signals = dominant_signals(feature, st.session_state.thresholds)
            temp_deg = degradation_level(feature["degradation_score"])
            temp_rec = recommendation(feature, realtime_fp, temp_deg, temp_signals)
            st.json({
                "machine_id": selected_machine,
                "priority": risk_level(realtime_fp),
                "recommendation": temp_rec,
                "maintenance_window": maintenance_window(realtime_fp),
            })

    # Realtime Alert Detail
    st.markdown("### Realtime Alert Detail")
    if alert:
        st.error(
            f"🚨 {alert['alert_level']} | Failure Probability: {alert['failure_probability'] * 100:.2f}% | {alert['conclusion']}"
        )
        st.markdown("**Trigger Reasons:**")
        for reason in alert["trigger_reasons"]:
            st.markdown(f"- {reason}")
        st.markdown("**Immediate Actions:**")
        for action in alert["immediate_actions"]:
            st.markdown(f"- {action}")
    else:
        st.success("No realtime alert for this motor.")

    # Trend Charts
    st.markdown("### Realtime Trend")
    history_df = get_machine_history_df(selected_machine)
    if not history_df.empty:
        history_df = history_df.copy()
        history_df["timestamp"] = pd.to_datetime(history_df["timestamp"])
        history_df["timestamp_str"] = history_df["timestamp"].dt.strftime("%H:%M:%S")

        col_left, col_right = st.columns(2)
        with col_left:
            st.plotly_chart(
                px.line(history_df, x="timestamp", y="temperature", title="Temperature Trend",
                        color_discrete_sequence=["#3b82f6"]),
                use_container_width=True,
                key="motor_temp_trend"
            )
            st.plotly_chart(
                px.line(history_df, x="timestamp", y="current", title="Current Trend",
                        color_discrete_sequence=["#06b6d4"]),
                use_container_width=True,
                key="motor_current_trend"
            )
            st.plotly_chart(
                px.line(history_df, x="timestamp", y="voltage", title="Voltage Trend",
                        color_discrete_sequence=["#8b5cf6"]),
                use_container_width=True,
                key="motor_voltage_trend"
            )
        with col_right:
            st.plotly_chart(
                px.line(history_df, x="timestamp", y="vibration", title="Vibration Trend",
                        color_discrete_sequence=["#ffd700"]),
                use_container_width=True,
                key="motor_vibration_trend"
            )
            st.plotly_chart(
                px.line(history_df, x="timestamp", y="pressure", title="Pressure Trend",
                        color_discrete_sequence=["#ff8c00"]),
                use_container_width=True,
                key="motor_pressure_trend"
            )
            st.plotly_chart(
                px.line(history_df, x="timestamp", y="rpm", title="RPM Trend",
                        color_discrete_sequence=["#00ff88"]),
                use_container_width=True,
                key="motor_rpm_trend"
            )

        # Historical Data Table
        st.markdown("### Historical Sensor Data")
        st.dataframe(history_df.tail(50), use_container_width=True, hide_index=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- PERIODIC REPORTS ---
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title"><span class="title-accent"></span> Periodic Reports</div>', unsafe_allow_html=True)
filtered_reports = [
    report for report in st.session_state.periodic_reports
    if report["machine_id"] in available_machines and report["risk_level"] in selected_risk_levels
]
if filtered_reports:
    report_options = [
        f"{r['analysis_time'].strftime('%Y-%m-%d %H:%M:%S')} | {r['machine_id']}"
        for r in filtered_reports
    ]
    selected_report_label = st.selectbox("Select report", report_options, key="periodic_report_select")
    selected_idx = report_options.index(selected_report_label)
    chosen_report = filtered_reports[selected_idx]

    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        st.markdown("##### Output 1 - Health Summary")
        st.json(chosen_report["output_1_health_summary"])
    with rc2:
        st.markdown("##### Output 2 - Failure Estimation")
        st.json(chosen_report["output_2_failure_estimation"])
    with rc3:
        st.markdown("##### Output 3 - Action Plan")
        st.json(chosen_report["output_3_action_plan"])
else:
    st.info("No periodic report available for the current filters.")
st.markdown('</div>', unsafe_allow_html=True)

# --- ALERT LOG ---
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-title"><span class="title-accent"></span> Alert Log</div>', unsafe_allow_html=True)
filtered_alerts = [
    a for a in st.session_state.alert_log
    if a["machine_id"] in available_machines and a["alert_level"] in selected_risk_levels
]
if filtered_alerts:
    alert_rows = []
    for alert_item in filtered_alerts[:30]:
        alert_rows.append({
            "time": alert_item["alert_time"],
            "machine_id": alert_item["machine_id"],
            "level": alert_item["alert_level"],
            "failure_probability_%": round(alert_item["failure_probability"] * 100, 2),
            "conclusion": alert_item["conclusion"],
            "triggers": " | ".join(alert_item["trigger_reasons"]),
        })
    st.dataframe(pd.DataFrame(alert_rows), use_container_width=True, hide_index=True)
else:
    st.success("No alert log for the current filters.")
st.markdown('</div>', unsafe_allow_html=True)

# --- DATASET INSPECTION ---
if show_dataset:
    df, dataset_name = load_cleaned_dataset()
    show_dataset_inspection(df, dataset_name)

# =========================================================
# AUTO REFRESH
# =========================================================
if st.session_state.running and st.session_state.auto_refresh:
    time.sleep(st.session_state.refresh_interval)
    st.rerun()

