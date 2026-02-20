
import streamlit as st
from backend.database import update_profile, login_user
from backend.services.analysis_service import run_holistic_checkup

def update_profile_wrapper(username, key, value):
    """
    Safely updates a single key in the user's profile.
    Args:
        username (str): The logged-in user.
        key (str): Metric to update (e.g., 'weight', 'step_goal').
        value (any): The new value.
    Returns:
        str: Success or error message.
    """
    if 'user_profile' not in st.session_state or not username:
         return "Error: User not authenticated."

    # 1. Get current profile to avoid overwriting other fields
    current_profile = st.session_state.user_profile.copy()
    
    # 2. Update the specific key
    # Handle nested updates (optional, for now flat is fine or simple dicts)
    current_profile[key] = value
    
    # 3. Recalculate BMI if weight or height changed
    if key in ['weight', 'height']:
        weight = current_profile.get('weight', 70)
        height = current_profile.get('height', 170)
        current_profile['bmi'] = round(weight / ((height/100)**2), 2)
    
    # 4. AUTO-ANALYSIS: Run holistic checkup to refresh risks and wellness
    try:
        risks, wellness = run_holistic_checkup(current_profile)
        current_profile['risks'] = risks
        current_profile['wellness'] = wellness
    except Exception as e:
        # If analysis fails, continue with profile update but log the issue
        pass
    
    # 5. Save to DB
    try:
        update_profile(username, current_profile)
        # 6. Update Session State immediately so UI reflects it
        st.session_state.user_profile = current_profile
        
        # 7. SYNC WITH FORM WIDGETS
        # The form widgets use keys like 'form_weight', 'form_age'. We must update them too.
        form_key = f"form_{key}"
        if form_key in st.session_state:
            st.session_state[form_key] = value
            
        return f"Successfully updated {key} to {value}."
    except Exception as e:
        return f"Database Error: {str(e)}"

def get_available_tools_prompt():
    return """
    AVAILABLE TOOLS:
    1. update_metric(key: str, value: int/float/str)
       - Use this to update user profile data like 'weight', 'height', 'age'.
       - Use this to update goals like 'step_goal' (default is 10000).
    
    FORMAT:
    If you decide to use a tool, you MUST output ONLY valid JSON:
    {
        "tool": "update_metric",
        "args": { "key": "weight", "value": 75 }
    }
    """
