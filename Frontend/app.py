import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.app.health_engine import calculate_health_score
from Backend.app.models.ml_model import model
from Frontend.utils.db_connection import load_dashboard_data

st.set_page_config(page_title="WINTEQ | Astra Otoparts Bootcamp Briefing", page_icon="⚙️", layout="wide")

CSS_PATH = Path(__file__).resolve().parent / "styles" / "streamlit.css"
if CSS_PATH.exists():
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def build_dashboard_frame(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    for col in [
        "air_temperature",
        "process_temperature",
        "rotation_speed",
        "torque",
        "tool_wear",
        "pressure",
        "vibration",
        "electrical_current",
    ]:
        if col not in df.columns:
            df[col] = np.nan

    if "product_id" in df.columns and "motor_id" not in df.columns:
        df["motor_id"] = df["product_id"]
    if "motor_id" not in df.columns:
        df["motor_id"] = [f"M{i:03d}" for i in range(1, len(df) + 1)]
    if "type" not in df.columns:
        df["type"] = "INDUCTION"

    feature_cols = [
        "air_temperature",
        "process_temperature",
        "rotation_speed",
        "torque",
        "tool_wear",
        "pressure",
        "vibration",
        "electrical_current",
    ]
    feature_frame = df[feature_cols].copy().fillna(0)

    try:
        probs = model.predict_proba(feature_frame)[:, 1]
    except Exception:
        probs = np.zeros(len(df))

    df["failure_probability"] = np.clip(probs, 0.0, 1.0)
    df["health_score"] = [
        calculate_health_score(
            row.get("air_temperature", 0),
            row.get("vibration", 0),
            row.get("electrical_current", 0),
            row.get("pressure", 0),
            row.get("rotation_speed", 0),
        )
        for _, row in df.iterrows()
    ]
    df["health_score"] = pd.to_numeric(df["health_score"], errors="coerce").fillna(0)

    if "rul" in df.columns:
        df["rul"] = pd.to_numeric(df["rul"], errors="coerce").fillna(0)
    else:
        df["rul"] = np.maximum(50, 1000 - (df["failure_probability"] * 700)).astype(int)

    df["risk_level"] = np.select(
        [df["failure_probability"] >= 0.8, df["failure_probability"] >= 0.6, df["failure_probability"] >= 0.35],
        ["CRITICAL", "HIGH", "MEDIUM"],
        default="LOW",
    )
    df["status"] = np.select(
        [df["rul"] <= 180, df["rul"] <= 420],
        ["Critical", "Warning"],
        default="Healthy",
    )
    df["maintenance_recommendation"] = df.apply(
        lambda row: (
            "Immediate shutdown and inspection"
            if row["failure_probability"] >= 0.8
            else "Schedule predictive maintenance within 24 hours"
            if row["failure_probability"] >= 0.6
            else "Continue routine monitoring"
        ),
        axis=1,
    )
    return df


@st.cache_data(show_spinner=False)
def load_view_data():
    raw_df, source = load_dashboard_data()
    frame = build_dashboard_frame(raw_df)
    return frame, source


frame, source = load_view_data()

if frame.empty:
    st.error("No data is available to display.")
    st.stop()

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">WINTEQ | ASTRA OTOPARTS BOOTCAMP BRIEFING</div>
        <div class="hero-subtitle">July 2026 · Engineering Solution Center · Industrial Intelligence and Flexible Automation</div>
        <div class="hero-badges">
            <span class="badge badge-green">Data Source: {source}</span>
            <span class="badge badge-yellow">AI-driven platform</span>
            <span class="badge badge-red">Enterprise-ready</span>
        </div>
    </div>
    """.format(source=source.upper()),
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("<div class='sidebar-card'><div class='section-title'>Control Center</div><div class='asset-text'>Filter the operating dataset and focus on the relevant use case.</div></div>", unsafe_allow_html=True)

    type_options = sorted(frame["type"].dropna().astype(str).unique().tolist()) if "type" in frame.columns else []
    selected_types = st.multiselect("Filter Motor Type", options=type_options, default=type_options)
    if selected_types:
        frame = frame[frame["type"].astype(str).isin(selected_types)].copy()

    st.markdown("---")
    st.metric("Motors loaded", len(frame))
    st.metric("Average health", f"{frame['health_score'].mean():.1f}")
    st.metric("Average failure probability", f"{frame['failure_probability'].mean() * 100:.1f}%")
    st.metric("Critical risk", int((frame["risk_level"] == "CRITICAL").sum()))

    st.markdown("---")
    st.info("When PostgreSQL is unavailable, the system automatically uses the local CSV and SQLite fallback.")

if frame.empty:
    st.warning("No records match the current filter.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='metric-card'><div class='metric-title'>Total motors</div><div class='metric-value'>{len(frame)}</div><div class='metric-sub'>Assets in view</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-card'><div class='metric-title'>Fleet health</div><div class='metric-value'>{frame['health_score'].mean():.1f}</div><div class='metric-sub'>Condition index</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card'><div class='metric-title'>Failure probability</div><div class='metric-value'>{frame['failure_probability'].mean() * 100:.1f}%</div><div class='metric-sub'>Estimated risk exposure</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='metric-card'><div class='metric-title'>Critical risk</div><div class='metric-value'>{int((frame['risk_level'] == 'CRITICAL').sum())}</div><div class='metric-sub'>Priority actions</div></div>", unsafe_allow_html=True)

st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Executive Overview</div>", unsafe_allow_html=True)
left, right = st.columns([1.25, 0.9])

with left:
    fig_health = px.scatter(
        frame,
        x="rotation_speed" if "rotation_speed" in frame.columns else "air_temperature",
        y="health_score",
        color="risk_level",
        size="failure_probability",
        hover_data=["motor_id", "type", "rul", "failure_probability"],
        title="Asset Condition vs Operating Profile"
    )
    fig_health.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_health, use_container_width=True)

with right:
    critical_assets = frame.sort_values("failure_probability", ascending=False).head(6)
    st.markdown("<div class='section-title' style='font-size:16px'>Critical Attention</div>", unsafe_allow_html=True)
    for _, row in critical_assets.iterrows():
        st.markdown(
            f"<div class='asset-card'><div class='asset-title'>{row['motor_id']}</div><div class='asset-text'>Risk: {row['risk_level']} · RUL: {int(row['rul'])} · {row['maintenance_recommendation']}</div></div>",
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Fleet Trend and Risk Distribution</div>", unsafe_allow_html=True)
trend_col, risk_col = st.columns([1.25, 0.75])

with trend_col:
    trend_df = pd.DataFrame({
        "index": range(min(20, len(frame))),
        "health_score": frame.sort_values("health_score").head(min(20, len(frame))) ["health_score"].values if len(frame) > 0 else []
    })
    if not trend_df.empty:
        fig_trend = px.line(trend_df, x="index", y="health_score", markers=True, title="Fleet Health Trend")
        fig_trend.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_trend, use_container_width=True)

with risk_col:
    risk_summary = frame.groupby("risk_level").size().reset_index(name="count")
    fig_risk = px.pie(risk_summary, names="risk_level", values="count", hole=0.5, title="Risk Distribution")
    fig_risk.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_risk, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

analytics_tab, alerts_tab = st.tabs(["Use Cases", "Alert Intelligence"])

with analytics_tab:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Use Case 1: Camera AI - Dynamic Software</div>", unsafe_allow_html=True)
    st.markdown("<div class='asset-text'>A modular and configuration-driven platform that enables rapid deployment of customer-specific machine vision workflows without routine code changes.</div>", unsafe_allow_html=True)
    st.markdown("<div class='asset-text'>• Modular workflow architecture</div>", unsafe_allow_html=True)
    st.markdown("<div class='asset-text'>• Configuration-driven setup</div>", unsafe_allow_html=True)
    st.markdown("<div class='asset-text'>• Template management for multiple inspection scenarios</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Use Case 2: Predictive Maintenance for Induction Motor Failure</div>", unsafe_allow_html=True)
    st.markdown("<div class='asset-text'>An AI-based predictive maintenance solution that continuously learns from historical and real-time machine data to estimate failure risk and support proactive maintenance planning.</div>", unsafe_allow_html=True)
    st.markdown("<div class='asset-text'>• Multi-parameter monitoring across temperature, vibration, current, pressure, and speed</div>", unsafe_allow_html=True)
    st.markdown("<div class='asset-text'>• Remaining Useful Life estimation</div>", unsafe_allow_html=True)
    st.markdown("<div class='asset-text'>• Real-time health scoring with maintenance recommendations</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with alerts_tab:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Priority Recommendations</div>", unsafe_allow_html=True)
    top_risk = frame.sort_values("failure_probability", ascending=False).head(8)
    for _, row in top_risk.iterrows():
        st.markdown(
            f"<div class='asset-card'><div class='asset-title'>{row['motor_id']}</div><div class='asset-text'>Risk: {row['risk_level']} · RUL: {int(row['rul'])} · {row['maintenance_recommendation']}</div></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Operational Insight</div>", unsafe_allow_html=True)
    selected_motor = st.selectbox("Select motor", frame["motor_id"].astype(str).tolist())
    motor_view = frame[frame["motor_id"].astype(str) == selected_motor].iloc[0:1]
    if not motor_view.empty:
        st.json({
            "motor_id": selected_motor,
            "status": motor_view["status"].iloc[0],
            "health_score": round(float(motor_view["health_score"].iloc[0]), 2),
            "failure_probability": round(float(motor_view["failure_probability"].iloc[0]), 4),
            "rul": int(motor_view["rul"].iloc[0]),
            "recommendation": motor_view["maintenance_recommendation"].iloc[0],
        })
    st.markdown("</div>", unsafe_allow_html=True)