def weather_health_rules(weather):
    rules = []

    temp = weather["temperature"]
    humidity = weather["humidity"]
    pressure = weather["pressure"]
    aqi = weather["aqi"]

    # ---- Temperature rules ----
    if temp >= 35:
        rules.append({
            "factor": "temperature",
            "condition": "high heat",
            "effect": "Dehydration, fatigue, blood pressure drop"
        })

    if temp <= 10:
        rules.append({
            "factor": "temperature",
            "condition": "cold",
            "effect": "Blood pressure increase, heart strain"
        })

    # ---- Humidity rules ----
    if humidity >= 80:
        rules.append({
            "factor": "humidity",
            "condition": "high humidity",
            "effect": "Breathing difficulty, fatigue"
        })

    if humidity <= 30:
        rules.append({
            "factor": "humidity",
            "condition": "low humidity",
            "effect": "Dry throat, cough"
        })

    # ---- Air pressure rules ----
    if pressure < 1000:
        rules.append({
            "factor": "air pressure",
            "condition": "sudden drop",
            "effect": "Headache, joint pain"
        })

    if pressure > 1025:
        rules.append({
            "factor": "air pressure",
            "condition": "sudden rise",
            "effect": "Blood pressure discomfort"
        })

    # ---- Air Quality rules ----
    if aqi >= 4:
        rules.append({
            "factor": "air quality",
            "condition": "poor AQI",
            "effect": "Asthma risk, chest tightness"
        })

    return rules
