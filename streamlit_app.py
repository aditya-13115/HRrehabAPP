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
    # 1. Try to get data
    try:
        res = requests.get(f"{API_URL}/patient/login/{username}")
        if res.status_code == 200:
            user_data = res.json()
        else:
            st.error("User not found.")
    except Exception as e:
        st.error(f"Server Connection Error: {e}")

    # 2. If successful, save and rerun (OUTSIDE the try/except)
    if user_data:
        st.session_state["user"] = user_data
        st.rerun()

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
            with st.form("login_form"):
                user_input = st.text_input("Username", key="login_u")
                # Using a form submit button prevents "double click" issues
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
    
    # --- SIDEBAR (Profile & Logout) ---
    with st.sidebar:
        st.header(f"👤 {user['full_name']}")
        st.caption(f"Role: {user['role'].upper()}")
        
        # MOVED PROFILE HERE
        if user["role"] == "patient":
            st.divider()
            st.subheader("Edit Profile")
            with st.form("sidebar_profile"):
                p_age = st.number_input("Age", 18, 100, user.get('age', 30))
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
    # 🏃 PATIENT VIEW
    # ----------------------------------------------------
    if user["role"] == "patient":
        # REFRESH BUTTON HEADER
        col_t, col_r = st.columns([6,1])
        with col_t: st.title("My Health Dashboard")
        with col_r: 
            if st.button("🔄 Refresh"): st.rerun()

        # --- GLOBAL STATS ---
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
        
        # --- TABS (Removed Profile from here) ---
        tab_predict, tab_hist = st.tabs(["💪 New Session", "📊 History & Remarks"])
        
        # --- TAB 1: PREDICTION (Live Borg) ---
        with tab_predict:
            st.subheader("Pre-Workout Vitals")
            
            # NO FORM HERE -> Allows Live Slider Updates
            c1, c2, c3 = st.columns(3)
            # Widened Ranges: Weight 20-300, HR 30-220
            weight = c1.number_input("Weight (kg)", 20.0, 300.0, 75.0)
            rhr = c2.number_input("Resting HR", 30, 200, 65)
            pulse = c3.number_input("Pulse Rate (Current)", 30, 220, 70)

            c4, c5, c6 = st.columns(3)
            # Widened Ranges: BP 50-300 (Sys) / 30-180 (Dia)
            sys = c4.number_input("Systolic BP", 50, 300, 120)
            dia = c5.number_input("Diastolic BP", 30, 180, 80)
            # Widened Range: Resp 5-60
            resp = c6.number_input("Resp. Rate", 5, 60, 16)

            st.markdown("**Pre-existing Conditions:**")
            cc1, cc2 = st.columns(2)
            has_htn = cc1.checkbox("Hypertension (HTN)")
            has_dm = cc2.checkbox("Diabetes (DM)")
            
            st.divider()
            st.markdown("**How do you feel right now? (Borg Scale)**")
            
            # Live Slider
            borg_val = st.slider("Fatigue Level", 6, 20, 6)
            st.info(f"**Level {borg_val}:** {BORG_DESC[borg_val]}")
            
            if st.button("Generate Plan", type="primary"):
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

            # SHOW PLAN & VIDEO (Outside Form)
            if st.session_state["plan_data"]:
                data = st.session_state["plan_data"]
                st.divider()
                st.subheader("Your AI Prescription")
                if data["is_urgent"]: st.error("⚠️ HIGH RISK DETECTED - Intensity Reduced")
                else: st.success(f"✅ Target: {data['predicted_intensity']} Intensity")
                
                # RESTORED VIDEO HERE
                st.video(data["youtube_link"])
                
                st.divider()
                st.subheader("Post-Workout Check-in")
                st.caption("Fill this AFTER you finish.")
                
                # --- UPDATED: Live Slider for Post-Workout ---
                fb_borg = st.slider("Exertion Level (After Workout)", 6, 20, 13)
                st.info(f"**Level {fb_borg}:** {BORG_DESC[fb_borg]}")
                
                fb_mood = st.select_slider("Mood", ["Happy", "Sad", "Tired", "Energetic"])
                
                if st.button("Save Log", type="primary"):
                    requests.patch(f"{API_URL}/patient/feedback/{data['id']}", 
                                 json={"borg_rating": fb_borg, "mood": fb_mood, "symptoms": []})
                    st.success("Logged!")
                    st.session_state["plan_data"] = None
                    st.rerun()

        # --- TAB 2: HISTORY ---
        with tab_hist:
            if not hist_df.empty:
                if "doctor_note" not in hist_df.columns: hist_df["doctor_note"] = "No remarks"
                
                st.markdown("### Activity Log")
                # Show Borg Before and After if available
                display_cols = ["timestamp", "predicted_intensity", "borg_rating_before", "doctor_note"]
                
                # Rename for clarity
                view_df = hist_df.copy()
                view_df = view_df.rename(columns={
                    "borg_rating_before": "Fatigue (Pre)",
                    "borg_rating": "Exertion (Post)"
                })
                
                cols_to_show = ["timestamp", "predicted_intensity", "Fatigue (Pre)", "doctor_note"]
                if "Exertion (Post)" in view_df.columns: cols_to_show.append("Exertion (Post)")
                
                final_cols = [c for c in cols_to_show if c in view_df.columns]
                st.dataframe(view_df[final_cols], use_container_width=True)
            else:
                st.info("No records found.")

    # ----------------------------------------------------
    # 👨‍⚕️ DOCTOR VIEW
    # ----------------------------------------------------
    elif user["role"] == "doctor":
        # REFRESH BUTTON HEADER
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
                    # Safe Defaults
                    for c in ["symptoms", "calories_burned", "is_urgent", "patient_username", "borg_rating", "borg_rating_before"]:
                        if c not in df.columns: df[c] = None

                    # 1. ALERT FILTER (Strict Urgency Check)
                    # Only show if is_urgent is TRUE. If Doctor overrode it (False), it disappears.
                    urgent_cases = df[df["is_urgent"] == True]
                    
                    if not urgent_cases.empty:
                        st.error(f"⚠️ {len(urgent_cases)} CRITICAL PATIENTS REQUIRE REVIEW")
                        # --- UPDATED: Added 'id' to the view ---
                        st.dataframe(urgent_cases[["id", "patient_username", "timestamp", "symptoms", "bp_systolic"]])
                    else:
                        st.success("✅ No Critical Alerts Pending")

                    st.divider()

                    # 2. PATIENT INSPECTOR
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        st.markdown("### 👤 Select Patient")
                        p_users = sorted(df["patient_username"].astype(str).unique())
                        selected_user = st.selectbox("Username", p_users)
                    
                    with c2:
                        st.markdown(f"### Patient: **{selected_user}** Overview")
                        p_df = df[df["patient_username"] == selected_user].copy()
                        p_df["timestamp"] = pd.to_datetime(p_df["timestamp"])
                        p_df = p_df.sort_values("timestamp", ascending=False)
                        
                        # Stats
                        stk = len(p_df["timestamp"].dt.date.unique())
                        cal = int(p_df["calories_burned"].sum())
                        
                        m1, m2 = st.columns(2)
                        m1.metric("Streak", f"{stk} Days")
                        m2.metric("Total Burn", f"{cal} kcal")
                        
                        st.subheader("Detailed History")
                        
                        # Rename Borg Columns for Doctor
                        p_df = p_df.rename(columns={
                            "borg_rating_before": "Fatigue (Pre)",
                            "borg_rating": "Exertion (Post)"
                        })

                        def highlight_risk(row):
                            return ['background-color: #ffcccc']*len(row) if row.get("is_urgent") else ['']*len(row)

                        # Added Exertion (Post) to view
                        view_cols = ["id", "timestamp", "predicted_intensity", "Fatigue (Pre)", "Exertion (Post)", "mood", "symptoms"]
                        final_view = [c for c in view_cols if c in p_df.columns]
                        
                        st.dataframe(p_df[final_view].style.apply(highlight_risk, axis=1), use_container_width=True)

                        st.divider()

                        # 3. ACTIONS
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