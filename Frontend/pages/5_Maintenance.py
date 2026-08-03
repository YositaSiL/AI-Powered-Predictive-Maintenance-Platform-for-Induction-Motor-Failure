"""
Maintenance Page - Maintenance scheduling, task tracking, and recommendations.
"""
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Frontend.utils.db_connection import load_dashboard_data

st.set_page_config(page_title="Maintenance - Predictive Maintenance", layout="wide")

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
        <div class="hero-title">Maintenance Management</div>
        <div class="hero-subtitle">Schedule and track maintenance tasks, view recommendations</div>
        <div class="hero-badges">
            <span class="hero-badge green">● Active Schedule</span>
            <span class="hero-badge blue">● Task Management</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

df, source = load_dashboard_data()

# Generate maintenance tasks based on dataset analysis
maintenance_tasks = []
if not df.empty and "motor_id" in df.columns and "rul" in df.columns:
    for _, row in df.iterrows():
        motor_id = str(row.get("motor_id", "Unknown"))
        rul = row.get("rul", 30)
        health = row.get("health_score", 50)
        failure_prob = row.get("failure_probability", 0)

        # Standardisasi persentase failure (jika 0.x, ubah ke persentase utuh)
        fp_percent = failure_prob * 100 if failure_prob <= 1.0 else failure_prob

        if isinstance(rul, (int, float)):
            # [PERBAIKAN 4] Priority berdasarkan AI (Failure Prob, Health, RUL)
            if fp_percent >= 80 or rul < 5:
                priority = "CRITICAL"
                task = "Immediate replacement required"
                rec_actions = ["✓ Immediate Motor Replacement", "✓ Cut off power supply", "✓ Notify Plant Manager"]
            elif fp_percent >= 60 or rul < 15:
                priority = "HIGH"
                task = "Inspect and service motor"
                rec_actions = ["✓ Inspect Bearing", "✓ Check Lubrication", "✓ Reduce Load", "✓ Schedule Maintenance"]
            elif fp_percent >= 30 or rul < 30:
                priority = "MEDIUM"
                task = "Plan preventive maintenance"
                rec_actions = ["✓ Vibration Analysis", "✓ Thermal Inspection", "✓ Clean Housing"]
            else:
                priority = "LOW"
                task = "Routine check"
                rec_actions = ["✓ Visual Inspection", "✓ Routine check"]

            # [PERBAIKAN 1 & 10] Status Maintenance mengikuti mesin + Warna
            if priority == "CRITICAL":
                status = "🔴 Pending"
            elif priority == "HIGH":
                status = "🟡 In Progress"
            elif priority == "MEDIUM":
                status = "🔵 Scheduled"
            else:
                status = "🟢 Completed"

            # [PERBAIKAN 6] Engineer Assignment Realistis
            if priority == "CRITICAL":
                engineer = "Senior Engineer"
            elif priority == "HIGH":
                engineer = "Maintenance Engineer"
            elif priority == "MEDIUM":
                engineer = "Technician"
            else:
                engineer = "Junior Technician"

            # [PERBAIKAN 5] Scheduled Date Realistis
            now = datetime.now()
            if priority == "CRITICAL":
                due_date = now
            elif priority == "HIGH":
                due_date = now + timedelta(days=random.randint(1, 3))
            elif priority == "MEDIUM":
                due_date = now + timedelta(days=7)
            else:
                due_date = now + timedelta(days=random.randint(14, 28))

            # [PERBAIKAN 9] Kolom Tabel Lebih Informatif
            maintenance_tasks.append({
                "Motor": motor_id,
                "Health": round(health, 1) if isinstance(health, (int, float)) else health,
                "Failure": round(fp_percent, 1) if isinstance(fp_percent, (int, float)) else fp_percent,
                "RUL": round(rul, 1) if isinstance(rul, (int, float)) else rul,
                "Priority": priority,
                "Status": status,
                "Engineer": engineer,
                "Due Date": due_date.strftime("%Y-%m-%d"),
                "Task": task, # Disimpan untuk kompatibilitas data
                "Recommendations": rec_actions # Disimpan untuk kartu bawah
            })

# Convert to DataFrame
task_df = pd.DataFrame(maintenance_tasks)

if not task_df.empty:
    # Filters
    st.markdown("### Filters")
    col1, col2 = st.columns(2)
    with col1:
        priority_filter = st.multiselect("Priority", ["CRITICAL", "HIGH", "MEDIUM", "LOW"], default=["CRITICAL", "HIGH", "MEDIUM", "LOW"])
    with col2:
        # Menyesuaikan filter dengan format warna status yang baru
        status_filter = st.multiselect("Status", ["🔴 Pending", "🟡 In Progress", "🔵 Scheduled", "🟢 Completed"], default=["🔴 Pending", "🟡 In Progress", "🔵 Scheduled", "🟢 Completed"])

    # [PERBAIKAN 2] Filter Status Aktif Berfungsi
    filtered_df = task_df[
        (task_df["Priority"].isin(priority_filter)) & 
        (task_df["Status"].isin(status_filter))
    ]

    # [PERBAIKAN 3] KPI Metrik Diperbaiki
    total_tasks = len(filtered_df)
    pending_count = len(filtered_df[filtered_df["Status"] == "🔴 Pending"])
    in_progress_count = len(filtered_df[filtered_df["Status"] == "🟡 In Progress"])
    completed_count = len(filtered_df[filtered_df["Status"] == "🟢 Completed"])

    kpi_c = st.columns(4)
    kpi_c[0].markdown(
        f'<div class="metric-card healthy"><div class="metric-title">Total Tasks</div><div class="metric-value">{total_tasks}</div><div class="metric-sub">All filtered tasks</div></div>',
        unsafe_allow_html=True,
    )
    kpi_c[1].markdown(
        f'<div class="metric-card critical"><div class="metric-title">Pending</div><div class="metric-value">{pending_count}</div><div class="metric-sub">Immediate actions</div></div>',
        unsafe_allow_html=True,
    )
    kpi_c[2].markdown(
        f'<div class="metric-card warning"><div class="metric-title">In Progress</div><div class="metric-value">{in_progress_count}</div><div class="metric-sub">Currently worked on</div></div>',
        unsafe_allow_html=True,
    )
    kpi_c[3].markdown(
        f'<div class="metric-card healthy"><div class="metric-title">Completed</div><div class="metric-value">{completed_count}</div><div class="metric-sub">Finished tasks</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # [PERBAIKAN 8] Maintenance Summary
    today_str = datetime.now().strftime("%Y-%m-%d")
    sch_today = len(filtered_df[filtered_df["Due Date"] == today_str])
    sch_overdue = len(filtered_df[(filtered_df["Due Date"] < today_str) & (filtered_df["Status"] != "🟢 Completed")])
    sch_upcoming = len(filtered_df[filtered_df["Due Date"] > today_str])

    st.markdown("### Today's Schedule")
    sum_c1, sum_c2, sum_c3, sum_c4 = st.columns(4)
    sum_c1.info(f"📅 **Pending (Today)**: {sch_today}")
    sum_c2.warning(f"⏳ **In Progress (Upcoming)**: {sch_upcoming}")
    sum_c3.error(f"🚨 **Overdue**: {sch_overdue}")
    sum_c4.success(f"✅ **Completed**: {completed_count}")
    
    st.markdown("---")

    # Task Priority Distribution
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### Priority Distribution")
        priority_counts = filtered_df["Priority"].value_counts().reset_index()
        priority_counts.columns = ["Priority", "Count"]
        fig = px.bar(priority_counts, x="Priority", y="Count", title="Tasks by Priority",
                    color="Priority",
                    color_discrete_map={"CRITICAL": "#ff4444", "HIGH": "#ff8c00", "MEDIUM": "#ffd700", "LOW": "#00ff88"})
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font={"color": "#cbd5e1"})
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("### Maintenance Schedule")
        schedule_df = filtered_df.groupby("Due Date").size().reset_index(name="Tasks")
        schedule_df = schedule_df.sort_values(by="Due Date")
        fig = px.line(schedule_df, x="Due Date", y="Tasks", title="Upcoming Tasks", markers=True,
                     color_discrete_sequence=["#3b82f6"])
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font={"color": "#cbd5e1"})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Maintenance Tasks Table
    st.markdown("### Maintenance Tasks")
    # Color-code priority
    def highlight_priority(val):
        if val == "CRITICAL":
            return "color: #ff4444; font-weight: 700"
        elif val == "HIGH":
            return "color: #ff8c00; font-weight: 600"
        elif val == "MEDIUM":
            return "color: #ffd700"
        return "color: #00ff88"

    # Menyembunyikan kolom internal untuk tampilan tabel agar rapi
    display_df = filtered_df.drop(columns=["Task", "Recommendations"])
    styled_task = display_df.style.map(highlight_priority, subset=["Priority"])
    st.dataframe(styled_task, use_container_width=True, hide_index=True)

    # Export
    csv_data = filtered_df.drop(columns=["Recommendations"]).to_csv(index=False).encode("utf-8")
    st.download_button("📥 Export Maintenance Tasks", data=csv_data, file_name="maintenance_tasks.csv", mime="text/csv", use_container_width=True)

    st.markdown("---")

    # [PERBAIKAN 7] Recommendation Card dengan Checklist
    st.markdown("### Maintenance Recommendations")
    rec_df = filtered_df[filtered_df["Priority"].isin(["CRITICAL", "HIGH"])].head(10)
    
    if not rec_df.empty:
        for _, row in rec_df.iterrows():
            badge_class = "critical" if row["Priority"] == "CRITICAL" else "warning"
            border_color = "#ff4444" if row['Priority'] == 'CRITICAL' else '#ff8c00'
            
            # Membangun string checklist dari list rekomendasi
            checklist_html = "".join([f"<div style='margin-left: 15px; color: #a8b2d1;'>{item}</div>" for item in row['Recommendations']])
            
            st.markdown(
                f"""
                <div class="asset-card" style="border-left-color:{border_color}; margin-bottom: 15px;">
                    <div class="asset-title">{row['Motor']}</div>
                    <div style="margin-top: 8px; margin-bottom: 8px;">
                        <span class="status-badge {badge_class}">{row['Priority']}</span>
                        <span style="color: #cbd5e1; margin-left: 10px; font-size: 14px;">Engineer: {row['Engineer']} | Due: {row['Due Date']}</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <strong style="color: #e2e8f0; font-size: 14px;">Recommended Action:</strong>
                        {checklist_html}
                    </div>
                </div>
                """, unsafe_allow_html=True,
            )
    else:
        st.success("No Critical or High priority tasks at the moment.")

else:
    st.info("No maintenance data available.")