"""
Reusable HTML component library for the Predictive Maintenance Platform.
Provides styled HTML components for consistent industrial UI across all pages.
"""
from datetime import datetime


def sidebar_logo():
    """Brand logo for sidebar."""
    return """
    <div class="sidebar-logo">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none" style="margin-bottom:6px;">
            <rect width="40" height="40" rx="10" fill="url(#logo_grad)"/>
            <defs>
                <linearGradient id="logo_grad" x1="0" y1="0" x2="40" y2="40">
                    <stop offset="0%" stop-color="#3b82f6"/>
                    <stop offset="100%" stop-color="#06b6d4"/>
                </linearGradient>
            </defs>
            <text x="20" y="26" text-anchor="middle" fill="white" font-size="18" font-weight="800" font-family="Inter">AO</text>
        </svg>
        <div class="sidebar-logo-text">Astra Otoparts</div>
        <div class="sidebar-logo-sub">Predictive Maintenance Platform</div>
    """


def sidebar_section(title):
    """Section title for sidebar."""
    return f'<div class="sidebar-section-title">{title}</div>'


def hero_card(title, subtitle, badges=None):
    """Hero/banner card with gradient accent and optional badges."""
    badges_html = ""
    if badges:
        badge_items = "".join(
            f'<span class="hero-badge {b["type"]}">{b["text"]}</span>'
            for b in badges
        )
        badges_html = f'<div class="hero-badges">{badge_items}</div>'

    return f"""
    <div class="hero-card">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.5rem;">
            <div>
                <div class="hero-title" data-animate="fade-in">{title}</div>
                <div class="hero-subtitle">{subtitle}</div>
                {badges_html}
            </div>
            <div style="text-align:right; flex-shrink:0;">
                <div style="color:#64748b;font-size:0.7rem;font-weight:500;letter-spacing:0.02em;">
                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
                <div style="color:#475569;font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-top:2px;">
                    Live Monitoring
                </div>
        </div>
    """


def kpi_card(icon, title, value, subtitle="", accent="info"):
    """Executive KPI card with icon and colored accent bar."""
    return f"""
    <div class="kpi-card {accent}" data-animate="scale-in">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-content">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            {f'<div class="kpi-sub">{subtitle}</div>' if subtitle else ''}
        </div>
    """


def metric_card(title, value, subtitle="", accent="info"):
    """Animated KPI metric card with colored accent bar."""
    return f"""
    <div class="metric-card {accent}" data-animate="scale-in">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-sub">{subtitle}</div>' if subtitle else ''}
    </div>
    """


def section_card(title):
    """Section card opening and closing tags."""
    open_tag = f"""
    <div class="section-card" data-animate="fade-in">
        <div class="section-title">
            <span class="title-accent"></span> {title}
        </div>
    """
    close_tag = '</div>'
    return open_tag, close_tag


def status_badge(text, status="info"):
    """Colored status badge."""
    return f'<span class="status-badge {status}">{text}</span>'


def asset_card(title, subtitle="", accent_color="#3b82f6"):
    """Equipment/machine card with left accent border."""
    return f"""
    <div class="asset-card" style="border-left-color:{accent_color};" data-animate="fade-in">
        <div class="asset-title">{title}</div>
        {f'<div class="asset-text">{subtitle}</div>' if subtitle else ''}
    </div>
    """


def motor_status_card(machine_id, health_score, failure_prob, rul, status="healthy"):
    """Factory floor motor card with status color for Digital Twin view."""
    status_colors = {"healthy": "#00ff88", "warning": "#ffd700", "critical": "#ff4444"}
    color = status_colors.get(status, "#3b82f6")
    status_labels = {"healthy": "NORMAL", "warning": "WARNING", "critical": "CRITICAL"}
    label = status_labels.get(status, "NORMAL")
    return f"""
    <div class="motor-card {status}" data-animate="scale-in" style="border-color: {color};">
        <div class="motor-indicator" style="background: {color};"></div>
        <div class="motor-id">{machine_id}</div>
        <div class="motor-status" style="color: {color};">{label}</div>
        <div class="motor-metrics">
            <div class="motor-metric">
                <span class="motor-metric-label">Health</span>
                <span class="motor-metric-value">{health_score:.1f}</span>
            </div>
            <div class="motor-metric">
                <span class="motor-metric-label">Failure</span>
                <span class="motor-metric-value">{failure_prob*100:.1f}%</span>
            </div>
            <div class="motor-metric">
                <span class="motor-metric-label">RUL</span>
                <span class="motor-metric-value">{rul}d</span>
            </div>
    </div>
    """


def ai_insight_card(machine_id, insight_text):
    """AI-generated insight card with icon."""
    return f"""
    <div class="ai-insight-card" data-animate="fade-in">
        <div class="ai-insight-header">
            <span class="ai-insight-icon">🤖</span>
            <span class="ai-insight-label">AI Insight — {machine_id}</span>
        </div>
        <div class="ai-insight-body">{insight_text}</div>
    """


def business_impact_card(icon, label, value, subtitle=""):
    """Business impact metric card for executive view."""
    return f"""
    <div class="impact-card" data-animate="scale-in">
        <div class="impact-icon">{icon}</div>
        <div class="impact-content">
            <div class="impact-label">{label}</div>
            <div class="impact-value">{value}</div>
            {f'<div class="impact-sub">{subtitle}</div>' if subtitle else ''}
        </div>
    """


def alert_card(machine_id, level, message, time_str):
    """Alert notification card with severity color."""
    icons = {"CRITICAL": "🚨", "WARNING": "⚠️", "RESOLVED": "✅"}
    icon = icons.get(level.upper(), "ℹ️")
    return f"""
    <div class="alert-card alert-{level.lower()}" data-animate="slide-in">
        <div class="alert-card-icon">{icon}</div>
        <div class="alert-card-content">
            <div class="alert-card-header">
                <span class="alert-card-machine">{machine_id}</span>
                <span class="alert-card-time">{time_str}</span>
            </div>
            <div class="alert-card-message">{message}</div>
    </div>
    """


def empty_state(icon="📊", title="No Data Available", message="Start monitoring or generate a cycle to see data here."):
    """Beautiful empty state with icon."""
    return f"""
    <div class="empty-state" data-animate="fade-in">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-message">{message}</div>
    """


def alert_banner(level, message):
    """Alert notification banner with icon."""
    icons = {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️", "SUCCESS": "✅"}
    icon = icons.get(level.upper(), "ℹ️")
    return f"""
    <div class="alert-banner alert-{level.lower()}" data-animate="slide-in">
        <span class="alert-icon">{icon}</span>
        <span class="alert-text">{message}</span>
    </div>
    """


def sidebar_nav(page_links):
    """Generate consistent sidebar navigation HTML."""
    items = "".join(
        f'<div class="sidebar-nav-item">{link}</div>' for link in page_links
    )
    return f'<div class="sidebar-nav">{items}</div>'
