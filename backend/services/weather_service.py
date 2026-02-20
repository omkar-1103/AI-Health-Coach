import requests
from datetime import datetime

# OpenMeteo is free and requires no API key for non-commercial use.

def get_coordinates(city_name):
    """
    Fetch latitude and longitude for a given city name.
    """
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        res = requests.get(url).json()
        
        if "results" in res and len(res["results"]) > 0:
            data = res["results"][0]
            return {
                "lat": data["latitude"], 
                "lon": data["longitude"], 
                "name": data["name"], 
                "country": data.get("country", "")
            }
        return None
    except Exception as e:
        print(f"Geocoding Error: {e}")
        return None

def get_weather_forecast(lat, lon):
    """
    Fetch comprehensive weather data: current, daily forecast, and hourly forecast.
    """
    try:
        # Request parameters for OpenMeteo
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,weather_code,surface_pressure,wind_speed_10m",
            "hourly": "temperature_2m,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max",
            "timezone": "auto",
            "forecast_days": 6  # 5 days + today
        }
        
        url = "https://api.open-meteo.com/v1/forecast"
        res = requests.get(url, params=params).json()
        
        # Process Current
        curr = res["current"]
        daily = res["daily"]
        hourly = res["hourly"]
        
        # Helper for WMO codes
        def get_desc(code):
            # Simple WMO code mapping
            if code == 0: return "Clear Sky", "☀️"
            if code in [1,2,3]: return "Partly Cloudy", "⛅"
            if code in [45,48]: return "Foggy", "🌫️"
            if code in [51,53,55]: return "Drizzle", "🌦️"
            if code in [61,63,65]: return "Rain", "🌧️"
            if code in [71,73,75]: return "Snow", "❄️"
            if code in [80,81,82]: return "Showers", "🌧️"
            if code in [95,96,99]: return "Thunderstorm", "⛈️"
            return "Unknown", "❓"

        def safe_round(val):
            try:
                if val is None: return 0
                return round(val)
            except: return 0

        desc, icon = get_desc(curr.get("weather_code", 0))
        
        # Format Sunrise/Sunset (ISO string to time)
        try:
            sunrise = datetime.fromisoformat(daily["sunrise"][0]).strftime("%I:%M %p")
            sunset = datetime.fromisoformat(daily["sunset"][0]).strftime("%I:%M %p")
        except:
            sunrise = "06:00 AM"
            sunset = "06:00 PM"

        # Construct Data Object
        weather_data = {
            "current": {
                "temp": safe_round(curr.get("temperature_2m")),
                "feels_like": safe_round(curr.get("apparent_temperature")),
                "humidity": curr.get("relative_humidity_2m", 0),
                "wind_speed": curr.get("wind_speed_10m", 0),
                "pressure": curr.get("surface_pressure", 1000),
                "uv": daily.get("uv_index_max", [0])[0], 
                "sunrise": sunrise,
                "sunset": sunset,
                "condition": desc,
                "icon": icon,
                "is_day": curr.get("is_day", 1)
            },
            "daily": [],
            "hourly": []
        }
        
        # Process Daily (Next 5 days)
        d_codes = daily.get("weather_code", [])
        d_times = daily.get("time", [])
        d_max = daily.get("temperature_2m_max", [])
        d_min = daily.get("temperature_2m_min", [])
        
        # Check lengths to be safe
        max_daily_idx = min(len(d_times), len(d_codes), len(d_max), len(d_min), 6)
        
        for i in range(1, max_daily_idx): # Start from 1 (tomorrow) up to available
            d_desc, d_icon = get_desc(d_codes[i])
            try:
                date_obj = datetime.strptime(d_times[i], "%Y-%m-%d")
                d_name = date_obj.strftime("%A")
                d_full = date_obj.strftime("%d %b")
            except:
                d_name = "Day"
                d_full = "--"

            weather_data["daily"].append({
                "date": d_times[i],
                "day_name": d_name,
                "full_date": d_full,
                "max_temp": safe_round(d_max[i]),
                "min_temp": safe_round(d_min[i]),
                "condition": d_desc,
                "icon": d_icon
            })
            
        # Process Hourly
        current_hour_index = datetime.now().hour
        if current_hour_index < 0: current_hour_index = 0
        
        # safely get array lengths
        h_times = hourly.get("time", [])
        h_codes = hourly.get("weather_code", [])
        h_temps = hourly.get("temperature_2m", [])
        h_winds = hourly.get("wind_speed_10m", [])
        
        limit_hourly = min(len(h_times), len(h_codes), len(h_temps), len(h_winds))

        for i in range(0, 5): 
            idx = current_hour_index + (i * 3)
            if idx >= limit_hourly: break
            
            try:
                h_time_str = h_times[idx]
                h_obj = datetime.fromisoformat(h_time_str)
                h_time_fmt = h_obj.strftime("%H:%M")
            except:
                h_time_fmt = "--:--"

            h_desc, h_icon = get_desc(h_codes[idx])
            
            weather_data["hourly"].append({
                "time": h_time_fmt,
                "temp": safe_round(h_temps[idx]),
                "icon": h_icon,
                "wind": h_winds[idx]
            })
            
        return weather_data
    except Exception as e:
        print(f"Weather Fetch Error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Keep the old function signature for backward compatibility just in case, but redirect
def get_weather_and_aqi(lat, lon):
    # This was used in the old code. We can adapt it or just fetch the new data.
    # The old code expected simple dict.
    w = get_weather_forecast(lat, lon)
    if w:
        return {
            "temperature": w["current"]["temp"],
            "humidity": w["current"]["humidity"],
            "aqi": 50, # Placeholder as OpenMeteo Separate API needed for AQI, keeping it simple for now
            "pressure": w["current"]["pressure"],
            "condition": w["current"]["condition"]
        }
    return {}
