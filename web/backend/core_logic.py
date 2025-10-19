import joblib
import pandas as pd
import os

# Đường dẫn tuyệt đối đến model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "xgb_student_model.joblib")

def load_model():
    return joblib.load(MODEL_PATH)

model = load_model()

def predict(input_data: dict):
    df = pd.DataFrame([input_data])
    prediction = model.predict(df)[0]
    return round(float(prediction), 2)

def feedback(score, habit):
    if score < 60:
        return f"Hiệu suất thấp. Hãy tập trung cải thiện {habit.lower()} mỗi ngày!"
    elif score < 85:
        return f"Khá tốt! Duy trì thói quen {habit.lower()} thường xuyên hơn nhé!"
    else:
        return f"Tuyệt vời! Bạn đang tiến gần mục tiêu {habit.lower()}!"
