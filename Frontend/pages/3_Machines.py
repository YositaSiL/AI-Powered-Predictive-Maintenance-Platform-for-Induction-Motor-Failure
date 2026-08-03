"""
Machines Page - Equipment inventory, search, filter, and status.
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Frontend.utils.db_connection import load_dashboard_data

st.set_page_config(page_title="Machines - Predictive Maintenance", layout="wide")

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
        <div class="hero-title">Machine Inventory</div>
        <div class="hero-subtitle">Asset health monitoring and equipment management</div>
    </div>
    """,
    unsafe_allow_html=True,
)

df, source = load_dashboard_data()

if df.empty:
    st.warning("No machine data available.")
    st.stop()

# Filters
st.markdown("### Filters")
col1, col2, col3 = st.columns(3)
with col1:
    motor_options = sorted(df["motor_id"].astype(str).unique().tolist())
    selected_motor = st.selectbox("Select Motor", ["All"] + motor_options)
with col2:
    search_term = st.text_input("Search Machine ID", placeholder="Type to search...")
with col3:
    if "risk_level" in df.columns:
        risk_options = sorted(df["risk_level"].dropna().astype(str).unique().tolist())
        selected_risk = st.multiselect("Risk Level", options=risk_options, default=risk_options)

# Apply filters
filtered_df = df.copy()
if selected_motor != "All":
    filtered_df = filtered_df[filtered_df["motor_id"].astype(str) == selected_motor]
if search_term:
    filtered_df = filtered_df[filtered_df["motor_id"].astype(str).str.contains(search_term, case=False)]
if "risk_level" in filtered_df.columns and selected_risk:
    filtered_df = filtered_df[filtered_df["risk_level"].isin(selected_risk)]

# KPI Summary
healthy_count = len(filtered_df[filtered_df["risk_level"] == "LOW"]) if "risk_level" in filtered_df.columns else 0
warning_count = len(filtered_df[filtered_df["risk_level"] == "MEDIUM"]) if "risk_level" in filtered_df.columns else 0
critical_count = len(filtered_df[filtered_df["risk_level"].isin(["HIGH", "CRITICAL"])]) if "risk_level" in filtered_df.columns else 0

kpi_c = st.columns(4)
kpi_c[0].markdown(
    f'<div class="metric-card info"><div class="metric-title">Total Motors</div><div class="metric-value">{filtered_df["motor_id"].nunique()}</div><div class="metric-sub">Monitored assets</div></div>',
    unsafe_allow_html=True,
)
kpi_c[1].markdown(
    f'<div class="metric-card healthy"><div class="metric-title">Healthy</div><div class="metric-value">{healthy_count}</div><div class="metric-sub">Low risk</div></div>',
    unsafe_allow_html=True,
)
kpi_c[2].markdown(
    f'<div class="metric-card warning"><div class="metric-title">Warning</div><div class="metric-value">{warning_count}</div><div class="metric-sub">Medium risk</div></div>',
    unsafe_allow_html=True,
)
kpi_c[3].markdown(
    f'<div class="metric-card critical"><div class="metric-title">Critical</div><div class="metric-value">{critical_count}</div><div class="metric-sub">High/Critical risk</div></div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# Risk Distribution
if "risk_level" in filtered_df.columns:
    left, right = st.columns([1, 1])
    with left:
        st.markdown("### Risk Distribution")
        risk_df = filtered_df["risk_level"].value_counts().reset_index()
        risk_df.columns = ["Risk Level", "Count"]
        fig = px.pie(risk_df, names="Risk Level", values="Count",
                    color_discrete_sequence=["#00ff88", "#ffd700", "#ff8c00", "#ff4444"])
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font={"color": "#cbd5e1"})
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### Top Critical Equipment")
        if "failure_probability" in filtered_df.columns:
            critical_df = filtered_df.sort_values("failure_probability", ascending=False).head(10)
            columns = [c for c in ["motor_id", "health_score", "failure_probability", "rul", "risk_level"] if c in critical_df.columns]
            st.dataframe(critical_df[columns], use_container_width=True, hide_index=True)

st.markdown("---")

# Equipment Inventory Table
st.markdown("### Equipment Inventory")
visible_columns = [
    col for col in [
        "motor_id", "type", "air_temperature", "process_temperature",
        "rotation_speed", "torque", "tool_wear", "vibration",
        "electrical_current", "pressure", "rul", "health_score",
        "failure_probability", "risk_level", "status",
    ] if col in filtered_df.columns
]
st.dataframe(filtered_df[visible_columns], use_container_width=True, hide_index=True)

st.markdown("---")

# Equipment Cards
st.markdown("### Equipment Overview")
card_df = filtered_df.copy()
if "failure_probability" in card_df.columns:
    card_df = card_df.sort_values("failure_probability", ascending=False)

for _, row in card_df.head(12).iterrows():
    with st.container():
        a, b, c = st.columns([2, 1, 1])
        with a:
            risk = row.get("risk_level", "N/A")
            badge_class = "critical" if risk in ["HIGH", "CRITICAL"] else "warning" if risk == "MEDIUM" else "healthy"
            st.markdown(
                f"""
                <div class="asset-card" style="border-left-color:{'#ff4444' if risk in ['HIGH','CRITICAL'] else '#ffd700' if risk=='MEDIUM' else '#00ff88'};">
                    <div class="asset-title">{row.get('motor_id', '-')}</div>
                    <div class="asset-text">
                        Type: {row.get('type', '-')} |
                        <span class="status-badge {badge_class}">{risk}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
        with b:
            if "health_score" in row and pd.notna(row["health_score"]):
                st.metric("Health Score", f"{row['health_score']:.1f}")
        with c:
            if "rul" in row and pd.notna(row["rul"]):
                st.metric("RUL", f"{row['rul']:.0f} Days")
        st.divider()

st.info(f"Showing {len(filtered_df)} records from {filtered_df['motor_id'].nunique()} motors.")

