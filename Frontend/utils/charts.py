"""
Charts module - reusable Plotly chart functions for the dashboard.
"""
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


def gauge_chart(value, title, max_value=100, suffix="", color_scheme=None):
    """Professional gauge chart with threshold coloring."""
    if color_scheme is None:
        color_scheme = [
            (0.35, "#00ff88"),
            (0.60, "#ffd700"),
            (0.80, "#ff8c00"),
            (1.00, "#ff4444"),
        ]

    steps = []
    prev_pct = 0
    for pct, color in color_scheme:
        steps.append({"range": [prev_pct * max_value, pct * max_value], "color": color})
        prev_pct = pct

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            number={
                "suffix": suffix,
                "font": {"size": 36, "color": "#f8fafc"},
            },
            title={
                "text": title,
                "font": {"size": 14, "color": "#94a3b8"},
            },
            gauge={
                "axis": {
                    "range": [0, max_value],
                    "tickwidth": 1,
                    "tickcolor": "#475569",
                    "tickfont": {"size": 10, "color": "#94a3b8"},
                },
                "bar": {"thickness": 0.4, "color": "#3b82f6"},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": steps,
                "threshold": {
                    "line": {"color": "#ef4444", "width": 3},
                    "thickness": 0.75,
                    "value": max_value * 0.85,
                },
            },
        )
    )
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f8fafc"},
    )
    return fig


def professional_line_chart(df, x, y, title, color="#3b82f6"):
    """Professional styled line chart."""
    fig = px.line(
        df, x=x, y=y, title=title,
        color_discrete_sequence=[color],
        template="plotly_dark",
    )
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#cbd5e1", "size": 11},
        xaxis={"gridcolor": "rgba(148,163,184,0.1)", "zeroline": False},
        yaxis={"gridcolor": "rgba(148,163,184,0.1)", "zeroline": False},
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_traces(line=dict(width=2), hovertemplate="%{y:.2f}")
    return fig


def professional_bar_chart(df, x, y, title, color="#3b82f6"):
    """Professional styled bar chart."""
    fig = px.bar(
        df, x=x, y=y, title=title,
        color_discrete_sequence=[color],
        template="plotly_dark",
    )
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#cbd5e1", "size": 11},
        xaxis={"gridcolor": "rgba(148,163,184,0.1)", "zeroline": False},
        yaxis={"gridcolor": "rgba(148,163,184,0.1)", "zeroline": False},
        hovermode="x unified",
        showlegend=False,
    )
    return fig


def professional_pie_chart(df, names, values, title):
    """Professional styled pie chart."""
    fig = px.pie(
        df, names=names, values=values, title=title,
        template="plotly_dark",
        color_discrete_sequence=["#00ff88", "#ffd700", "#ff8c00", "#ff4444"],
    )
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#cbd5e1", "size": 11},
        showlegend=True,
        legend={"font": {"color": "#cbd5e1", "size": 10}},
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label}<br>%{value} (%{percent})",
    )
    return fig

