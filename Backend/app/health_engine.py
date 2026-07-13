def calculate_health_score(temperature, vibration, electrical_current, pressure, rpm):
    temp_component = max(0, 100 - (temperature - 70) * 1.2)
    vibration_component = max(0, 100 - vibration * 450)
    current_component = max(0, 100 - (electrical_current - 20) * 1.1)
    pressure_component = max(0, 100 - abs(pressure - 8.5) * 5)
    rpm_component = max(0, 100 - abs(rpm - 1500) * 0.03)

    score = round(
    (
        temp_component * 0.25
        + vibration_component * 0.30
        + current_component * 0.20
        + pressure_component * 0.15
        + rpm_component * 0.10
    ),
    2,
)
    return max(0, min(100, score))
