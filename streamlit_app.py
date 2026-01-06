import streamlit as st
import requests
import pandas as pd

# --- CONFIG ---
API_URL = "http://127.0.0.1:8000/api/v1"
st.set_page_config(page_title="JIJU Health Portal", page_icon="❤️", layout="wide")

# --- AUTH STATE ---
if "user" not in st.session_state: st.session_state["user"] = None
if "plan_data" not in st.session_state: st.session_state["plan_data"] = None

def login(username):
    try:
        res = requests.get(f"{API_URL}/patient/login/{username}")
        if res.status_code == 200:
            st.session_state["user"] = res.json()
            st.rerun()
        else: st.error("User not found! Try 'john_doe' or 'dr_house'.")
    except: st.error("Server Offline")

def logout():
    st.session_state["user"] = None
    st.session_state["plan_data"] = None
    st.rerun()

# ==========================================
# 🔐 SCREEN 1: LOGIN
# ==========================================
if not st.session_state["user"]:
    col1, col2 = st.columns([1, 2])
    with col1: st.image("https://cdn-icons-png.flaticon.com/512/883/883360.png", width=150)
    with col2:
        st.title("JIJU Health Portal")
        st.markdown("### AI-Powered Cardiac Rehab")
        user_input = st.text_input("Enter Username")
        if st.button("Login"): login(user_input)
    st.info("Demo: 'john_doe' (Patient) | 'dr_house' (Doctor)")

# ==========================================
# 🏥 SCREEN 2: MAIN APP
# ==========================================
else:
    user = st.session_state["user"]
    
    with st.sidebar:
        st.header(f"👤 {user['full_name']}")
        st.caption(f"Role: {user['role'].upper()}")
        if st.button("Logout"): logout()

    # ----------------------------------------------------
    # 🏃 PATIENT VIEW
    # ----------------------------------------------------
    if user["role"] == "patient":
        st.title("My Health Dashboard")
        
        tab1, tab2 = st.tabs(["📝 New Workout", "📊 History & Streak"])
        
        # --- TAB 1: PREDICTION ---
        with tab1:
            with st.form("health_form"):
                c1, c2, c3 = st.columns(3)
                age = c1.number_input("Age", 18, 100, 25)
                weight = c2.number_input("Weight (kg)", 40.0, 150.0, 75.0)
                rhr = c3.number_input("Resting HR", 40, 120, 65)
                c4, c5, c6 = st.columns(3)
                sys = c4.number_input("Systolic BP", 90, 200, 120)
                dia = c5.number_input("Diastolic BP", 50, 130, 80)
                borg_before = c6.slider("Fatigue Level (Borg Before)", 6, 20, 6, help="6=No fatigue, 20=Exhausted")

                if st.form_submit_button("Get Plan"):
                    payload = {"age": age, "weight": weight, "resting_hr": rhr, "bp_systolic": sys, "bp_diastolic": dia, "borg_rating_before": borg_before}
                    res = requests.post(f"{API_URL}/patient/predict/{user['id']}", json=payload)
                    if res.status_code == 200: st.session_state["plan_data"] = res.json()
            
            # SHOW RESULTS
            if st.session_state["plan_data"]:
                data = st.session_state["plan_data"]
                
                if data["is_urgent"]: st.error("⚠️ HIGH RISK: Intensity lowered to LOW.")
                else: st.success(f"✅ Approved for {data['predicted_intensity']} Intensity")
                
                c1, c2 = st.columns([2,1])
                c1.video(data["youtube_link"])
                c2.metric("Target HR", f"{data['target_hr_min']} - {data['target_hr_max']}")
                c2.metric("Est. Calories", f"{data['calories_burned']} kcal")
                
                st.divider()
                st.subheader("Post-Workout Feedback")
                with st.form("feedback"):
                    borg = st.slider("Borg Scale (Exertion 6-20)", 6, 20, 13)
                    mood = st.select_slider("Mood", ["Happy", "Sad", "Tired", "Energetic"])
                    if st.form_submit_button("Save Log"):
                        requests.patch(f"{API_URL}/patient/feedback/{data['id']}", 
                                     json={"borg_rating": borg, "mood": mood, "symptoms": []})
                        st.success("Saved!")
                        st.session_state["plan_data"] = None # Reset

        # --- TAB 2: HISTORY ---
        with tab2:
            res = requests.get(f"{API_URL}/patient/history/{user['id']}")
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                if not df.empty:
                    # Streak Logic
                    df['date'] = pd.to_datetime(df['timestamp']).dt.date
                    streak = len(df['date'].unique())
                    
                    m1, m2 = st.columns(2)
                    m1.metric("🔥 Active Streak", f"{streak} Days")
                    m2.metric("⚡ Total Calories", f"{int(df['calories_burned'].sum())}")
                    
                    st.dataframe(df[["timestamp", "predicted_intensity", "borg_rating", "mood"]])
                else: st.info("No history yet.")

    # ----------------------------------------------------
    # 👨‍⚕️ DOCTOR VIEW
    # ----------------------------------------------------
    elif user["role"] == "doctor":
        st.title("Clinician Dashboard")
        if st.button("Refresh"): st.rerun()
        
        res = requests.get(f"{API_URL}/doctor/dashboard")
        if res.status_code == 200:
            records = res.json()
            if records:
                df = pd.DataFrame(records)
                
                # URGENT ALERTS
                urgent = df[df["is_urgent"] == True]
                if not urgent.empty:
                    st.error(f"{len(urgent)} Urgent Cases!")
                    st.dataframe(urgent)
                
                st.subheader("Patient Records")
                st.dataframe(df[["id", "patient_id", "timestamp", "predicted_intensity", "borg_rating", "mood"]])
                
                # OVERRIDE TOOL
                st.divider()
                st.subheader("Modify Prescription")
                c1, c2, c3 = st.columns([1,2,1])
                rec_id = c1.selectbox("Record ID", df["id"].unique())
                new_int = c2.selectbox("New Intensity", ["Low", "Moderate", "High"])
                if c3.button("Update"):
                    requests.patch(f"{API_URL}/doctor/override/{rec_id}", params={"new_intensity": new_int})
                    st.success("Updated!")
                    st.rerun()
            else: st.info("No records found.")