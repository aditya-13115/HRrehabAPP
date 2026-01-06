import streamlit as st
import requests
import pandas as pd

# --- CONFIG ---
API_URL = "http://127.0.0.1:8000/api/v1"
st.set_page_config(page_title="JIJU RECAP Portal", page_icon="❤️", layout="wide")

if "user" not in st.session_state: st.session_state["user"] = None
if "plan_data" not in st.session_state: st.session_state["plan_data"] = None

# --- BORG SCALE DESCRIPTIONS ---
BORG_DESC = {
    6: "No exertion at all (Sitting, lying down)",
    7: "Extremely light (Very relaxed walking)",
    8: "Extremely light (Almost effortless)",
    9: "Very light (Slow walking)",
    10: "Very light (Easy activity)",
    11: "Light (Comfortable, can talk easily)",
    12: "Light (Slightly increased breathing)",
    13: "Somewhat hard (Noticeable effort, talking harder)",
    14: "Somewhat hard (Breathing heavier, focused)",
    15: "Hard (Difficult to talk continuously)",
    16: "Hard (Heavy breathing, tiring)",
    17: "Very hard (Can only speak few words)",
    18: "Very hard (Extremely exhausting)",
    19: "Extremely hard (Near maximal effort)",
    20: "Maximal exertion (Absolute maximum effort)"
}

# --- AUTH FUNCTIONS ---
def login(username):
    try:
        res = requests.get(f"{API_URL}/patient/login/{username}")
        if res.status_code == 200:
            st.session_state["user"] = res.json()
            st.rerun()
        else: st.error("User not found.")
    except: st.error("Server Offline")

def logout():
    st.session_state["user"] = None
    st.session_state["plan_data"] = None
    st.rerun()

# ==========================================
# 🔐 SCREEN 1: LOGIN & REGISTER
# ==========================================
if not st.session_state["user"]:
    c1, c2 = st.columns([1,2])
    with c1: st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=120)
    with c2:
        st.title("JIJU RECAP Portal")
        auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with auth_tab1:
            user_input = st.text_input("Username", key="login_u")
            if st.button("Login"): login(user_input)

        with auth_tab2:
            new_u = st.text_input("Username", key="reg_u")
            new_n = st.text_input("Full Name", key="reg_n")
            new_role = st.selectbox("Role", ["patient", "doctor"])
            
            c_a, c_b = st.columns(2)
            reg_age = c_a.number_input("Age", 18, 100, 30)
            reg_sex = c_b.selectbox("Gender", ["M", "F"])
            
            if st.button("Sign Up"):
                payload = {"username": new_u, "full_name": new_n, "role": new_role}
                res = requests.post(f"{API_URL}/auth/register", json=payload)
                if res.status_code == 200:
                    user_id = res.json()["user_id"]
                    requests.patch(f"{API_URL}/patient/profile/{user_id}", json={"age": reg_age, "gender": reg_sex})
                    st.success("Account created! Please Login.")
                else: st.error("Registration failed.")

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

        # --- 1. GLOBAL STATS (Moved to top for visibility) ---
        try:
            h_res = requests.get(f"{API_URL}/patient/history/{user['id']}")
            hist_df = pd.DataFrame()
            if h_res.status_code == 200:
                h_data = h_res.json()
                if h_data:
                    hist_df = pd.DataFrame(h_data)
                    # Metrics Calculation
                    hist_df['date'] = pd.to_datetime(hist_df['timestamp']).dt.date
                    streak_days = len(hist_df['date'].unique())
                    total_cals = int(hist_df['calories_burned'].sum())
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("🔥 Active Streak", f"{streak_days} Days")
                    m2.metric("⚡ Total Burn", f"{total_cals} kcal")
                    m3.metric("📝 Total Sessions", len(hist_df))
                    st.divider()
        except:
            st.error("Could not load stats.")
        
        tab_profile, tab_predict, tab_hist = st.tabs(["👤 My Profile", "💪 New Session", "📊 History & Remarks"])
        
        # --- TAB 1: PROFILE ---
        with tab_profile:
            st.subheader("Edit Personal Details")
            with st.form("profile_update"):
                c1, c2 = st.columns(2)
                p_age = c1.number_input("Age", 18, 100, user.get('age', 30))
                p_sex = c2.selectbox("Gender", ["M", "F"], index=0 if user.get('gender')=='M' else 1)
                
                if st.form_submit_button("Update Profile"):
                    res = requests.patch(f"{API_URL}/patient/profile/{user['id']}", json={"age": p_age, "gender": p_sex})
                    if res.status_code == 200:
                        st.session_state["user"]["age"] = p_age
                        st.session_state["user"]["gender"] = p_sex
                        st.success("Profile Updated!")
                        st.rerun()

        # --- TAB 2: PREDICTION ---
        with tab_predict:
            st.subheader("Pre-Workout Vitals")
            with st.form("predict_form"):
                c1, c2, c3 = st.columns(3)
                weight = c1.number_input("Weight (kg)", 40.0, 150.0, 75.0)
                rhr = c2.number_input("Resting HR", 40, 120, 65)
                pulse = c3.number_input("Pulse Rate (Current)", 40, 150, 70)

                c4, c5, c6 = st.columns(3)
                sys = c4.number_input("Systolic BP", 90, 200, 120)
                dia = c5.number_input("Diastolic BP", 50, 130, 80)
                resp = c6.number_input("Resp. Rate", 10, 40, 16)

                st.markdown("**Pre-existing Conditions:**")
                cc1, cc2 = st.columns(2)
                has_htn = cc1.checkbox("Hypertension (HTN)")
                has_dm = cc2.checkbox("Diabetes (DM)")
                
                st.divider()
                st.markdown("**How do you feel right now? (Borg Scale)**")
                borg_val = st.slider("", 6, 20, 6)
                st.info(f"**Level {borg_val}:** {BORG_DESC[borg_val]}")
                
                if st.form_submit_button("Generate Plan"):
                    payload = {
                        "weight": weight, "resting_hr": rhr, 
                        "bp_systolic": sys, "bp_diastolic": dia,
                        "pulse_rate_before": pulse, "respiratory_rate_before": resp,
                        "borg_rating_before": borg_val,
                        "has_htn": has_htn, "has_dm": has_dm
                    }
                    res = requests.post(f"{API_URL}/patient/predict/{user['id']}", json=payload)
                    if res.status_code == 200: st.session_state["plan_data"] = res.json()
                    else: st.error(res.text)

            if st.session_state["plan_data"]:
                data = st.session_state["plan_data"]
                st.divider()
                if data["is_urgent"]: st.error("⚠️ HIGH RISK DETECTED.")
                else: st.success(f"✅ Target: {data['predicted_intensity']} Intensity")
                st.video(data["youtube_link"])
                
                st.subheader("Post-Workout Check-in")
                with st.form("feedback_form"):
                    fb_borg = st.slider("Exertion Level (After)", 6, 20, 13)
                    fb_mood = st.select_slider("Mood", ["Happy", "Sad", "Tired", "Energetic"])
                    if st.form_submit_button("Save Log"):
                        requests.patch(f"{API_URL}/patient/feedback/{data['id']}", 
                                     json={"borg_rating": fb_borg, "mood": fb_mood, "symptoms": []})
                        st.success("Logged!")
                        st.session_state["plan_data"] = None

        # --- TAB 3: HISTORY & REMARKS (Updated) ---
        with tab_hist:
            if not hist_df.empty:
                # Ensure doctor_note column exists
                if "doctor_note" not in hist_df.columns:
                    hist_df["doctor_note"] = "No remarks"
                
                st.markdown("### Your Activity Log & Clinical Feedback")
                # Show key columns including Doctor's Note
                display_cols = ["timestamp", "predicted_intensity", "borg_rating_before", "doctor_note"]
                final_cols = [c for c in display_cols if c in hist_df.columns]
                
                st.dataframe(hist_df[final_cols], use_container_width=True)
            else:
                st.info("No records found.")

    # ----------------------------------------------------
    # 👨‍⚕️ DOCTOR VIEW (Username Selector + Detailed View)
    # ----------------------------------------------------
    elif user["role"] == "doctor":
        st.title("👨‍⚕️ Clinical Command Center")
        
        try:
            res = requests.get(f"{API_URL}/doctor/dashboard")
            if res.status_code == 200:
                all_records = res.json()
                if not all_records:
                    st.info("No records found in the system.")
                else:
                    df = pd.DataFrame(all_records)
                    # Ensure columns exist
                    if "symptoms" not in df.columns: df["symptoms"] = "None"
                    if "calories_burned" not in df.columns: df["calories_burned"] = 0
                    if "is_urgent" not in df.columns: df["is_urgent"] = False
                    if "patient_username" not in df.columns: df["patient_username"] = "Unknown"

                    # 1. GLOBAL ALERTS
                    urgent_cases = df[
                        (df["is_urgent"] == True) | 
                        (df["symptoms"].astype(str).str.contains("Chest Pain|Dizziness", na=False))
                    ]
                    
                    if not urgent_cases.empty:
                        st.error(f"⚠️ {len(urgent_cases)} CRITICAL PATIENTS REQUIRE REVIEW")
                        st.dataframe(urgent_cases[["patient_username", "timestamp", "symptoms", "bp_systolic", "is_urgent"]])
                    else:
                        st.success("✅ No Critical Alerts Pending")

                    st.divider()

                    # 2. PATIENT INSPECTOR (By Username)
                    c1, c2 = st.columns([1, 3])
                    
                    with c1:
                        st.markdown("### 👤 Select Patient")
                        # Get unique patient Usernames
                        patient_users = sorted(df["patient_username"].astype(str).unique())
                        selected_user = st.selectbox("Choose User to Inspect", patient_users)
                    
                    with c2:
                        st.markdown(f"### Patient: **{selected_user}** Overview")
                        
                        # Filter data for this specific patient
                        p_df = df[df["patient_username"] == selected_user].copy()
                        p_df["timestamp"] = pd.to_datetime(p_df["timestamp"])
                        p_df = p_df.sort_values("timestamp", ascending=False)
                        
                        # Stats
                        total_cals = p_df["calories_burned"].sum()
                        unique_days = len(p_df["timestamp"].dt.date.unique())
                        avg_borg = p_df["borg_rating_before"].mean() if "borg_rating_before" in p_df else 0
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("🔥 Active Streak", f"{unique_days} Days")
                        m2.metric("⚡ Total Burn", f"{int(total_cals)} kcal")
                        m3.metric("📉 Avg Fatigue", f"{avg_borg:.1f}/20")
                        
                        st.markdown("#### 📅 Activity History")
                        
                        def highlight_risk(row):
                            if row.get("is_urgent"): return ['background-color: #ffcccc'] * len(row)
                            return [''] * len(row)

                        display_cols = ["id", "timestamp", "predicted_intensity", "borg_rating", "mood", "symptoms", "calories_burned"]
                        final_cols = [c for c in display_cols if c in p_df.columns]
                        
                        st.dataframe(p_df[final_cols].style.apply(highlight_risk, axis=1), use_container_width=True)

                        st.divider()

                        # 3. CLINICAL ACTIONS
                        act_tab1, act_tab2 = st.tabs(["📝 Add Clinical Remark", "⚡ Override Intensity"])
                        
                        # ACTION 1: ADD REMARK
                        with act_tab1:
                            st.write("Select a specific record to attach a note.")
                            target_record = st.selectbox("Select Record ID", p_df["id"].tolist(), key="remark_rec")
                            remark_text = st.text_area("Clinical Note / Recommendation")
                            
                            if st.button("Save Remark"):
                                try:
                                    r_res = requests.post(
                                        f"{API_URL}/doctor/remark/{target_record}",
                                        params={"text": remark_text, "user_id": user["id"]}
                                    )
                                    if r_res.status_code == 200:
                                        st.success("Note saved to patient record!")
                                    else:
                                        st.error("Failed to save note.")
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        # ACTION 2: OVERRIDE INTENSITY
                        with act_tab2:
                            st.warning("Overriding the AI prescription will automatically adjust Heart Rate Zones.")
                            
                            ov_rec_id = st.selectbox("Select Record ID", p_df["id"].tolist(), key="ov_rec")
                            if not p_df.empty:
                                current_int = p_df[p_df["id"] == ov_rec_id]["predicted_intensity"].values[0]
                                st.info(f"Current Intensity: **{current_int}**")
                            
                            new_int = st.selectbox("Set New Intensity", ["Low", "Moderate", "High"])
                            
                            if st.button("Update Prescription"):
                                try:
                                    ov_res = requests.patch(
                                        f"{API_URL}/doctor/override/{ov_rec_id}",
                                        params={"new_intensity": new_int}
                                    )
                                    if ov_res.status_code == 200:
                                        st.success(f"Prescription updated to {new_int}")
                                        st.rerun()
                                    else:
                                        st.error("Update failed.")
                                except Exception as e:
                                    st.error(f"Error: {e}")

            else:
                st.error("Could not connect to database.")
        except Exception as e:
            st.error(f"Connection Error: {e}")