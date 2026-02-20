from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
import requests

# Import internal services
# Note: Since we are in backend/, these imports should work relative to logic
from database import init_db, register_user, login_user, update_profile
from services.wearable_service import get_wearable_data
from services.weather_service import get_weather_and_aqi
from services.weather_health_rules import weather_health_rules
from services.ml_diabetes import predict_diabetes
from services.ml_heart import predict_heart
from services.ml_stroke import predict_stroke
from rag.rag_service import rag_search

app = FastAPI(title="AI Health Coach API")

# CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB on startup
@app.on_event("startup")
def startup_event():
    init_db()

# --- MODELS ---
class UserAuth(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    username: str
    profile_data: Dict[str, Any]

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict] = {}

class PredictionRequest(BaseModel):
    data: Dict[str, Any]

# --- ROUTES: AUTH ---
@app.post("/auth/register")
def register(user: UserAuth):
    success, msg = register_user(user.username, user.password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": "Registration successful"}

@app.post("/auth/login")
def login(user: UserAuth):
    success, profile = login_user(user.username, user.password)
    if not success:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": user.username, "profile": profile, "token": "fake-jwt-token-for-demo"}

@app.post("/auth/update_profile")
def update_user_profile(up: UserProfile):
    update_profile(up.username, up.profile_data)
    return {"message": "Profile updated"}

# --- ROUTES: DATA ---
@app.get("/data/wearable")
def get_wearable():
    return get_wearable_data()

@app.get("/data/weather")
def get_weather(lat: float = 19.07, lon: float = 72.87):
    # Default to Mumbai if not provided
    try:
        data = get_weather_and_aqi(lat, lon)
        rules = weather_health_rules(data)
        return {"weather": data, "advisories": rules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ROUTES: PREDICTION ---
@app.post("/predict/diabetes")
def api_predict_diabetes(req: PredictionRequest):
    try:
        # Defaults handled in frontend or basic logic, service expects dict
        result = predict_diabetes(req.data)
        return {"risk": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/heart")
def api_predict_heart(req: PredictionRequest):
    try:
        result = predict_heart(req.data)
        return {"risk": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/stroke")
def api_predict_stroke(req: PredictionRequest):
    try:
        result = predict_stroke(req.data)
        return {"risk": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ROUTES: CHAT ---
@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """
    Combines RAG + Mistral for a comprehensive reply.
    """
    try:
        # 1. RAG Search
        try:
            rag_docs = rag_search(req.message)
            rag_context = "\n".join(rag_docs)
        except:
            rag_context = "No specific guidelines found."

        # 2. Construct System Prompt
        # Context from frontend (vitals, profile) is passed in req.context
        ctx = req.context
        vitals = ctx.get("vitals", "Unknown")
        profile = ctx.get("profile", "Unknown")
        weather = ctx.get("weather", "Unknown")

        system_prompt = (
            f"Act as a compassionate, expert AI Doctor.\n"
            f"--- PATIENT CONTEXT ---\n"
            f"Vitals: {vitals}\n"
            f"Profile: {profile}\n"
            f"Environment: {weather}\n"
            f"--- MEDICAL GUIDELINES (RAG) ---\n{rag_context}\n"
            f"----------------------\n"
            f"Answer the user's question safely and professionally."
        )

        MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
        if not MISTRAL_API_KEY:
             return {"reply": "Configuration Error: API Key missing on backend."}
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-tiny",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message}
            ]
        }
        
        # Direct Request
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return {"reply": response.json()["choices"][0]["message"]["content"]}
        else:
            return {"reply": f"I'm sorry, I'm having trouble thinking right now. (API Error: {response.text})"}

    except Exception as e:
        print(f"Chat Error: {e}")
        return {"reply": "I'm sorry, an internal error occurred."}

if __name__ == "__main__":
    import uvicorn
    # Allow running directly for testing
    uvicorn.run(app, host="0.0.0.0", port=8000)
