import joblib
import pandas as pd
import numpy as np
from pathlib import Path

# --- FIX STARTS HERE ---
# 1. Get the directory where THIS file (ml_service.py) lives: .../backend/app/services
BASE_DIR = Path(__file__).resolve().parent

# 2. Go up one level to 'app', then down into 'ml_models'
MODEL_DIR = BASE_DIR.parent / "ml_models"

MODEL_PATH = MODEL_DIR / "xgb_pipeline.pkl"
ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"

class MLService:
    def __init__(self):
        try:
            self.pipeline = joblib.load(MODEL_PATH)
            self.encoder = joblib.load(ENCODER_PATH)
            print("✅ ML Models loaded successfully.")
        except Exception as e:
            print(f"⚠️  ML Load Error: {e}")
            self.pipeline = None

    def predict_and_audit(self, age: int, weight: float, rhr: int, bp_sys: int, bp_dia: int,borg_before: int):
        
        # 1. Prepare Data
        input_data = pd.DataFrame([{
            'Age': age,
            'Weight (kg)': weight,
            'Resting Heart Rate (BPM)': rhr,
            'BPB_Systolic': bp_sys,
            'BPB_Diastolic': bp_dia,
            # Placeholders for missing columns
            'Gender': 'M', 'Pre-existing Conditions': 'HTN', 
            'Borg Scale Rating (Before)': borg_before, # <--- USE REAL INPUT HERE
            'Pulse Rate Before': rhr, 
            'Respiratory Rate Before': 16
        }])

        # 2. Get ML Prediction
        prediction = "Moderate" # Default
        if self.pipeline:
            try:
                pred_encoded = self.pipeline.predict(input_data)
                prediction = self.encoder.inverse_transform(pred_encoded)[0]
            except Exception as e:
                print(f"Prediction Error: {e}")

        # 3. SAFETY LAYER (UPDATED: Checks vitals INDEPENDENTLY)
        mhr = 220 - age
        target_min = int(0.50 * mhr)
        target_max = int(0.85 * mhr)
        is_urgent = False

        # RULE A: Absolute Contraindications (Too dangerous to exercise)
        if rhr > 100 or bp_sys > 160 or bp_dia > 100:
            is_urgent = True
            prediction = "Low" # Force downgrade

        # RULE B: High Intensity Safety Check
        if prediction == "High":
            if age > 65 or rhr > 90:
                prediction = "Moderate" # Downgrade for safety (but not urgent)

        # 4. Real YouTube Links
        youtube_map = {
            "Low": "https://www.youtube.com/watch?v=ipNvN-GHhe0",      # Joe Wicks 15 Min Low Impact
            "Moderate": "https://www.youtube.com/watch?v=rZDzP11ePt8", # FitByMik 20 Min Cardio
            "High": "https://www.youtube.com/watch?v=hLVh5IBsCxk"      # GrowingAnnanas HIIT
        }

        return {
            "predicted_intensity": prediction,
            "mhr": mhr,
            "target_hr_min": target_min,
            "target_hr_max": target_max,
            "is_urgent": is_urgent,
            "youtube_link": youtube_map.get(prediction, "")
        }

ml_service = MLService()