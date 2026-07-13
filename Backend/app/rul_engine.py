def calculate_rul(health_score, failure_probability, trend):
    trend_factor = {"NORMAL": 1.0, "WARNING": 0.75, "CRITICAL": 0.45}.get(trend, 0.8)
    score_factor = max(0.2, health_score / 100)
    failure_factor = max(0.05, 1 - failure_probability)
    rul = round(30 * score_factor * failure_factor * trend_factor, 2)
    return max(0.1, rul)
