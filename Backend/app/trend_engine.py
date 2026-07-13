def evaluate_trend(history):
    if not history:
        return {"temperature": "NORMAL", "vibration": "NORMAL", "electrical_current": "NORMAL", "overall": "NORMAL"}

    temp_values = [item["temperature"] for item in history[-10:]]
    vib_values = [item["vibration"] for item in history[-10:]]
    current_values = [item["electrical_current"] for item in history[-10:]]

    temp_trend = temp_values[-1] - temp_values[0]
    vib_trend = vib_values[-1] - vib_values[0]
    current_trend = current_values[-1] - current_values[0]

    def classify(value, threshold):
        if value > threshold * 1.5:
            return "CRITICAL"
        if value > threshold:
            return "WARNING"
        return "NORMAL"

    temperature = classify(temp_trend, 4)
    vibration = classify(vib_trend, 0.01)
    electrical_current = classify(current_trend, 1.5)

    overall = "CRITICAL" if any(item == "CRITICAL" for item in [temperature, vibration, electrical_current]) else "WARNING" if any(item == "WARNING" for item in [temperature, vibration, electrical_current]) else "NORMAL"

    return {
        "temperature": temperature,
        "vibration": vibration,
        "electrical_current": electrical_current,
        "overall": overall,
    }
