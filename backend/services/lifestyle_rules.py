# services/lifestyle_rules.py

def lifestyle_from_wearables(w):
    risks = []

    if w["steps_per_day"] < 4000:
        risks.append("Low physical activity")

    if w["sleep_hours"] < 6:
        risks.append("Poor sleep")

    if w["avg_heart_rate"] > 90:
        risks.append("High resting heart rate")

    if w["spo2"] < 95:
        risks.append("Low oxygen saturation")

    return risks
