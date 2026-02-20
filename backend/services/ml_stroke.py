# services/ml_stroke.py

import joblib, numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def predict_stroke(data):
    scaler = joblib.load(os.path.join(BASE_DIR, "models", "stroke_scaler.pkl"))
    model = joblib.load(os.path.join(BASE_DIR, "models", "stroke_model.pkl"))

    # Feature list matching model training
    FEATURE_ORDER = ["gender", "age", "hypertension", "heart_disease", "ever_married", "work_type", "Residence_type", "avg_glucose_level", "bmi", "smoking_status"]
    
    # Ensure all keys exist
    X = np.array([[data.get(f, 0) for f in FEATURE_ORDER]])
    X = scaler.transform(X)

    return "High Risk" if model.predict(X)[0] == 1 else "Low Risk"
