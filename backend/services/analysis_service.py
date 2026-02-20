import streamlit as st
from backend.services.ml_diabetes import predict_diabetes
from backend.services.ml_heart import predict_heart
from backend.services.ml_stroke import predict_stroke
from backend.services.ml_burnout import predict_burnout
from backend.services.ml_sleep import predict_sleep_quality
from backend.services.wearable_service import get_wearable_data
from backend.config.defaults import DIABETES_DEFAULTS, HEART_DEFAULTS, STROKE_DEFAULTS

def run_holistic_checkup(profile, manual_inputs_override=None):
    """
    Runs all ML models based on the current profile and optional manual inputs.
    Returns:
        tuple: (risks_dict, wellness_dict)
    """
    try:
        # 1. Gather Data (Safe Defaults)
        age = int(profile.get('age', 40))
        weight = float(profile.get('weight', 70))
        height = float(profile.get('height', 170))
        
        # Calculate BMI immediately as it's critical
        bmi = round(weight / ((height/100)**2), 2)
        
        # Defaults for medical values if not in profile (users might not know)
        avg_glucose = 120 # Default healthy-ish
        
        # 2. Medical Inputs Preparation
        # We try to use profile data if available, else defaults
        d_in = DIABETES_DEFAULTS.copy()
        d_in.update({
            "Age": age, 
            "BMI": bmi, 
            "Glucose": avg_glucose
        })
        
        h_in = HEART_DEFAULTS.copy()
        h_in.update({"age": age})
        
        s_in = STROKE_DEFAULTS.copy()
        s_in.update({
            "age": age, 
            "bmi": bmi, 
            "avg_glucose_level": avg_glucose
            # smoking_status handling needs context, defaulting to 0 (Unknown/Never) for auto-updates
        })
        
        # 3. Medical Predictions
        db_res = predict_diabetes(d_in)
        ht_res = predict_heart(h_in)
        st_res = predict_stroke(s_in)
        
        risks = {
            "diabetes": db_res, 
            "heart": ht_res, 
            "stroke": st_res
        }

        # 4. Wellness Inputs (Fusion)
        # Check if device is connected via session state proxy or direct check
        # Since this runs in backend, we might not have direct access to st.session_state 
        # but we can check if wearable data is injected or we fetch it.
        # For this implementation, we will fetch fresh if available.
        
        w_data = get_wearable_data() # This simulates fetching
        
        # Base manual inputs (defaults)
        wellness_inputs = {
            "hrv_7d_avg": 45,
            "sleep_7d_avg": 7.0,
            "sleep_pressure": 50,
            "stress_score": 50,
            "activity_load": 50,
            "baseline_hrv": 50,
            "hrv_deviation": 0,
            "sleep_duration_hours": 7.0,
            "hrv_rmssd_ms": 45,
            "spo2_avg_pct": 98
        }
        
        # If manual overrides provided (e.g. from Form), use them
        if manual_inputs_override:
            wellness_inputs.update(manual_inputs_override)
            
        # Smart Overrides from Wearable (Priority)
        if w_data:
             if 'sleep_duration_hours' in w_data: wellness_inputs['sleep_duration_hours'] = w_data['sleep_duration_hours']
             if 'hrv_rmssd_ms' in w_data: wellness_inputs['hrv_rmssd_ms'] = w_data['hrv_rmssd_ms']
             if 'spo2' in w_data: wellness_inputs['spo2_avg_pct'] = w_data['spo2']
             
             steps = w_data.get('steps', 0)
             if steps < 3000: wellness_inputs['activity_load'] = 20
             elif steps < 8000: wellness_inputs['activity_load'] = 55
             else: wellness_inputs['activity_load'] = 85
             
        # Recalc derived
        wellness_inputs['hrv_deviation'] = wellness_inputs['hrv_rmssd_ms'] - wellness_inputs['baseline_hrv']
        
        # 5. Wellness Predictions
        burnout_res = predict_burnout(wellness_inputs)
        sleep_res = predict_sleep_quality(wellness_inputs)
        
        wellness = {
            "burnout": burnout_res, 
            "sleep": sleep_res
        }
        
        return risks, wellness
        
    except Exception as e:
        # Fallback to avoid crashing the agent
        return {}, {}
