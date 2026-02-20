# services/ml_heart.py

import joblib
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FEATURE_ORDER = [
    "age",
    "sex",
    "dataset",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalch",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal"
]

def predict_heart(data):
    model_path = os.path.join(BASE_DIR, "models", "heart_model.pkl")
    scaler_path = os.path.join(BASE_DIR, "models", "heart_scaler.pkl")

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    # 🔥 ORDER-CONTROLLED INPUT
    X = np.array([[data[f] for f in FEATURE_ORDER]])
    X = scaler.transform(X)

    prediction = model.predict(X)[0]
    return "High Risk" if prediction == 1 else "Low Risk"
