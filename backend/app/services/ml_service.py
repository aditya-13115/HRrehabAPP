import joblib
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR.parent / "ml_models"
MODEL_PATH = MODEL_DIR / "best_model.pkl"

class MLService:
    def __init__(self):
        try:
            self.pipeline = joblib.load(MODEL_PATH)
            print("ML Model loaded successfully.")
        except Exception as e:
            print(f"ML Load Error: {e}")
            self.pipeline = None

    def evaluate_post_workout(self, borg_after, borg_change, hr_percent_mhr, pulse_change, borg_before, age, resp_before):
        input_data = pd.DataFrame([{
            'Borg Scale Rating (After)': borg_after,
            'Borg_Change': borg_change,
            'HR_Percent_MHR': hr_percent_mhr,
            'Pulse_Change': pulse_change,
            'Borg Scale Rating (Before)': borg_before,
            'Age': age,
            'Respiratory Rate Before': resp_before
        }])

        prediction_str = "Moderate" 
        
        if self.pipeline:
            try:
                pred_encoded = self.pipeline.predict(input_data)[0]
                mapping = {0: "Low", 1: "Moderate", 2: "High"}
                prediction_str = mapping.get(int(pred_encoded), "Moderate")
            except Exception as e:
                print(f"Prediction Error: {e}")

        youtube_map = {
            "Low": [
                "https://www.youtube.com/watch?v=O1XJ8tE2HqA",
                "https://www.youtube.com/watch?v=5if4cjO5nxo",
                "https://www.youtube.com/watch?v=gC_L9qAHVJ8"
            ],      
            "Moderate": [
                "https://www.youtube.com/watch?v=rZDzP11ePt8",
                "https://www.youtube.com/watch?v=UBMk30rjy0o",
                "https://www.youtube.com/watch?v=CBWQGb4LyAM"
            ], 
            "High": [
                "https://www.youtube.com/watch?v=hLVh5IBsCxk",
                "https://www.youtube.com/watch?v=ml6cT4AZdqI",
                "https://www.youtube.com/watch?v=M0uO8X3_tEA"
            ]      
        }

        return {
            "predicted_intensity": prediction_str,
            "youtube_links": youtube_map.get(prediction_str, [])
        }

ml_service = MLService()