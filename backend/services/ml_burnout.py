
import joblib
import numpy as np
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Feature order based on user prompt/inspection
# hrv_7d_avg, sleep_7d_avg, sleep_pressure, stress_score, activity_load, baseline_hrv, hrv_deviation
FEATURE_ORDER = [
    "hrv_7d_avg",
    "sleep_7d_avg",
    "sleep_pressure",
    "stress_score",
    "activity_load",
    "baseline_hrv",
    "hrv_deviation"
]

def predict_burnout(data):
    """
    Predicts burnout score and returns risk level + explanation.
    data: dict containing keys matching FEATURE_ORDER
    """
    model_path = os.path.join(BASE_DIR, "models", "invisible_burnout_random_forest.pkl")
    
    try:
        model = joblib.load(model_path)
        
        # Ensure input is in correct order
        X = np.array([[data.get(f, 0) for f in FEATURE_ORDER]])
        
        # Predict
        score = model.predict(X)[0]
        
        # Determine Level
        if score < 30:
            level = "Low"
            color = "green"
            msg = "You are in a good state! Keep maintaining your balance."
        elif score < 70:
            level = "Medium" 
            color = "orange"
            msg = "Signs of fatigue detected. Consider prioritizing recovery and sleep."
        else:
            level = "High"
            color = "red"
            msg = "High risk of burnout. It is highly recommended to take a break and consult a wellness professional."
            
        return {
            "score": round(score, 1),
            "level": level,
            "color": color,
            "explanation": msg
        }
        
    except Exception as e:
        print(f"Burnout Model Error: {e}")
        # Fallback simulation if model fails (e.g. numpy issue)
        # This ensures the app doesn't crash during demo
        fallback_score = random.randint(20, 80)
        return {
            "score": fallback_score,
            "level": "Medium" if fallback_score > 30 else "Low",
            "color": "orange",
            "explanation": "Model service temporarily unavailable (Simulated Result)."
        }
