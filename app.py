# ---------------- IMPORTS ----------------
import streamlit as st
import sys
import os
from dotenv import load_dotenv
load_dotenv()  # loads .env file

# Check Streamlit secrets first (for Cloud), then env vars (for Local)
if "MISTRAL_API_KEY" in st.secrets:
    MISTRAL_API_KEY = st.secrets["MISTRAL_API_KEY"]
else:
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    st.error("MISTRAL_API_KEY not found. Please set it in .env (local) or Secrets (cloud).")
    st.stop()
# Add backend directory to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
import time
import requests
import os
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd

# DB & Services
from backend.database import init_db, login_user, register_user, update_profile
from backend.services.wearable_service import get_wearable_data
from backend.services.weather_service import get_weather_and_aqi, get_coordinates, get_weather_forecast
from backend.services.weather_health_rules import weather_health_rules
from backend.services.ml_diabetes import predict_diabetes
from backend.services.ml_heart import predict_heart
from backend.services.ml_stroke import predict_stroke
from backend.services.ml_burnout import predict_burnout
from backend.services.ml_sleep import predict_sleep_quality
from backend.services.analysis_service import run_holistic_checkup
from backend.config.defaults import DIABETES_DEFAULTS, HEART_DEFAULTS, STROKE_DEFAULTS
from backend.rag.rag_service import rag_search


# Init DB
init_db()

# ---------------- PAGE CONFIG ----------------
# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Health Coach: A Mini Doctor in Your Pocket",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- STATE MANAGEMENT ----------------
if 'auth_status' not in st.session_state: st.session_state.auth_status = None 
if 'username' not in st.session_state: st.session_state.username = None
if 'device_connected' not in st.session_state: st.session_state.device_connected = False
if 'user_profile' not in st.session_state: st.session_state.user_profile = {}
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'weather_loc' not in st.session_state: st.session_state.weather_loc = "Mumbai, IN" 
if 'active_alerts' not in st.session_state: st.session_state.active_alerts = [] # Persistent Alerts

# ---------------- CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

/* GLOBAL */
.stApp {
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #e0e0e0;
}

/* Background Image Overlay */
.stApp {
    background-color: #050a14;
}

/* Login Card Styling - Exact Match */
.login-card {
    background: rgba(13, 17, 30, 0.85); /* Darker, deep blue tone */
    border: 1px solid rgba(50, 60, 90, 0.5);
    border-radius: 24px;
    padding: 40px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.8);
    backdrop-filter: blur(20px);
}

.login-title {
    font-size: 20px;
    font-weight: 600;
    color: #fff;
    text-align: center;
    margin-bottom: 5px;
}
.login-subtitle {
    font-size: 14px;
    color: #00f2fe; /* Cyan color from image */
    text-align: center;
    margin-bottom: 25px;
}
.big-hero-title {
    font-size: 56px;
    font-weight: 700;
    color: white;
    line-height: 1.2;
    margin-bottom: 15px;
    text-shadow: 0 4px 15px rgba(0,0,0,0.9); /* READABILITY FIX */
}
.hero-desc {
    font-size: 18px;
    color: #e0e7ff; /* Whiter text for better contrast */
    max-width: 500px;
    line-height: 1.6;
    text-shadow: 0 2px 5px rgba(0,0,0,0.8); /* READABILITY FIX */
}

/* Input Fields - Dark Theme */
div[data-baseweb="input"] {
    background-color: rgba(30, 41, 59, 0.5) !important; /* Darker input background */
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    color: white !important;
    padding: 5px;
}
div[data-baseweb="input"]:focus-within {
    border-color: #00f2fe !important;
    box-shadow: 0 0 0 1px #00f2fe !important;
    background-color: rgba(30, 41, 59, 0.8) !important;
}
input {
    color: white !important; 
    font-size: 15px;
}
div[data-testid="stForm"] {
    border: none;
    padding: 0;
}

/* Tabs as Pill Toggle */
.stTabs [data-baseweb="tab-list"] {
    background-color: rgba(0, 0, 0, 0.4);
    padding: 5px;
    border-radius: 50px;
    display: flex;
    justify-content: space-between;
    margin-bottom: 25px;
    border: 1px solid rgba(255,255,255,0.05);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 40px !important;
    padding: 8px 0px !important;
    background-color: transparent;
    color: #94a3b8;
    border: none !important;
    flex: 1;
    text-align: center;
    text-align: center;
    justify-content: center;
    font-weight: 500; /* Bolder tabs */
    color: #cbd5e1; /* Lighter gray for visibility */
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%) !important;
    color: #0b0f19 !important;
    font-weight: 700;
    box-shadow: 0 4px 15px rgba(0, 242, 254, 0.4);
}

/* Primary Button */
/* Primary Button - Strict Override */
div.stButton > button:first-child {
    background: linear-gradient(90deg, #22d3ee 0%, #0ea5e9 100%) !important;
    border: none !important;
    height: 52px !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    color: #0f172a !important;
    width: 100% !important;
    transition: all 0.3s !important;
}
div.stButton > button:first-child:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(34, 211, 238, 0.4) !important;
    color: #0f172a !important;
}

/* Helper Text */
.form-footer {
    text-align: center; 
    color: #64748b; 
    font-size: 13px; 
    margin-top: 20px;
}

/* CARDS /* --- BENTO GRID SYSTEM --- */
.bento-box {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.bento-box:hover {
    transform: translateY(-4px);
    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.4);
    border-color: rgba(255, 255, 255, 0.25);
    background: rgba(255, 255, 255, 0.07);
}

/* Typography */
.weather-title { font-size: 14px; font-weight: 600; color: #00f2fe; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
.weather-value-big { font-size: 64px; font-weight: 800; color: #fff; line-height: 1; }
.weather-value-med { font-size: 28px; font-weight: 700; color: #fff; }
.weather-unit { font-size: 16px; color: #9ca3af; font-weight: 500; }
.weather-sub { font-size: 18px; color: #e0e0e0; }

/* Custom Metric Card */
.metric-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    height: 100%;
}
.metric-icon { font-size: 32px; margin-bottom: 10px; }

/* Forecast Row */
.forecast-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.forecast-item:last-child { border-bottom: none; }

/* Tabs Override */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }

div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 15px;
}
div[data-testid="stMetricLabel"] { color: #00f2fe !important; }
div[data-testid="stMetricValue"] { color: #ffffff !important; font-size: 24px; }
244: 
245: /* Medical Form Styling */
246: .health-check-card {
247:     background: rgba(30, 41, 59, 0.4);
248:     border: 1px solid rgba(255, 255, 255, 0.08);
249:     border-radius: 16px;
250:     padding: 25px;
251:     margin-bottom: 20px;
252: }
253: .health-section-header {
254:     color: #00f2fe;
255:     font-size: 16px;
256:     font-weight: 600;
257:     text-transform: uppercase;
258:     letter-spacing: 1px;
259:     margin-bottom: 15px;
260:     border-bottom: 1px solid rgba(255,255,255,0.1);
261:     padding-bottom: 8px;
262: }

</style>
""", unsafe_allow_html=True)


# ---------------- HELPER FUNCTIONS ----------------
def create_donut_chart(value, max_val, suffix, color):
    val = float(value)
    mx = float(max_val)
    if mx == 0: mx = 1
    
    filled = val
    remainder = max(0, mx - val)
    if val > mx:
        filled = mx
        remainder = 0
        
    fig = go.Figure(data=[go.Pie(
        values=[filled, remainder],
        hole=0.75,
        marker=dict(colors=[color, "rgba(255,255,255,0.1)"]),
        textinfo="none",
        hoverinfo="none",
        sort=False,
        direction="clockwise"
    )])
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=140,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text=f"<span style='font-size:24px; font-weight:bold; color:white'>{value}</span><br><span style='font-size:12px; color:#aaa'>{suffix}</span>", x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    return fig

def render_bento_metric(title, value, unit, icon):
    st.markdown(f"""
    <div class="bento-box" style="height: 180px;">
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="weather-title">{title}</div>
            <div class="weather-value-med">{value}<span class="weather-unit"> {unit}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
def generate_workout_plan(weather, vitals, profile, risks=None, wellness=None):
    """
    Generates a personalized workout plan using AI.
    Args:
        weather: Weather conditions dict
        vitals: Wearable data dict (steps, HR, etc.)
        profile: User profile dict
        risks: Health risks dict (diabetes, heart, stroke) - NEW
        wellness: Wellness scores dict (burnout, sleep) - NEW
    """
    w_cond = str(weather).lower()
    steps = vitals.get('steps', 0)
    
    # 2. RAG Search
    query = f"workout plan for {w_cond} weather, {steps} steps energy level, {profile.get('age', '30')} years old"
    retrieved_docs = rag_search(query)
    context_text = "\n".join(retrieved_docs)
    
    # 3. Build Health Context (NEW)
    health_context = ""
    vitals_context = ""
    
    # Add health risks if available
    if risks:
        risk_notes = []
        if "High" in risks.get('heart', ''):
            risk_notes.append("⚠️ High heart disease risk - Recommend low-intensity cardio, avoid high-intensity intervals")
        if "High" in risks.get('diabetes', ''):
            risk_notes.append("⚠️ High diabetes risk - Focus on blood sugar regulation, include resistance training")
        if "High" in risks.get('stroke', ''):
            risk_notes.append("⚠️ High stroke risk - Avoid sudden exertion, prioritize steady-state exercises")
        
        if risk_notes:
            health_context = "HEALTH RISKS:\n" + "\n".join(risk_notes) + "\n"
    
    # Add wellness scores if available
    if wellness:
        burnout_score = wellness.get('burnout', {}).get('score', 0)
        sleep_eff = wellness.get('sleep', {}).get('efficiency_score', 100)
        
        wellness_notes = []
        if burnout_score > 70:
            wellness_notes.append("⚠️ High burnout detected - Prioritize restorative exercises (yoga, stretching, walking)")
        elif burnout_score > 50:
            wellness_notes.append("⚠️ Moderate burnout - Balance intensity with recovery")
        
        if sleep_eff < 70:
            wellness_notes.append("⚠️ Poor sleep quality - Avoid late evening high-intensity workouts")
        
        if wellness_notes:
            health_context += "WELLNESS STATUS:\n" + "\n".join(wellness_notes) + "\n"
    
    # Add real-time vitals if available (NEW)
    if vitals:
        hr = vitals.get('heart_rate')
        resting_hr = vitals.get('resting_heart_rate')
        hrv = vitals.get('hrv_rmssd_ms')
        stress = vitals.get('stress_score')
        
        vitals_notes = []
        if hr and resting_hr and hr > resting_hr + 20:
            vitals_notes.append(f"⚠️ Elevated heart rate ({hr} bpm vs resting {resting_hr} bpm) - Consider lighter workout")
        if hrv and hrv < 30:
            vitals_notes.append(f"⚠️ Low HRV ({hrv} ms) - Body needs recovery, recommend low intensity")
        if stress and stress > 70:
            vitals_notes.append(f"⚠️ High stress level ({stress}/100) - Include stress-relief exercises")
        
        if vitals_notes:
            vitals_context = "REAL-TIME VITALS:\n" + "\n".join(vitals_notes) + "\n"
    
    # 4. LLM Prompt
    prompt = f"""
    You are an expert fitness coach. Create a personalized workout plan based on the following context.
    
    USER CONTEXT:
    - Weather: {w_cond}
    - Daily Steps So Far: {steps}
    - Profile: {profile}
    
    {health_context}
    {vitals_context}
    
    GUIDELINES (from RAG):
    {context_text}
    
    TASK:
    Generate a JSON response with the following structure ONLY:
    {{
        "workout_type": "string (e.g., Indoor Yoga, HIIT, Output Run)",
        "total_duration": "string (e.g., 30 mins)",
        "intensity": "string (Low/Medium/High)",
        "recommended_time": "string (Morning/Evening)",
        "exercises": [
            {{"name": "Exercise Name", "duration": "Duration/Reps", "notes": "Brief instruction"}}
        ],
        "safety_notes": "One concise warning or advice sentence based on weather/fatigue.",
        "reason": "Why this workout was chosen (1 sentence)."
    }}
    """
    
    # 4. Call LLM
    try:
        resp = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
            json={
                "model": "mistral-tiny", 
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
        )
        if resp.status_code == 200:
            import json
            return json.loads(resp.json()['choices'][0]['message']['content'])
        else:
            print(f"LLM Error: {resp.text}")
            return _get_fallback_plan(w_cond, steps) # Fallback
    except Exception as e:
        print(f"Generation Error: {e}")
        return _get_fallback_plan(w_cond, steps)

def _get_fallback_plan(w_cond, steps):
    # Fallback to simple heuristics if AI fails
    plan = {
        "workout_type": "General Fitness",
        "total_duration": "30 mins",
        "intensity": "Medium",
        "recommended_time": "Anytime",
        "exercises": [
            {"name": "Warmup", "duration": "5 mins", "notes": "Light stretching"},
            {"name": "Brisk Walk", "duration": "20 mins", "notes": "Steady pace"},
            {"name": "Cooldown", "duration": "5 mins", "notes": "Static stretches"}
        ],
        "safety_notes": "Stay hydrated and listen to your body.",
        "reason": "Standard maintenance workout (AI temporarily unavailable)."
    }
    return plan


def get_unified_wellness_inputs(profile, form_inputs, device_connected):
    """
    Smart Data Fusion: Prioritizes Wearable Data if available, falls back to Form Inputs.
    Returns a dictionary ready for ML models.
    """
    # 1. Base: Start with Form Inputs
    inputs = form_inputs.copy()
    
    # 2. Overlay: Wearable Data (Priority)
    w_data = {}
    if device_connected:
        w_data = get_wearable_data()
        
        # --- SMART OVERRIDES ---
        # Sleep: Watch is more accurate than user memory
        if 'sleep_duration_hours' in w_data:
            inputs['sleep_duration_hours'] = w_data['sleep_duration_hours']
        
        # Activity: Steps proxy for activity level
        # < 3000 (Sedentary), 3000-8000 (Moderate), > 8000 (Active)
        steps = w_data.get('steps', 0)
        if steps < 3000: inputs['activity_load'] = 20
        elif steps < 8000: inputs['activity_load'] = 55
        else: inputs['activity_load'] = 85
            
        # HRV: Explicitly use measured HRV
        if 'hrv_rmssd_ms' in w_data:
            inputs['hrv_rmssd_ms'] = w_data['hrv_rmssd_ms']
            
        # SpO2
        if 'spo2' in w_data:
            inputs['spo2_avg_pct'] = w_data['spo2']

    return inputs, w_data



def login_page():
    # Load background image
    # Load background image
    import base64
    
    @st.cache_data # CACHE THIS HEAVY OP
    def get_base64_of_bin_file(bin_file):
        try:
            with open(bin_file, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()
        except Exception:
            return None

    bin_str = get_base64_of_bin_file("bg_img.png")
    if bin_str:
        background_style = f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{bin_str}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
        """
        st.markdown(background_style, unsafe_allow_html=True)
    
    # Layout
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, mid, c2 = st.columns([1.4, 0.2, 1]) # Added middle spacer
    
    with c1:
        st.markdown("<div style='height: 120px;'></div>", unsafe_allow_html=True)
        # Clean Left Side Text (No Icons)
        st.markdown("""
        <div>
            <div class="big-hero-title">AI Health Coach:<br>A Mini Doctor in<br>Your Pocket</div>
            <div class="hero-desc">Smart health guidance, real-time monitoring, and personalized AI support.</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        # Login Card Right
        # Note: CSS now targets div[data-testid="column"]:nth-of-type(3) for the card look
        
        # Header inside card
        # REMOVED DUPLICATE TITLE HERE FOR CLEANER LOOK
        st.markdown("""
        <div style="text-align:center; padding-top: 10px; margin-bottom:10px;">
        </div>
        """, unsafe_allow_html=True)

        # Tabs (Styled as Pill Toggle)
        t_login, t_signup = st.tabs(["Login", "Sign Up"])
        
        with t_login:
            st.markdown("<p style='text-align:center; color:#94a3b8; font-size:13px; margin-bottom:20px;'>Secure access to your personal AI health dashboard</p>", unsafe_allow_html=True)
            with st.form("login_form"):
                u = st.text_input("Username", placeholder="Username", label_visibility="collapsed") 
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                p = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Login", type="primary"):
                    success, profile = login_user(u, p)
                    if success:
                        st.session_state.auth_status = 'logged_in'
                        st.session_state.username = u
                        st.session_state.user_profile = profile
                        st.rerun()
                    else: st.error("Access Denied")
            
            st.markdown("<div class='form-footer'>Don't have an account? Sign Up</div>", unsafe_allow_html=True)

        with t_signup:
            st.markdown("<p style='text-align:center; color:#94a3b8; font-size:13px; margin-bottom:20px;'>Create your secure health profile</p>", unsafe_allow_html=True)
            with st.form("signup_form"):
                new_u = st.text_input("New Username", placeholder="Choose Username", label_visibility="collapsed")
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                new_p = st.text_input("New Password", type="password", placeholder="Choose Password", label_visibility="collapsed")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Sign Up", type="primary"):
                    if new_u and new_p:
                        success, msg = register_user(new_u, new_p)
                        if success: st.success("Account created! Go to Login.")
                        else: st.error(msg)
                    else: st.warning("Fields required")
                    



def main_app():
    # SIDEBAR
    with st.sidebar:
        st.write(f"👤 **{st.session_state.username}**")
        if not st.session_state.device_connected:
            st.warning("🔴 Device Disconnected")
            if st.button("🔗 Connect Device"):
                 progress = st.progress(0)
                 status = st.empty()
                 status.write("Syncing Vitals...")
                 time.sleep(1)
                 progress.progress(100)
                 st.session_state.device_connected = True
                 st.rerun()
        else:
            st.success("🟢 Galaxy Watch 5 Active")
            st.metric("Battery", "88%", "-2%")
            if st.button("Disconnect"):
                st.session_state.device_connected = False
                st.rerun()
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.auth_status = None
            st.rerun()
            
        # --- AGENT: PERSISTENT ALERTS (OBSERVER) ---
        if st.session_state.active_alerts:
            st.markdown("---")
            st.error("⚠️ Active Health Alerts")
            for alert in st.session_state.active_alerts:
                 st.markdown(f"<div style='font-size:12px; color:#fca5a5;'>• {alert}</div>", unsafe_allow_html=True)
            if st.button("Clear Alerts"):
                st.session_state.active_alerts = []
                st.rerun()

    # TABS
    t1, t2, t3, t4, t5 = st.tabs(["📊 Dashboard", "🌦️ Weather Impact", "🏥 Health Check", "💬 AI Doctor", "🏋️ Workout Plan"])

    # --- TAB 1: DASHBOARD ---
    # --- TAB 1: DASHBOARD ---
    with t1:
        st.markdown("<h2 style='margin-bottom: 5px;'>Wellness & Health Dashboard</h2>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 25px; color: #94a3b8; font-size: 14px;'>Connecting your life data, strictly raw and unfiltered.</div>", unsafe_allow_html=True)

        if not st.session_state.device_connected:
             st.info("Connect device in Sidebar to view live metrics.")
        else:
             if st.button("🔄 Sync Now", key="refresh_dash"): st.rerun()
             w = get_wearable_data()
             
             # --- STYLE: CARD UI ---
             def render_card(title, value, unit, icon, color="#00f2fe"):
                 st.markdown(f"""
                 <div class="bento-box" style="padding: 20px; height: 160px; position: relative;">
                     <div style="position: absolute; top: 15px; right: 15px; font-size: 24px; opacity: 0.8;">{icon}</div>
                     <div style="font-size: 13px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">{title}</div>
                     <div style="font-size: 38px; font-weight: 800; color: white;">{value}</div>
                     <div style="font-size: 14px; color: {color}; font-weight: 500;">{unit}</div>
                     <div style="position: absolute; bottom: 15px; left: 20px; font-size: 10px; color: #555;">Measured by wearable</div>
                 </div>
                 """, unsafe_allow_html=True)

             # --- S1: HEART & BODY ---
             st.markdown("##### ❤️ Heart & Body")
             c1, c2, c3 = st.columns(3)
             with c1: render_card("Heart Rate", w['heart_rate'], "BPM", "❤", "#ef4444")
             with c2: render_card("Resting HR", w.get('resting_heart_rate', '--'), "BPM", "🛌", "#f472b6")
             with c3: render_card("HRV (RMSSD)", w.get('hrv_rmssd_ms', '--'), "ms", "📉", "#a78bfa")

             # --- S2: SLEEP SUMMARY ---
             st.markdown("##### 💤 Sleep Summary")
             c1, c2, c3 = st.columns(3)
             with c1: render_card("Duration", w.get('sleep_duration_hours', '--'), "Hours", "🌙", "#60a5fa")
             with c2: render_card("Efficiency", f"{w.get('sleep_efficiency', '--')}", "%", "📊", "#34d399")
             with c3: render_card("Sleep Score", w.get('sleep_score', '--'), "/ 100", "🏆", "#fbbf24")

             # --- S3: ACTIVITY ---
             st.markdown("##### 👟 Activity")
             c1, c2, c3 = st.columns(3)
             with c1: render_card("Steps", w['steps'], "steps", "👣", "#fb923c")
             with c2: render_card("Calories", w['calories'], "kcal", "🔥", "#ef4444")
             with c3: render_card("Distance", w['distance'], "km", "📍", "#22d3ee")

             # --- S4: OXYGEN & STRESS ---
             st.markdown("##### 🧬 Vitals")
             c1, c2 = st.columns(2)
             with c1: 
                 st.markdown(f"""
                 <div class="bento-box" style="padding: 20px; display: flex; align-items: center; justify-content: space-between;">
                     <div>
                         <div style="font-size: 13px; color: #94a3b8; text-transform: uppercase;">Blood Oxygen (SpO₂)</div>
                         <div style="font-size: 32px; font-weight: bold; color: white;">{w['spo2']}%</div>
                         <div style="font-size: 11px; color: #555;">Measured by wearable</div>
                     </div>
                     <div style="font-size: 40px;">💨</div>
                 </div>
                 """, unsafe_allow_html=True)
             with c2:
                 s_val = w.get('stress_score', 50)
                 s_lvl = "Low" if s_val < 35 else "Medium" if s_val < 70 else "High"
                 s_col = "#4ade80" if s_lvl == "Low" else "#facc15" if s_lvl == "Medium" else "#f87171"
                 st.markdown(f"""
                 <div class="bento-box" style="padding: 20px; display: flex; align-items: center; justify-content: space-between;">
                     <div>
                         <div style="font-size: 13px; color: #94a3b8; text-transform: uppercase;">Stress Level</div>
                         <div style="font-size: 32px; font-weight: bold; color: {s_col};">{s_lvl}</div>
                         <div style="font-size: 11px; color: #555;">Score: {s_val}/100</div>
                     </div>
                     <div style="font-size: 40px;">🧠</div>
                 </div>
                 """, unsafe_allow_html=True)

             # --- S5: TRENDS ---
             st.markdown("##### 📈 24H Trends")
             t1_col, t2_col = st.columns(2)
             
             with t1_col:
                 # HR Line Chart
                 hist_time = w['history']['time']
                 hist_hr = w['history']['heart_rate']
                 
                 fig = go.Figure()
                 fig.add_trace(go.Scatter(x=hist_time, y=hist_hr, mode='lines+markers', line=dict(color='#ef4444', width=3), name='HR'))
                 fig.update_layout(
                     title={'text': "Heart Rate Trend", 'font': {'color': '#fff', 'size': 14}},
                     height=250,
                     paper_bgcolor='rgba(0,0,0,0)',
                     plot_bgcolor='rgba(255,255,255,0.05)',
                     margin=dict(l=10, r=10, t=40, b=10),
                     xaxis=dict(showgrid=False, tickfont=dict(color='#888')),
                     yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#888'))
                 )
                 st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

             with t2_col:
                 # Steps Bar Chart
                 hist_steps = w['history']['steps']
                 fig = go.Figure()
                 fig.add_trace(go.Bar(x=hist_time, y=hist_steps, marker_color='#fb923c', name='Steps'))
                 fig.update_layout(
                     title={'text': "Hourly Steps", 'font': {'color': '#fff', 'size': 14}},
                     height=250,
                     paper_bgcolor='rgba(0,0,0,0)',
                     plot_bgcolor='rgba(255,255,255,0.05)',
                     margin=dict(l=10, r=10, t=40, b=10),
                     xaxis=dict(showgrid=False, tickfont=dict(color='#888')),
                     yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#888'))
                 )
                 st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- TAB 2: WEATHER DASHBOARD (FINAL SAKET LAYOUT) ---
    with t2:
        # SEARCH ROW
        col_search, col_loc_info = st.columns([3, 1])
        with col_search:
            new_loc_input = st.text_input("Search Location", st.session_state.weather_loc, label_visibility="collapsed", placeholder="Enter City Name...")
        with col_loc_info:
            if st.button("Update Weather", use_container_width=True):
                st.session_state.weather_loc = new_loc_input
                st.rerun()

        # FETCH & RENDER
        with st.spinner("Fetching Real-time Data..."):
            coords = get_coordinates(st.session_state.weather_loc)
            if coords:
                wd = get_weather_forecast(coords['lat'], coords['lon'])
                if wd:
                    curr = wd['current']
                    
                    # --- TOP ROW: BLOCK A (City/Clock) & BLOCK B (Temp/Sun) ---
                    col_a, col_b = st.columns([1, 2])
                    
                    with col_a:
                        # BLOCK A: CITY & CLOCK
                        st.markdown(f"""
                        <div class="bento-box" style="height: 320px; text-align: center; display: flex; flex-direction: column; justify-content: center;">
                            <div class="weather-title">Location</div>
                            <div class="weather-value-med" style="margin-bottom: 20px;">{coords['name']}</div>
                            <div class="weather-value-big" style="font-size: 72px;">{datetime.now().strftime("%I:%M")}</div>
                            <div class="weather-sub">{datetime.now().strftime("%A, %d %b")}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col_b:
                        # BLOCK B: TEMP + SUNRISE + SUNSET
                        st.markdown(f"""
                        <div class="bento-box" style="height: 320px;">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <div class="weather-value-big" style="font-size: 100px;">{curr['temp']}°C</div>
                                    <div class="weather-sub" style="font-size: 24px;">Feels like: {curr['feels_like']}°C</div>
                                </div>
                                <div style="text-align: center; flex: 1;">
                                    <div style="font-size: 100px;">{curr['icon']}</div>
                                    <div class="weather-value-med">{curr['condition']}</div>
                                </div>
                                <div style="text-align: right; min-width: 150px;">
                                    <div style="margin-bottom: 30px;">
                                        <div class="weather-title">Sunrise</div>
                                        <div class="weather-value-med" style="font-size: 22px;">🌅 {curr['sunrise']}</div>
                                    </div>
                                    <div>
                                        <div class="weather-title">Sunset</div>
                                        <div class="weather-value-med" style="font-size: 22px;">🌇 {curr['sunset']}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # --- MIDDLE ROW: BLOCK C (4 SEPARATE METRICS) ---
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.markdown(f"""
                        <div class="bento-box" style="height: 180px; text-align: center;">
                            <div style="font-size: 40px; margin-bottom: 10px;">💧</div>
                            <div class="weather-title">Humidity</div>
                            <div class="weather-value-med">{curr['humidity']}<span class="weather-unit">%</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                    with m2:
                        st.markdown(f"""
                        <div class="bento-box" style="height: 180px; text-align: center;">
                            <div style="font-size: 40px; margin-bottom: 10px;">💨</div>
                            <div class="weather-title">Wind Speed</div>
                            <div class="weather-value-med">{curr['wind_speed']}<span class="weather-unit">km/h</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                    with m3:
                        st.markdown(f"""
                        <div class="bento-box" style="height: 180px; text-align: center;">
                            <div style="font-size: 40px; margin-bottom: 10px;">⏲</div>
                            <div class="weather-title">Pressure</div>
                            <div class="weather-value-med">{curr['pressure']}<span class="weather-unit">hPa</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                    with m4:
                        st.markdown(f"""
                        <div class="bento-box" style="height: 180px; text-align: center;">
                            <div style="font-size: 40px; margin-bottom: 10px;">☀</div>
                            <div class="weather-title">UV Index</div>
                            <div class="weather-value-med">{curr['uv']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # --- BOTTOM ROW: BLOCK D (5-DAY) & BLOCK E (HOURLY Visual Cards) ---
                    col_d, col_e = st.columns([1, 2])
                    
                    with col_d:
                        # Consolidate Forecast HTML
                        if wd['daily']:
                            f_html = '<div class="bento-box" style="min-height: 500px;">'
                            f_html += '<div class="weather-title" style="margin-bottom: 20px;">5 Days Forecast</div>'
                            for day in wd['daily']:
                                f_html += f"""<div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
<div style="font-size: 28px;">{day['icon']}</div>
<div style="flex: 1; margin-left: 15px;">
<div style="font-weight: bold; color: white;">{day['max_temp']}°C</div>
<div style="font-size: 12px; color: #aaa;">{day['day_name']}</div>
</div>
<div style="text-align: right; color: #aaa; font-size: 13px;">{day['full_date']}</div>
</div>"""
                            f_html += '</div>'
                            st.markdown(f_html, unsafe_allow_html=True)
                        else:
                            st.warning("No 5-day forecast available.")
                        
                    with col_e:
                        # Consolidate Hourly HTML
                        if wd['hourly']:
                            h_html = '<div class="bento-box" style="min-height: 500px;">'
                            h_html += '<div class="weather-title" style="margin-bottom: 30px;">Hourly Forecast</div>'
                            h_html += '<div style="display: flex; overflow-x: auto; padding-bottom: 20px; gap: 15px; scrollbar-width: thin;">'
                            for h in wd['hourly']:
                                h_html += f"""<div style="background: rgba(255,255,255,0.05); border-radius: 20px; padding: 20px; min-width: 125px; text-align: center; border: 1px solid rgba(255,255,255,0.1);">
<div style="font-weight: 600; font-size: 15px; margin-bottom: 10px; color: white;">{h['time']}</div>
<div style="font-size: 42px; margin-bottom: 10px;">{h['icon']}</div>
<div style="font-size: 26px; font-weight: 800; color: #00f2fe;">{h['temp']}°</div>
<div style="font-size: 12px; color: #aaa; margin-top: 10px;">💨 {h['wind']} km/h</div>
</div>"""
                            h_html += '</div></div>'
                            st.markdown(h_html, unsafe_allow_html=True)
                        else:
                            st.warning("No hourly forecast available.")
                else:
                    st.error("Failed to load weather data. Please check logs or try again.")
            else:
                st.error(f"Could not find coordinates for '{st.session_state.weather_loc}'.")

    # --- TAB 3: CHECKUP (REAL ML) ---
    # --- TAB 3: CHECKUP (REAL ML) ---
    with t3:
        st.markdown("<h2 style='text-align: center; margin-bottom: 10px;'>Comprehensive Health Check</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8; margin-bottom: 30px;'>One form, complete analysis. Get a holistic view of your health risks and wellness status.</p>", unsafe_allow_html=True)
        
        # 1. UNIFIED FORM
        with st.form("checkup_form"):
            
            # SECTION 1: BIOMETRICS
            st.markdown('<div class="health-check-card"><div class="health-section-header">1. Biometrics & Vital Stats</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                prof = st.session_state.user_profile
                age = st.number_input("Age", 1, 100, prof.get('age', 40), key="form_age")
                weight = st.number_input("Weight (kg)", 30, 200, prof.get('weight', 70), key="form_weight")
            with c2:
                height = st.number_input("Height (cm)", 100, 250, prof.get('height', 170), key="form_height")
                glu = st.number_input("Avg Glucose (mg/dL)", 50, 400, 120, key="form_glucose")
            with c3:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="form_gender") 
                bp_high = st.selectbox("History of High BP?", ["No", "Yes"], index=0, key="form_bp_high")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # SECTION 2: LIFESTYLE & HABITS
            st.markdown('<div class="health-check-card"><div class="health-section-header">2. Lifestyle & Habits</div>', unsafe_allow_html=True)
            l1, l2, l3 = st.columns(3)
            with l1:
                smoke = st.selectbox("Do you smoke?", ["No", "Yes"], index=0, key="form_smoke")
                alcohol = st.selectbox("Alcohol Consumption", ["None", "Occasional", "Frequent"], index=1, key="form_alcohol")
            with l2:
                activity_lvl = st.select_slider("Daily Activity Level", options=["Sedentary", "Moderate", "Active"], value="Moderate", key="form_activity")
                diet = st.selectbox("Diet Type", ["Balanced", "Veg", "Non-Veg", "Keto/Paleo"], index=0, key="form_diet")
            with l3:
                stress_lvl = st.select_slider("Self-Perceived Stress", options=["Low", "Medium", "High"], value="Medium", key="form_stress")
            st.markdown('</div>', unsafe_allow_html=True)

            # SECTION 3: SLEEP & WELLBEING
            st.markdown('<div class="health-check-card"><div class="health-section-header">3. Sleep & Well-being</div>', unsafe_allow_html=True)
            s1, s2 = st.columns(2)
            with s1:
                sleep_hrs = st.slider("Average Sleep Duration (Hours)", 3.0, 12.0, 7.0, 0.5, key="form_sleep")
                wake_tired = st.selectbox("Do you wake up feeling tired?", ["No", "Sometimes", "Yes"], index=1, key="form_tired")
            with s2:
                phone_bed = st.selectbox("Use phone right before bed?", ["Yes", "No"], index=0, key="form_phone")
                mood = st.selectbox("General Mood lately", ["Happy", "Neutral", "Anxious", "Low"], index=1, key="form_mood")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("Run Full System Diagnosis", type="primary", use_container_width=True)


            if submit:
                with st.spinner("Analyzing Medical & Wellness Data..."):
                    try:
                        # --- PREPARATION & CALCULATIONS ---
                        bmi = round(weight / ((height/100)**2), 2)
                        
                        # Wellness Mapping (Manual Inputs from Form)
                        stress_map = {"Low": 30, "Medium": 60, "High": 85}
                        stress_val = stress_map[stress_lvl]
                        
                        act_map = {"Sedentary": 20, "Moderate": 55, "Active": 85}
                        act_val = act_map[activity_lvl]
                        
                        pressure_map = {"No": 30, "Sometimes": 50, "Yes": 80}
                        pressure_val = pressure_map[wake_tired]
                        
                        # Form-Based Wellness Inputs
                        manual_inputs = {
                            "hrv_7d_avg": 45,  # Default fallback
                            "sleep_7d_avg": sleep_hrs, 
                            "sleep_pressure": pressure_val, 
                            "stress_score": stress_val, 
                            "activity_load": act_val, 
                            "baseline_hrv": 50, 
                            "hrv_deviation": 0,
                            "sleep_duration_hours": sleep_hrs, 
                            "hrv_rmssd_ms": 45, 
                            "spo2_avg_pct": 98
                        }
                        
                        # Smart Fusion: Overlay wearable data if device connected
                        unified_inputs, w_data = get_unified_wellness_inputs(
                            st.session_state.user_profile, 
                            manual_inputs, 
                            st.session_state.device_connected
                        )
                        
                        # Update Profile with Form Data
                        new_prof = st.session_state.user_profile.copy()
                        new_prof.update({
                            "age": age, 
                            "weight": weight, 
                            "height": height, 
                            "gender": gender,
                            "bmi": bmi
                        })
                        
                        # --- RUN HOLISTIC CHECKUP ---
                        # This replaces the duplicate ML prediction code (lines 863-911)
                        risks, wellness = run_holistic_checkup(new_prof, unified_inputs)
                        
                        # Update profile with analysis results
                        new_prof['risks'] = risks
                        new_prof['wellness'] = wellness
                        
                        # Save to DB and Session
                        update_profile(st.session_state.username, new_prof)

                        st.session_state.user_profile = new_prof

                        # --- AGENT A: EVENT-DRIVEN OBSERVER ---
                        # Automatically checks for critical states and triggers Alerts
                        
                        # 1. Burnout Check
                        burnout_res = wellness.get('burnout', {})
                        b_score = burnout_res.get('score', 0)
                        if b_score > 70:
                            msg = "High Burnout Risk Detected!"
                            detail = f"Score is {b_score}/100. System recommends activating Recovery Mode."
                            
                            # A. Pop-up (Immediate)
                            st.toast(msg + " " + detail, icon="🔥")
                            
                            # B. Sidebar (Persistent)
                            alert_txt = f"Burnout Level:{b_score} (High)"
                            if alert_txt not in st.session_state.active_alerts:
                                st.session_state.active_alerts.append(alert_txt)
                                
                            # C. Chat Log (Context)
                            sys_msg = {"role": "system", "content": f"🚨 SYSTEM ALERT: {msg}\n{detail}"}
                            if sys_msg not in st.session_state.chat_history:
                                st.session_state.chat_history.append(sys_msg)

                        # 2. Disease Risk Check
                        db_res = risks.get('diabetes', '')
                        ht_res = risks.get('heart', '')
                        st_res = risks.get('stroke', '')
                        risk_warnings = []
                        if "High" in db_res: risk_warnings.append("High Diabetes Risk")
                        if "High" in ht_res: risk_warnings.append("High Heart Risk")
                        if "High" in st_res: risk_warnings.append("High Stroke Risk")  # NEW: Stroke alert
                        
                        if risk_warnings:
                            r_msg = "Critical Medical Risk Flagged"
                            
                            # A. Pop-up
                            st.toast(f"{r_msg}: {', '.join(risk_warnings)}", icon="🏥")
                            
                            # B. Sidebar
                            for r in risk_warnings:
                                if r not in st.session_state.active_alerts: st.session_state.active_alerts.append(r)
                            
                            # C. Chat Log
                            sys_r_msg = {"role": "system", "content": f"🚨 MEDICAL ALERT: {r_msg}. Please consult a doctor."}
                            if sys_r_msg not in st.session_state.chat_history:
                                st.session_state.chat_history.append(sys_r_msg)
                        
                        # 3. Sleep Quality Check (NEW)
                        sleep_res = wellness.get('sleep', {})
                        sleep_eff = sleep_res.get('efficiency_score', 100)
                        if sleep_eff < 70:
                            msg = "Poor Sleep Quality Detected!"
                            detail = f"Efficiency: {sleep_eff}%. Consider improving sleep hygiene."
                            
                            # A. Pop-up
                            st.toast(msg + " " + detail, icon="💤")
                            
                            # B. Sidebar
                            alert_txt = f"Sleep Efficiency: {sleep_eff}% (Low)"
                            if alert_txt not in st.session_state.active_alerts:
                                st.session_state.active_alerts.append(alert_txt)
                            
                            # C. Chat Log
                            sleep_msg = {"role": "system", "content": f"💤 SLEEP ALERT: {msg}\n{detail}"}
                            if sleep_msg not in st.session_state.chat_history:
                                st.session_state.chat_history.append(sleep_msg)


                        # --- DISPLAY RESULTS: STRUCTURED REPORT ---
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.success("Analysis Complete. Here is your structured health report.")
                        
                        # ZONE 1: MEDICAL RISKS (Risk Cards)
                        st.subheader("🛑 Zone 1: Critical Health Risks")
                        st.markdown("<div style='font-size:14px; color:#aaa; margin-bottom:15px;'>Based on clinical ML models trained on medical datasets.</div>", unsafe_allow_html=True)
                        
                        r1, r2, r3 = st.columns(3)
                        
                        def render_risk_card(title, risk_level, icon):
                            color_map = {"Low": "#22c55e", "Low Risk": "#22c55e", "Medium": "#eab308", "High": "#ef4444", "High Risk": "#ef4444"}
                            # Normalize risk level string
                            r_key = "High" if "High" in risk_level else "Medium" if "Medium" in risk_level else "Low"
                            ft_color = color_map.get(r_key, "#aaa")
                            bg_color = ft_color + "22" # 22 is hex for approx 13% opacity
                            
                            st.markdown(f"""
                            <div class="bento-box" style="padding: 20px; text-align: center; border: 1px solid {ft_color}; background: {bg_color};">
                                <div style="font-size: 30px; margin-bottom: 10px;">{icon}</div>
                                <div style="font-size: 14px; color: #ddd; margin-bottom: 5px;">{title}</div>
                                <div style="font-size: 20px; font-weight: 800; color: {ft_color};">{risk_level}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with r1: render_risk_card("Diabetes Risk", db_res, "🩸")
                        with r2: render_risk_card("Heart Disease Risk", ht_res, "❤️")
                        with r3: render_risk_card("Stroke Risk", st_res, "🧠")
                        
                        # ZONE 2: WELLNESS & LIFESTYLE (Detailed Cards)
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.subheader("🧬 Zone 2: Wellness & Vitality Scores")
                        st.markdown("<div style='font-size:14px; color:#aaa; margin-bottom:15px;'>AI assessment of your daily recovery and stress adaptation.</div>", unsafe_allow_html=True)

                        w1, w2 = st.columns(2)
                        with w1:
                            # Burnout
                            br = wellness.get('burnout', {})
                            st.markdown(f"""
                            <div class="bento-box" style="padding: 20px;">
                                <div style="display:flex; justify-content:space-between;">
                                    <div style="font-weight:bold; color:#facc15;">🔥 Burnout Risk</div>
                                    <div style="font-size:12px; background:#333; padding:2px 8px; border-radius:10px;">{br.get('level', 'N/A')}</div>
                                </div>
                                <div style="margin: 15px 0;">
                                    <span style="font-size: 36px; font-weight: bold; color:white;">{br.get('score', 0)}</span>
                                    <span style="font-size: 14px; color: #888;"> / 100</span>
                                </div>
                                <div style="font-size: 13px; color: #ccc; line-height: 1.5; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px;">
                                    {br.get('explanation', 'No data available')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with w2:
                            # Sleep
                            sr = wellness.get('sleep', {})
                            eff = sr.get('efficiency_score', 0)
                            factors = ", ".join(sr.get('factors', [])) if sr.get('factors') else "None identified"
                            st.markdown(f"""
                            <div class="bento-box" style="padding: 20px;">
                                <div style="display:flex; justify-content:space-between;">
                                    <div style="font-weight:bold; color:#60a5fa;">💤 Sleep Quality</div>
                                    <div style="font-size:12px; background:#333; padding:2px 8px; border-radius:10px;">AI Analysis</div>
                                </div>
                                <div style="margin: 15px 0;">
                                    <span style="font-size: 36px; font-weight: bold; color:white;">{eff}%</span>
                                    <span style="font-size: 14px; color: #888;"> Efficiency</span>
                                </div>
                                <div style="font-size: 13px; color: #ccc; line-height: 1.5; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px;">
                                    <b>Impact Factors:</b> {factors}<br>
                                    <span style="color:#aaa; font-style:italic;">Optimize these areas to improve Deep Sleep.</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        # ZONE 3: ACTIONS
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.subheader("💡 Zone 3: AI Action Plan")
                        
                        # Heuristic based Advice
                        recs = []
                        if "High" in db_res or "High" in ht_res:
                            recs.append("Consult a doctor immediately regarding cardiovascular/metabolic risks.")
                            recs.append("Reduce sugar and processed food intake.")
                        else:
                            recs.append("Maintenance: Keep up your moderate activity levels.")
                            
                        if burnout_res.get('score', 0) > 60:
                             recs.append("High Burnout Detected: Prioritize 15min downtime every 4 hours.")
                        if sleep_hrs < 6:
                             recs.append("Sleep Deprived: Aim for at least 7 hours to boost immunity.")
                        
                        # Fallback
                        if len(recs) < 3: recs.append("Stay hydrated: Aim for 2-3 liters of water daily.")
                        
                        for i, r in enumerate(recs[:3]):
                             st.markdown(f"""
                             <div style="padding: 10px 15px; margin-bottom: 8px; background: rgba(0, 242, 254, 0.05); border-left: 3px solid #00f2fe; border-radius: 4px;">
                                <span style="font-weight:bold; color:#00f2fe; margin-right:10px;">{i+1}.</span> {r}
                             </div>
                             """, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"An error occurred during verification: {e}")

    # --- TAB 4: AI DOCTOR (WEATHER AWARE) ---
    with t4:
        st.header("Chat with Dr. AI")
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if q := st.chat_input("Ask about your health..."):
            st.session_state.chat_history.append({"role":"user", "content":q})
            with st.chat_message("user"): st.markdown(q)
            
            with st.chat_message("assistant"):
                try:
                    # 1. Weather Context
                    w_ctx = ""
                    try:
                        coords = get_coordinates(st.session_state.weather_loc)
                        if coords:
                            w_data = get_weather_forecast(coords['lat'], coords['lon'])['current']
                            w_ctx = f"CURRENT WEATHER in {coords['name']}: {w_data['temp']}°C, {w_data['condition']}. UV Index: {w_data['uv']}."
                    except: w_ctx = "Weather context: Currently unavailable."

                    # 2. Vitals & Profile (ENHANCED CONTEXT)
                    v_txt = "Using Manual Inputs (Device Not Connected)"
                    w_real = {}
                    if st.session_state.device_connected:
                        w_real = get_wearable_data()
                        v_txt = (
                            f"REAL-TIME VITALS: "
                            f"Heart Rate: {w_real.get('heart_rate','?')} bpm, "
                            f"Resting HR: {w_real.get('resting_heart_rate','?')} bpm, "
                            f"Steps: {w_real.get('steps',0)}, "
                            f"SpO2: {w_real.get('spo2','?')}%, "
                            f"HRV(RMSSD): {w_real.get('hrv_rmssd_ms','?')} ms, "
                            f"Stress Score: {w_real.get('stress_score','?')}/100, "
                            f"Sleep: {w_real.get('sleep_duration_hours','?')}h (Eff: {w_real.get('sleep_efficiency','?')}%)"
                        )
                    
                    p = st.session_state.user_profile
                    # Extract recent predictions if available
                    risks = p.get('risks', {})
                    wellness = p.get('wellness', {})
                    
                    p_txt = (
                        f"USER PROFILE: "
                        f"Age: {p.get('age','?')}y, "
                        f"Weight: {p.get('weight','?')}kg, "
                        f"Height: {p.get('height','?')}cm, "
                        f"Gender: {p.get('gender','?')}, "
                        f"BMI: {p.get('bmi','?')}, "
                        f"Medical Risks: {risks}, "
                        f"Wellness Status: {wellness}"
                    )
                    
                    # 3. RAG Search
                    docs = rag_search(q)
                    rag_text = "\n".join(docs)
                    
                    # 4. Prompt Engineering (STRICT GUARDRAILS)
                    prompt = f"""
                    
                    SYSTEM INSTRUCTIONS:
                    You are a dedicated AI Health Coach.
                    
                    ROLE:
                    - Provide health, wellness, and lifestyle guidance.
                    - Provide diagnosis-related educational information.
                    - You are NOT a doctor.

                    --- ALLOWED SCOPE ---
                    1. General health, wellness, fitness, sleep, stress, hydration.
                    2. Lifestyle improvement and preventive care.
                    3. Weather impact on health.
                    4. Diagnosis-related education:
                        - Explain symptoms in general terms
                        - Explain what test values generally indicate (e.g., blood sugar, BP, BMI),
                          without giving thresholds for diagnosis
                        - Explain how doctors evaluate conditions
                        - Explain when medical attention is needed

                    --- STRICT MEDICAL SAFETY RULES ---
                    1. Do NOT confirm or deny any disease.
                    2. Do NOT say phrases like:
                    "you have", "you don't have", "it seems like", "likely", "unlikely".
                    3. Do NOT prescribe medicines or dosages.
                    4. Do NOT give final diagnosis.
                    5. If symptoms are serious, clearly advise consulting a doctor.
                    6. Do NOT name specific diseases unless the user explicitly mentions them,
                    and even then, explain evaluation only.

                    --- DISALLOWED TOPICS ---
                    - Coding, politics, entertainment, general knowledge.
                    IF out of scope, reply exactly:
                    "I’m a health-focused assistant. Please ask health or lifestyle-related questions."

                    --- HARMFUL CONTENT ---
                    STRICTLY refuse self-harm, violence, or illegal requests.
                    Reply exactly:
                    "I cannot assist with that request. I am here to help with health and wellness only."

                    --- TONE ---
                    Calm, supportive, simple, and non-alarmist.

                    --- COMPREHENSIVE CONTEXT ---
                    [ENVIRONMENT]
                    {w_ctx}

                    [PATIENT DATA]
                    {v_txt}
                    {p_txt}
                    
                    --- LOGIC RULES FOR AI (Do not mention these explicitly to user) ---
                    1. **Burnout Score (0-100)**:
                       - > 70 (High): Advise immediate rest, disconnect from work, and consider professional help.
                       - 30-70 (Medium): Suggest stress management, better sleep hygiene, and light exercise.
                       - < 30 (Low): Encourage maintaining current healthy habits.
                    
                    2. **Sleep Efficiency (0-100%)**:
                       - < 80%: Ask about caffeine, screen time, or stress. Suggest a bedtime routine.
                       - > 90%: Praise good sleep health.
                    
                    3. **Integration**:
                       - If Burnout is High AND Sleep Efficiency is Low, prioritize SLEEP RECOVERY advice first.
                       - If Heart/Stroke risk is present, link stress/sleep management to heart health (e.g., "Good sleep helps lower blood pressure").

                    --- RETRIEVED MEDICAL GUIDELINES ---
                    {rag_text}

                    --- USER QUESTION ---
                    {q}

                    --- RESPONSE INSTRUCTIONS ---
                    1. FIRST, analyze the [PATIENT DATA] and [ENVIRONMENT] above.
                    2. SECOND, check the [RETRIEVED MEDICAL GUIDELINES] for relevant info.
                    3. SYNTHESIZE a helpful response.
                    4. ALWAYS reference specific values if applicable (e.g., "Given your burnout score of 85...", "Since the air quality is poor...", "With a history of high BP...").
                    5. If the User's data is missing or '?', general advice is okay, but mention that personalization is limited.
                    6. Be Educational, Supportive, and Clear.
                    7. STRICTLY ADHERE to Safety Rules (No Diagnosis).

                    ASSISTANT RESPONSE:

                    """

                    # 5. API Call (AGENTIC LOOP)
                    import json
                    
                    # First Pass: Ask LLM
                    resp = requests.post(
                        "https://api.mistral.ai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                        json={
                            "model": "mistral-tiny", 
                            "messages": [{"role": "user", "content": prompt}]
                            # Removed JSON mode to allow normal conversations
                        }
                    )
                    
                    final_ans = ""
                    
                    if resp.status_code == 200:
                        content = resp.json()['choices'][0]['message']['content']
                        
                        # Simple conversation - no tool calling
                        final_ans = content
                        
                        # Clean up response
                        st.markdown(final_ans)
                        st.session_state.chat_history.append({"role": "assistant", "content": final_ans})
                    else:
                        st.error(f"AI Service Error: {resp.text}")
                except Exception as e:
                    st.error(f"System Error: {e}")

    # --- TAB 5: WORKOUT PLANNER ---
    with t5:
        st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>🏋️ Dynamic AI Workout Planner</h2>", unsafe_allow_html=True)
        
        # --- INPUTS (Hidden calculations for Context) ---
        w_cond = "Unknown"
        temp = "?"
        try:
            coords = get_coordinates(st.session_state.weather_loc)
            wd = get_weather_forecast(coords['lat'], coords['lon'])['current']
            w_cond = wd['condition']
            temp = wd['temp']
        except: pass
        
        # Gather wearable data (enhanced with more vitals)
        vitals_data = {'steps': 0}
        if st.session_state.device_connected:
            v = get_wearable_data()
            vitals_data = {
                'steps': v['steps'],
                'heart_rate': v.get('heart_rate'),
                'resting_heart_rate': v.get('resting_heart_rate'),
                'hrv_rmssd_ms': v.get('hrv_rmssd_ms'),
                'stress_score': v.get('stress_score'),
                'sleep_score': v.get('sleep_score')
            }

        # Center the Generate Button
        st.markdown("<br>", unsafe_allow_html=True)
        c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
        with c_btn2:
             if st.button("💪 GENERATE MY WORKOUT PLAN", use_container_width=True, type="primary"):
                 with st.spinner("Creating your personalized routine..."):
                     # Pass health risks and wellness data (NEW)
                     plan = generate_workout_plan(
                         w_cond, 
                         vitals_data,
                         st.session_state.user_profile,
                         risks=st.session_state.user_profile.get('risks', {}),
                         wellness=st.session_state.user_profile.get('wellness', {})
                     )
                     st.session_state['workout_plan'] = plan
        
        if 'workout_plan' in st.session_state:
            p = st.session_state['workout_plan']
            
            st.markdown("---")
            
            # --- 7. WHY THIS WORKOUT? ---
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; margin-bottom: 25px; border-left: 4px solid #8b5cf6;">
                <div style="font-weight: bold; color: #8b5cf6; margin-bottom: 5px;">🤖 Why this workout?</div>
                <div style="font-style: italic; color: #e0e0e0;">"{p.get('reason', 'Tailored for your current conditions.')}"</div>
            </div>
            """, unsafe_allow_html=True)
            
            # --- 4. STRUCTURED FORMAT (Type, Duration, Intensity, Time) ---
            # Using 4 columns for clear structured display
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"<div class='bento-box' style='padding:15px; text-align:center;'><div style='color:#aaa; font-size:12px;'>Type</div><div style='font-weight:bold; font-size:18px;'>{p.get('workout_type', 'General')}</div></div>", unsafe_allow_html=True)
            with m2:
                st.markdown(f"<div class='bento-box' style='padding:15px; text-align:center;'><div style='color:#aaa; font-size:12px;'>Duration</div><div style='font-weight:bold; font-size:18px;'>{p.get('total_duration', '30m')}</div></div>", unsafe_allow_html=True)
            with m3:
                st.markdown(f"<div class='bento-box' style='padding:15px; text-align:center;'><div style='color:#aaa; font-size:12px;'>Intensity</div><div style='font-weight:bold; font-size:18px;'>{p.get('intensity', 'Medium')}</div></div>", unsafe_allow_html=True)
            with m4:
                st.markdown(f"<div class='bento-box' style='padding:15px; text-align:center;'><div style='color:#aaa; font-size:12px;'>Time</div><div style='font-weight:bold; font-size:18px;'>{p.get('recommended_time', 'Anytime')}</div></div>", unsafe_allow_html=True)

            # --- 6. SAFETY & WEATHER NOTES ---
            st.warning(f"⚠️ **Safety & Weather**: {p.get('safety_notes', 'Stay hydrated and listen to your body.')}")
            
            # --- 5. EXERCISE BREAKDOWN ---
            st.subheader("📋 Exercise Breakdown")
            for i, ex in enumerate(p.get('exercises', [])):
                notes = ex.get('notes', '')
                notes_html = ""
                if notes and notes.lower() != "no specific notes":
                    notes_html = f"<div style='font-size: 13px; color: #bbb; margin-top: 5px;'>📝 {notes}</div>"
                
                st.markdown(f"""<div style="display: flex; align-items: center; background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.05);">
<div style="font-size: 18px; font-weight: bold; color: #00f2fe; margin-right: 20px; width: 25px;">{i+1}.</div>
<div style="flex: 1;">
<div style="font-size: 16px; font-weight: 600; color: white;">{ex.get('name', 'Exercise')}</div>
{notes_html}
</div>
<div style="background: rgba(0, 242, 254, 0.1); padding: 8px 12px; border-radius: 8px; font-family: monospace; color: #00f2fe; white-space: nowrap; font-weight: bold;">
{ex.get('duration', '1 min')}
</div>
</div>""", unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="text-align: center; color: #888; margin-top: 50px;">
                <p>Click the button above to generate a workout tailored to your weather, energy levels, and profile.</p>
            </div>
            """, unsafe_allow_html=True)

if st.session_state.auth_status == 'logged_in': main_app()
else: login_page()
