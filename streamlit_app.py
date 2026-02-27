import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- CONFIG ---
API_URL = "http://127.0.0.1:8000/api/v1"
st.set_page_config(page_title="HR Rehab Portal", page_icon="❤️", layout="wide")

if "user" not in st.session_state: st.session_state["user"] = None
if "plan_data" not in st.session_state: st.session_state["plan_data"] = None

# --- BORG SCALE DESCRIPTIONS ---
BORG_DESC = {
    6: "No exertion at all",
    7: "Extremely light",
    8: "Extremely light",
    9: "Very light",
    10: "Very light",
    11: "Light",
    12: "Light",
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
    user_data = None
    try:
        res = requests.get(f"{API_URL}/patient/login/{username}")
        if res.status_code == 200:
            user_data = res.json()
        else:
            st.error("User not found.")
    except Exception as e:
        st.error(f"Server Connection Error: {e}")

    if user_data:
        st.session_state["user"] = user_data
        st.rerun()

def logout():
    st.session_state["user"] = None
    st.session_state["plan_data"] = None
    st.session_state["final_plan"] = None
    st.rerun()

# ==========================================
# SCREEN 1: LOGIN & REGISTER
# ==========================================
if not st.session_state["user"]:
    c1, c2 = st.columns([1,2])
    with c1: st.image("https://cdn-icons-png.flaticon.com/512/2966/2966327.png", width=120)
    with c2:
        st.title("HR Rehab Portal")
        auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Register"])
        
        with auth_tab1:
            with st.form("login_form"):
                user_input = st.text_input("Username", key="login_u")
                if st.form_submit_button("Login"):
                    if user_input:
                        login(user_input)
                    else:
                        st.warning("Please enter a username.")

        with auth_tab2:
            new_u = st.text_input("Username", key="reg_u")
            new_n = st.text_input("Full Name", key="reg_n")
            new_role = st.selectbox("Role", ["patient", "doctor"])
            
            c_a, c_b = st.columns(2)
            reg_age = c_a.number_input("Age", min_value=18, max_value=100, value=30)
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
# SCREEN 2: MAIN APP
# ==========================================
else:
    user = st.session_state["user"]
    
    with st.sidebar:
        st.header(f"👤 {user['full_name']}")
        st.caption(f"Role: {user['role'].upper()}")
        
        if user["role"] == "patient":
            st.divider()
            st.subheader("Edit Profile")
            with st.form("sidebar_profile"):
                p_age = st.number_input("Age", min_value=18, max_value=100, value=user.get('age', 30))
                p_sex = st.selectbox("Gender", ["M", "F"], index=0 if user.get('gender')=='M' else 1)
                
                if st.form_submit_button("Update Profile"):
                    res = requests.patch(f"{API_URL}/patient/profile/{user['id']}", json={"age": p_age, "gender": p_sex})
                    if res.status_code == 200:
                        st.session_state["user"]["age"] = p_age
                        st.session_state["user"]["gender"] = p_sex
                        st.success("Updated!")
                        st.rerun()
        
        st.divider()
        if st.button("Logout"): logout()

    # ----------------------------------------------------
    # PATIENT VIEW
    # ----------------------------------------------------
    if user["role"] == "patient":
        col_t, col_r = st.columns([6,1])
        with col_t: st.title("My Health Dashboard")
        with col_r: 
            if st.button("🔄 Refresh"): st.rerun()

        try:
            h_res = requests.get(f"{API_URL}/patient/history/{user['id']}")
            hist_df = pd.DataFrame()
            if h_res.status_code == 200:
                h_data = h_res.json()
                if h_data:
                    hist_df = pd.DataFrame(h_data)
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
        
        tab_predict, tab_hist, tab_monitor = st.tabs(["💪 New Session", "📊 History & Remarks", "📈 Continuous Monitoring"])
        
        with tab_predict:
            st.subheader("Pre-Workout Vitals")
            
            c1, c2, c3 = st.columns(3)
            weight = c1.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=75.0)
            rhr = c2.number_input("Resting HR", min_value=30, max_value=220, value=65)
            pulse = c3.number_input("Pulse Rate (Current)", min_value=30, max_value=220, value=70)

            c4, c5, c6 = st.columns(3)
            sys = c4.number_input("Systolic BP", min_value=70, max_value=250, value=120)
            dia = c5.number_input("Diastolic BP", min_value=40, max_value=150, value=80)
            resp = c6.number_input("Resp. Rate", min_value=5, max_value=60, value=16)

            st.markdown("**Pre-existing Conditions:**")
            cc1, cc2 = st.columns(2)
            has_htn = cc1.checkbox("Hypertension (HTN)")
            has_dm = cc2.checkbox("Diabetes (DM)")
            
            st.divider()
            st.markdown("**How do you feel right now? (Borg Scale)**")
            
            borg_val = st.slider("Fatigue Level", min_value=6, max_value=20, value=6)
            st.info(f"**Level {borg_val}:** {BORG_DESC[borg_val]}")
            
            if st.button("Start Session", type="primary"):
                payload = {
                    "weight": weight, "resting_hr": rhr, 
                    "bp_systolic": sys, "bp_diastolic": dia,
                    "pulse_rate_before": pulse, "respiratory_rate_before": resp,
                    "borg_rating_before": borg_val,
                    "has_htn": has_htn, "has_dm": has_dm
                }
                res = requests.post(f"{API_URL}/patient/predict/{user['id']}", json=payload)
                if res.status_code == 200: 
                    st.session_state["plan_data"] = res.json()
                    st.session_state["final_plan"] = None
                else: 
                    st.error(res.text)

            if st.session_state["plan_data"]:
                data = st.session_state["plan_data"]
                st.divider()
                
                if "final_plan" not in st.session_state:
                    st.session_state["final_plan"] = None
                
                if data["is_urgent"]:
                    st.error("⚠️ CRITICAL EXERTION DETECTED: Vitals or Fatigue are dangerously high. Please do NOT exercise.")
                    st.warning("Follow this guided meditation to lower your heart rate safely.")
                    if data.get("youtube_links"):
                        st.video(data["youtube_links"][0])
                    if st.button("Close Session"):
                        st.session_state["plan_data"] = None
                        st.rerun()

                elif not st.session_state["final_plan"]:
                    st.info("🏃‍♂️ **Warmup Phase:** Cleared! Please complete a **Moderate** intensity warmup using one of the routines below.")
                    
                    if len(data.get("youtube_links", [])) >= 2:
                        vid_col1, vid_col2 = st.columns(2)
                        with vid_col1: st.video(data["youtube_links"][0])
                        with vid_col2: st.video(data["youtube_links"][1])
                    
                    st.divider()
                    st.subheader("Post-Warmup Vitals (Required for AI Prediction)")
                    
                    c_a, c_b = st.columns(2)
                    fb_pulse = c_a.number_input("HR Post (After Moderate Exercise)", min_value=30, max_value=220, value=110)
                    fb_borg = c_b.slider("Exertion Level (After Warmup)", min_value=6, max_value=20, value=13)
                    st.info(f"**Level {fb_borg}:** {BORG_DESC[fb_borg]}")
                    
                    fb_mood = st.select_slider("Mood", ["Happy", "Neutral", "Sad", "Tired", "Energetic"], value="Neutral")
                    
                    if st.button("Get AI Prescription for Next Exercises", type="primary"):
                        payload = {"borg_rating": fb_borg, "pulse_rate_after": fb_pulse, "mood": fb_mood, "symptoms": []}
                        res = requests.patch(f"{API_URL}/patient/feedback/{data['id']}", json=payload)
                        if res.status_code == 200:
                            st.session_state["final_plan"] = res.json()
                            st.rerun()
                        else:
                            st.error("Failed to generate AI prescription.")
                
                else:
                    final_data = st.session_state["final_plan"]
                    
                    if final_data.get("is_urgent"):
                        st.error("⚠️ CRITICAL EXERTION DETECTED POST-WARMUP: Your heart rate or fatigue escalated too fast.")
                        st.warning("Please stop exercising immediately and follow this meditation.")
                        if final_data.get("youtube_links"):
                            st.video(final_data["youtube_links"][0])
                    else:
                        st.success(f"✅ **AI Target for Next Exercises:** {final_data['predicted_intensity']} Intensity")
                        st.markdown("Choose a routine below to continue:")
                        
                        links = final_data.get("youtube_links", [])
                        if len(links) >= 3:
                            v1, v2, v3 = st.columns(3)
                            with v1: st.video(links[0])
                            with v2: st.video(links[1])
                            with v3: st.video(links[2])
                    
                    st.divider()
                    if st.button("Finish & Save Session"):
                        st.session_state["plan_data"] = None
                        st.session_state["final_plan"] = None
                        st.success("Session Completed!")
                        st.rerun()

        with tab_hist:
            if not hist_df.empty:
                if "doctor_note" not in hist_df.columns: hist_df["doctor_note"] = "No remarks"
                if "mood" not in hist_df.columns: hist_df["mood"] = "Neutral"
                
                view_df = hist_df.copy()
                view_df["timestamp"] = pd.to_datetime(view_df["timestamp"])
                view_df = view_df.sort_values("timestamp")

                view_df = view_df.rename(columns={
                    "borg_rating_before": "Fatigue (Pre)",
                    "borg_rating_after": "Exertion (Post)",
                    "pulse_rate_before": "HR (Pre)",
                    "pulse_rate_after": "HR (Post)",
                    "bp_systolic": "Sys BP",
                    "bp_diastolic": "Dia BP"
                })
                
                st.subheader("📈 Vitals Trend Analysis")
                c_g1, c_g2 = st.columns(2)
                
                hr_cols = ["HR (Pre)"]
                if "HR (Post)" in view_df.columns: hr_cols.append("HR (Post)")
                if set(hr_cols).issubset(view_df.columns):
                    fig_hr = px.line(view_df, x="timestamp", y=hr_cols, labels={"value": "BPM", "variable": "Phase", "timestamp": "Date"}, title="Heart Rate Trend", markers=True)
                    c_g1.plotly_chart(fig_hr, use_container_width=True)
                
                bp_cols = ["Sys BP", "Dia BP"]
                if set(bp_cols).issubset(view_df.columns):
                    fig_bp = px.line(view_df, x="timestamp", y=bp_cols, labels={"value": "mmHg", "variable": "Metric", "timestamp": "Date"}, title="Blood Pressure Trend", markers=True)
                    c_g2.plotly_chart(fig_bp, use_container_width=True)

                st.divider()
                st.markdown("### Activity Log")
                
                view_df["timestamp"] = view_df["timestamp"].dt.strftime('%Y-%m-%d %I:%M %p')
                
                cols_to_show = ["timestamp", "predicted_intensity", "Fatigue (Pre)", "HR (Pre)", "Sys BP", "Dia BP", "mood", "doctor_note"]
                if "Exertion (Post)" in view_df.columns: cols_to_show.insert(3, "Exertion (Post)")
                if "HR (Post)" in view_df.columns: cols_to_show.insert(6, "HR (Post)")
                
                final_cols = [c for c in cols_to_show if c in view_df.columns]
                st.dataframe(view_df[final_cols].sort_index(ascending=False), use_container_width=True)
            else:
                st.info("No records found.")
                
        with tab_monitor:
            st.subheader("Live Vitals Tracking")
            st_autorefresh(interval=300000, key="fitness_refresh")
            
            try:
                fit_res = requests.get(f"{API_URL}/fitness/history/{user['id']}?limit=60")
                if fit_res.status_code == 200:
                    fit_data = fit_res.json()
                    if fit_data:
                        f_df = pd.DataFrame(fit_data)
                        f_df['timestamp'] = pd.to_datetime(f_df['timestamp'])
                        f_df = f_df.sort_values('timestamp')

                        if 'heart_rate' in f_df.columns and not f_df['heart_rate'].dropna().empty:
                            fig_hr = px.line(f_df, x="timestamp", y="heart_rate", title="Heart Rate History", markers=True)
                            st.plotly_chart(fig_hr, use_container_width=True)
                        else:
                            st.info("No heart rate data available.")

                        if 'steps' in f_df.columns and not f_df['steps'].dropna().empty:
                            fig_steps = px.bar(f_df, x="timestamp", y="steps", title="Step Count Over Time")
                            st.plotly_chart(fig_steps, use_container_width=True)
                        else:
                            st.info("No step data available.")
                    else:
                        st.info("No fitness records found. Ensure the mobile client is syncing.")
            except Exception as e:
                st.error(f"Could not load continuous monitoring data: {e}")

    # ----------------------------------------------------
    # DOCTOR VIEW
    # ----------------------------------------------------
    elif user["role"] == "doctor":
        col_t, col_r = st.columns([6,1])
        with col_t: st.title("👨‍⚕️ Clinical Command Center")
        with col_r: 
            if st.button("🔄 Refresh", key="doc_refresh"): st.rerun()
        
        try:
            res = requests.get(f"{API_URL}/doctor/dashboard")
            if res.status_code == 200:
                all_records = res.json()
                if not all_records:
                    st.info("No records found.")
                else:
                    df = pd.DataFrame(all_records)
                    for c in ["symptoms", "calories_burned", "is_urgent", "patient_username", "borg_rating_after", "borg_rating_before", "mood", "pulse_rate_before", "pulse_rate_after", "bp_systolic", "bp_diastolic"]:
                        if c not in df.columns: df[c] = None

                    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime('%Y-%m-%d %I:%M %p')
                    
                    urgent_cases = df[df["is_urgent"] == True]
                    
                    if not urgent_cases.empty:
                        st.error(f"⚠️ {len(urgent_cases)} CRITICAL PATIENTS REQUIRE REVIEW")
                        st.dataframe(urgent_cases[["id", "patient_username", "timestamp", "symptoms", "bp_systolic"]])
                    else:
                        st.success("✅ No Critical Alerts Pending")

                    st.divider()

                    c1, c2 = st.columns([1, 3])
                    with c1:
                        st.markdown("### 👤 Select Patient")
                        p_users = sorted(df["patient_username"].astype(str).unique())
                        selected_user = st.selectbox("Username", p_users)
                    
                    with c2:
                        st.markdown(f"### Patient: **{selected_user}** Overview")
                        p_df = df[df["patient_username"] == selected_user].copy()
                        p_df = p_df.sort_values("timestamp", ascending=False)
                        
                        stk = len(pd.to_datetime(p_df["timestamp"]).dt.date.unique())
                        cal = int(p_df["calories_burned"].sum())
                        
                        m1, m2 = st.columns(2)
                        m1.metric("Streak", f"{stk} Days")
                        m2.metric("Total Burn", f"{cal} kcal")
                        
                        st.subheader("Detailed History")
                        
                        p_df = p_df.rename(columns={
                            "borg_rating_before": "Fatigue (Pre)",
                            "borg_rating_after": "Exertion (Post)",
                            "pulse_rate_before": "HR (Pre)",
                            "pulse_rate_after": "HR (Post)",
                            "bp_systolic": "Sys BP",
                            "bp_diastolic": "Dia BP"
                        })

                        def highlight_risk(row):
                            return ['background-color: #ffcccc']*len(row) if row.get("is_urgent") else ['']*len(row)

                        view_cols = ["id", "timestamp", "predicted_intensity", "Fatigue (Pre)", "Exertion (Post)", "HR (Pre)", "HR (Post)", "Sys BP", "Dia BP", "mood", "symptoms"]
                        final_view = [c for c in view_cols if c in p_df.columns]
                        
                        st.dataframe(p_df[final_view].style.apply(highlight_risk, axis=1), use_container_width=True)

                        st.divider()

                        act1, act2 = st.tabs(["Add Remark", "Override Plan"])
                        with act1:
                            rec_id = st.selectbox("Record ID", p_df["id"].tolist(), key="rem_id")
                            note = st.text_area("Doctor's Note")
                            if st.button("Save Note"):
                                requests.post(f"{API_URL}/doctor/remark/{rec_id}", params={"text": note, "user_id": user["id"]})
                                st.success("Saved!")
                        
                        with act2:
                            ov_id = st.selectbox("Record ID to Edit", p_df["id"].tolist(), key="ov_id")
                            new_i = st.selectbox("New Intensity", ["Low", "Moderate", "High"])
                            if st.button("Update"):
                                requests.patch(f"{API_URL}/doctor/override/{ov_id}", params={"new_intensity": new_i})
                                st.success("Updated!")
                                st.rerun()

            else:
                st.error("Database Error")
        except Exception as e:
            st.error(f"Connection Error: {e}")