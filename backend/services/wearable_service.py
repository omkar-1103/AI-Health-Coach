
import random
import math
import time
from datetime import datetime

# Global simulation state to keep consistency across refreshes (in a real app, this would be DB)
_SIM_STATE = {
    "step_count": 2500,
    "last_update": time.time()
}

def get_wearable_data():
    """
    Simulated wearable data with realistic time-variant behavior.
    """
    current_time = time.time()
    
    # simulate step accumulation over time (approx 1 step per sec if active)
    elapsed = current_time - _SIM_STATE["last_update"]
    if elapsed > 1:
        # 30% chance of walking
        if random.random() > 0.7:
            _SIM_STATE["step_count"] += int(elapsed * 1.5)
        _SIM_STATE["last_update"] = current_time

    # Heart rate varies with time (Sine wave daily cycle + noise)
    # Hour of day 0-24
    hour = datetime.now().hour + (datetime.now().minute / 60)
    # Basal HR cycle (lowest at 4am, highest at 4pm)
    base_hr = 75 + 10 * math.sin((hour - 10) * math.pi / 12)
    # Add noise
    heart_rate = int(base_hr + random.randint(-5, 15))

    # Generate Mock History for Charts (Last 24 Hours)
    # We want a list of 24 points for Heart Rate and Steps
    history = {
        "time": [f"{h:02d}:00" for h in range(24)],
        "heart_rate": [],
        "steps": []
    }
    
    for h in range(24):
        # Sine wave similar to live data but for the whole day
        base = 75 + 10 * math.sin((h - 10) * math.pi / 12)
        history["heart_rate"].append(int(base + random.randint(-5, 15)))
        
        # Steps higher in day (8am-8pm)
        if 8 <= h <= 20:
             history["steps"].append(random.randint(200, 800))
        else:
             history["steps"].append(random.randint(0, 50))

    # Sleep metrics
    sleep_duration = round(random.uniform(6.0, 8.5), 1)  # Hours
    sleep_efficiency = round(random.uniform(75, 95), 1)  # Percentage (70-95% is normal)
    
    # HRV (Heart Rate Variability) - RMSSD in milliseconds
    # Normal range: 20-100ms (higher is generally better)
    hrv_rmssd = round(random.uniform(25, 85), 1)
    
    # Extra Metrics for Dashboard
    resting_hr = int(base_hr - 15) # Approx RHR
    stress_score = max(0, min(100, int(100 - hrv_rmssd + random.randint(-10, 10)))) # Inverse to HRV
    sleep_score = int((sleep_duration / 8) * 50 + (sleep_efficiency / 100) * 50)
    
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "heart_rate": heart_rate,
        "resting_heart_rate": resting_hr,
        "steps": _SIM_STATE["step_count"],
        "sleep_duration_hours": sleep_duration,
        "sleep_efficiency": sleep_efficiency,
        "sleep_score": sleep_score,
        "hrv_rmssd_ms": hrv_rmssd,
        "stress_score": stress_score,
        "sleep": sleep_duration,  # Keep for backward compatibility
        "spo2": random.choice([98, 98, 99, 97]),
        "calories": int(_SIM_STATE["step_count"] * 0.04), # Approx 0.04 cal/step
        "distance": round(_SIM_STATE["step_count"] * 0.0008, 2), # Approx 0.8m/step = 0.0008km
        "history": history
    }
