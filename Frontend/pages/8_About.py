"""
About Page - Project information, architecture, and technology stack.
"""
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(page_title="About - Predictive Maintenance", layout="wide")

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
        <div class="hero-title">About the Platform</div>
        <div class="hero-subtitle">AI-Powered Predictive Maintenance Platform for Induction Motor Failure</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Project Overview
st.markdown("## Project Overview")
st.markdown(
    """
    <div class="section-card">
        An Intelligent On-Premise Predictive Maintenance Platform that continuously learns from operational data,
    predicts induction motor failures before they occur, and provides actionable maintenance recommendations
    through flexible industrial connectivity and dynamic machine learning capabilities.
    </div>
    """,
    unsafe_allow_html=True,
)

# Business Problem & Solution
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Business Problem")
    st.markdown(
        """
        <div class="section-card">
            <ul style="color: #cbd5e1;">
                <li>Current machine monitoring systems detect issues only after signs of degradation have already appeared</li>
                <li>Relying solely on individual thresholds is no longer sufficient in complex systems</li>
                <li>Need for multiple operating parameter analysis</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown("### Expected Impact")
    st.markdown(
        """
        <div class="section-card">
            <ul style="color: #cbd5e1;">
                <li>Earlier detection of potential equipment failures</li>
                <li>Reduced unplanned downtime and maintenance costs</li>
                <li>Lower false alarm rates</li>
                <li>Improved maintenance scheduling through RUL predictions</li>
                <li>Increased equipment reliability and efficiency</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# Architecture
st.markdown("## System Architecture")
st.markdown(
    """
    <div class="section-card">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div class="metric-card info" style="text-align:center;">
                <div class="metric-title">Frontend</div>
                <div class="metric-sub">Streamlit<br>Plotly Charts<br>Interactive Dashboard</div>
            </div>
            <div class="metric-card info" style="text-align:center;">
                <div class="metric-title">Backend API</div>
                <div class="metric-sub">FastAPI<br>RESTful Endpoints<br>Real-time Monitoring</div>
            </div>
            <div class="metric-card info" style="text-align:center;">
                <div class="metric-title">ML Engine</div>
                <div class="metric-sub">Random Forest<br>Health Scoring<br>RUL Estimation</div>
            </div>
            <div class="metric-card info" style="text-align:center;">
                <div class="metric-title">Database</div>
                <div class="metric-sub">PostgreSQL<br>SQLite Fallback<br>Time-series Data</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Technology Stack
st.markdown("## Technology Stack")

tech_stack = {
    "Python": "Core programming language",
    "Streamlit": "Interactive dashboard and UI framework",
    "Plotly": "Professional charts and visualizations",
    "Pandas": "Data manipulation and analysis",
    "Scikit-Learn": "Random Forest ML model",
    "FastAPI": "High-performance backend API",
    "Joblib": "Model persistence and loading",
    "PostgreSQL": "Primary database",
    "SQLAlchemy": "ORM and database connectivity",
    "Uvicorn": "ASGI server for FastAPI",
}

tech_cols = st.columns(2)
for idx, (tech, desc) in enumerate(tech_stack.items()):
    with tech_cols[idx % 2]:
        st.markdown(
            f"""
            <div class="asset-card" style="border-left-color: #3b82f6;">
                <div class="asset-title">{tech}</div>
                <div class="asset-text">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

# Dataset
st.markdown("## Dataset")
st.markdown(
    """
    <div class="section-card">
        <p style="color: #cbd5e1;">
            The platform uses the Astra Case dataset containing operational data from induction motors,
        including temperature, vibration, current, pressure, and other sensor readings. The dataset
        includes machine failure labels for supervised learning.
        </p>
        <div style="display: flex; gap: 1rem; margin-top: 1rem;">
            <span class="hero-badge blue">10000+ Records</span>
            <span class="hero-badge green">10+ Features</span>
            <span class="hero-badge yellow">Multiple Machine Types</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# ML Model
st.markdown("## Machine Learning Model")
st.markdown(
    """
    <div class="section-card">
        <div style="color: #cbd5e1;">
            <p><strong>Algorithm:</strong> Random Forest Classifier</p>
            <p><strong>Features:</strong> Air Temperature, Process Temperature, Rotational Speed, Torque, Tool Wear, Pressure, Vibration, Electrical Current</p>
            <p><strong>Output:</strong> Failure Probability (0-1), Health Score (0-100), Risk Level (LOW/MEDIUM/HIGH/CRITICAL)</p>
            <p><strong>Additional Engines:</strong> Health Scoring Engine, RUL Estimation, Trend Analysis</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Developer Info
st.markdown("## Developer Information")
st.markdown(
    """
    <div class="section-card">
        <div style="color: #cbd5e1;">
            <p><strong>Project:</strong> AI-Powered Predictive Maintenance Platform for Induction Motor Failure</p>
            <p><strong>Version:</strong> 1.0.0</p>
            <p><strong>Technology Stack:</strong> Python, Streamlit, FastAPI, Scikit-Learn, PostgreSQL</p>
            <p><strong>Target Industry:</strong> Automotive Manufacturing - Astra Otoparts</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

