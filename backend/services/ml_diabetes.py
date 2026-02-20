# services/ml_diabetes.py

import joblib, numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def predict_diabetes(data):
    scaler = joblib.load(os.path.join(BASE_DIR, "models", "diabetes_scaler.pkl"))
    model = joblib.load(os.path.join(BASE_DIR, "models", "diabetes_model.pkl"))

    # Feature list matching model training (Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age)
    FEATURE_ORDER = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"]
    
    # Ensure all keys exist (defaults provided in app.py merger, but safety here)
    X = np.array([[data.get(f, 0) for f in FEATURE_ORDER]])
    X = scaler.transform(X)

    return "High Risk" if model.predict(X)[0] == 1 else "Low Risk"
