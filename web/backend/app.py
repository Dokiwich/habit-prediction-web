from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import xgboost as xgb
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
CORS(app, supports_credentials=True)

# Load model và scaler
try:
    model = xgb.XGBRegressor()
    model.load_model('model/habit_prediction_model.json')
    with open('model/xgb_student_model.joblib', 'rb') as f:
        scaler = pickle.load(f)
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    model = None
    scaler = None

# In-memory storage (no login required)
habits_db = []
completions_db = []
predictions_db = []

# Feature names
FEATURE_NAMES = [
    'age', 'gender_encoded', 'year', 'gpa',
    'motivation_level', 'self_discipline', 'stress_level', 
    'time_management_skill', 'goal_clarity',
    'family_support', 'family_income_encoded', 'living_situation_encoded',
    'siblings_count', 'study_environment_quality', 
    'distance_to_school_km', 'commute_time_minutes', 
    'has_study_room', 'friend_support', 'mentor_availability',
    'week', 'week_squared', 'is_early_semester', 'is_mid_semester', 'is_late_semester',
    'study_hours_per_week', 'exercise_sessions_per_week', 
    'sleep_hours_per_day', 'social_activities_per_week',
    'meditation_frequency', 'reading_frequency', 'exercise_frequency',
    'meal_planning_frequency', 'journaling_frequency',
    'weekly_motivation', 'weekly_stress', 'weekly_energy_level',
    'study_distractions', 'weather_quality', 'noise_level',
    'has_exam', 'has_deadline', 'has_family_event',
    'total_habit_frequency', 'avg_habit_frequency',
    'motivation_x_discipline', 'stress_x_distractions', 'support_score',
    'prev_week_performance', 'rolling_avg_performance'
]

# ==================== HABIT ROUTES ====================

@app.route('/api/habits', methods=['GET'])
def get_habits():
    """Lấy danh sách thói quen"""
    return jsonify({
        'success': True,
        'habits': habits_db
    }), 200

@app.route('/api/habits', methods=['POST'])
def add_habit():
    """Thêm thói quen mới"""
    try:
        data = request.get_json()
        
        habit = {
            'id': len(habits_db) + 1,
            'name': data.get('name'),
            'icon': data.get('icon', '🎯'),
            'streak': 0,
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        
        habits_db.append(habit)
        
        return jsonify({
            'success': True,
            'habit': habit
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/habits/<int:habit_id>', methods=['DELETE'])
def delete_habit(habit_id):
    """Xóa thói quen"""
    global habits_db
    habits_db = [h for h in habits_db if h['id'] != habit_id]
    return jsonify({'success': True}), 200

# ==================== COMPLETION ROUTES ====================

@app.route('/api/completions', methods=['POST'])
def mark_completion():
    """Đánh dấu hoàn thành thói quen"""
    try:
        data = request.get_json()
        
        completion = {
            'habit_id': data.get('habit_id'),
            'date': data.get('date', datetime.date.today().isoformat()),
            'completed': data.get('completed', True),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
        
        completions_db.append(completion)
        
        # Update streak
        habit = next((h for h in habits_db if h['id'] == completion['habit_id']), None)
        if habit and completion['completed']:
            habit['streak'] = habit.get('streak', 0) + 1
        
        return jsonify({
            'success': True,
            'completion': completion
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/completions/today', methods=['GET'])
def get_today_completions():
    """Lấy danh sách hoàn thành hôm nay"""
    today = datetime.date.today().isoformat()
    today_completions = [c for c in completions_db if c['date'] == today]
    
    return jsonify({
        'success': True,
        'completions': today_completions,
        'date': today
    }), 200

@app.route('/api/completions/history', methods=['GET'])
def get_completion_history():
    """Lấy lịch sử 7 ngày"""
    today = datetime.date.today()
    history = []
    
    for i in range(7):
        date = (today - datetime.timedelta(days=6-i)).isoformat()
        day_completions = [c for c in completions_db if c['date'] == date and c['completed']]
        total_habits = len(habits_db)
        percentage = (len(day_completions) / total_habits * 100) if total_habits > 0 else 0
        
        history.append({
            'date': date,
            'completed': len(day_completions),
            'total': total_habits,
            'percentage': round(percentage, 0)
        })
    
    return jsonify({
        'success': True,
        'history': history
    }), 200

# ==================== STATISTICS ROUTES ====================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Thống kê tổng quan"""
    try:
        total_habits = len(habits_db)
        
        # Calculate current streak
        current_streak = 0
        today = datetime.date.today()
        check_date = today
        
        while True:
            date_str = check_date.isoformat()
            day_completions = [c for c in completions_db 
                             if c['date'] == date_str and c['completed']]
            
            if len(day_completions) == total_habits and total_habits > 0:
                current_streak += 1
                check_date -= datetime.timedelta(days=1)
            else:
                break
        
        # Calculate completion rate (last 30 days)
        last_30_days = []
        for i in range(30):
            date = (today - datetime.timedelta(days=i)).isoformat()
            day_completions = [c for c in completions_db if c['date'] == date]
            last_30_days.extend(day_completions)
        
        total_possible = total_habits * 30
        completion_rate = (len([c for c in last_30_days if c['completed']]) / total_possible * 100) if total_possible > 0 else 0
        
        # Find longest streak
        longest_streak = 0
        temp_streak = 0
        check_date = today
        
        for i in range(365):  # Check last year
            date_str = check_date.isoformat()
            day_completions = [c for c in completions_db 
                             if c['date'] == date_str and c['completed']]
            
            if len(day_completions) == total_habits and total_habits > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
            
            check_date -= datetime.timedelta(days=1)
        
        stats = {
            'total_habits': total_habits,
            'current_streak': current_streak,
            'completion_rate': round(completion_rate, 0),
            'longest_streak': longest_streak
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== LEADERBOARD ROUTES ====================

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Bảng xếp hạng (mock data)"""
    leaderboard = [
        {
            'rank': 1,
            'name': 'Trịnh Đình Thắng',
            'avatar': 'TĐ',
            'streak': 15,
            'score': 1250
        },
        {
            'rank': 2,
            'name': 'Nguyễn Văn A',
            'avatar': 'NV',
            'streak': 12,
            'score': 980
        },
        {
            'rank': 3,
            'name': 'Lê Thị B',
            'avatar': 'LT',
            'streak': 10,
            'score': 850
        },
        {
            'rank': 4,
            'name': 'Phạm Thị C',
            'avatar': 'PT',
            'streak': 8,
            'score': 720
        }
    ]
    
    return jsonify({
        'success': True,
        'leaderboard': leaderboard
    }), 200

# ==================== PREDICTION ROUTES ====================

@app.route('/api/predict', methods=['POST'])
def predict():
    """Dự đoán hiệu suất thói quen"""
    try:
        if model is None or scaler is None:
            return jsonify({
                'success': False,
                'message': 'Model not loaded!'
            }), 500
        
        data = request.get_json()
        
        # Prepare features
        features = prepare_features(data)
        
        # Scale features
        features_scaled = scaler.transform([features])
        
        # Predict
        prediction = float(model.predict(features_scaled)[0])
        
        # Save prediction
        prediction_record = {
            'habit_id': data.get('habit_id'),
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'prediction': prediction
        }
        predictions_db.append(prediction_record)
        
        # Categorize result
        if prediction >= 80:
            category = 'Excellent'
            recommendation = 'Bạn đang có thói quen rất tốt! Hãy duy trì.'
        elif prediction >= 60:
            category = 'Good'
            recommendation = 'Thói quen khá ổn, cố gắng cải thiện thêm.'
        elif prediction >= 40:
            category = 'Average'
            recommendation = 'Cần tăng cường kỷ luật và quản lý thời gian.'
        else:
            category = 'Need Improvement'
            recommendation = 'Cần thay đổi đáng kể. Tập trung vào động lực và môi trường.'
        
        return jsonify({
            'success': True,
            'prediction': {
                'score': round(prediction, 0),
                'category': category,
                'recommendation': recommendation
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def prepare_features(data):
    """Chuẩn bị features từ input data"""
    total_habit_freq = sum([
        data.get('meditation_frequency', 0),
        data.get('reading_frequency', 0),
        data.get('exercise_frequency', 0),
        data.get('meal_planning_frequency', 0),
        data.get('journaling_frequency', 0)
    ])
    
    week = data.get('week', 1)
    
    features = {
        'age': data.get('age', 20),
        'gender_encoded': 1 if data.get('gender') == 'Male' else 0,
        'year': data.get('year', 1),
        'gpa': data.get('gpa', 3.0),
        'motivation_level': data.get('motivation_level', 5),
        'self_discipline': data.get('self_discipline', 5),
        'stress_level': data.get('stress_level', 5),
        'time_management_skill': data.get('time_management_skill', 5),
        'goal_clarity': data.get('goal_clarity', 5),
        'family_support': data.get('family_support', 5),
        'family_income_encoded': data.get('family_income_encoded', 1),
        'living_situation_encoded': data.get('living_situation_encoded', 0),
        'siblings_count': data.get('siblings_count', 1),
        'study_environment_quality': data.get('study_environment_quality', 5),
        'distance_to_school_km': data.get('distance_to_school_km', 10),
        'commute_time_minutes': data.get('commute_time_minutes', 30),
        'has_study_room': data.get('has_study_room', 0),
        'friend_support': data.get('friend_support', 5),
        'mentor_availability': data.get('mentor_availability', 0),
        'week': week,
        'week_squared': week ** 2,
        'is_early_semester': 1 if week <= 4 else 0,
        'is_mid_semester': 1 if 4 < week <= 8 else 0,
        'is_late_semester': 1 if week > 8 else 0,
        'study_hours_per_week': data.get('study_hours_per_week', 20),
        'exercise_sessions_per_week': data.get('exercise_sessions_per_week', 3),
        'sleep_hours_per_day': data.get('sleep_hours_per_day', 7),
        'social_activities_per_week': data.get('social_activities_per_week', 3),
        'meditation_frequency': data.get('meditation_frequency', 0),
        'reading_frequency': data.get('reading_frequency', 0),
        'exercise_frequency': data.get('exercise_frequency', 0),
        'meal_planning_frequency': data.get('meal_planning_frequency', 0),
        'journaling_frequency': data.get('journaling_frequency', 0),
        'weekly_motivation': data.get('weekly_motivation', 5),
        'weekly_stress': data.get('weekly_stress', 5),
        'weekly_energy_level': data.get('weekly_energy_level', 5),
        'study_distractions': data.get('study_distractions', 5),
        'weather_quality': data.get('weather_quality', 5),
        'noise_level': data.get('noise_level', 5),
        'has_exam': data.get('has_exam', 0),
        'has_deadline': data.get('has_deadline', 0),
        'has_family_event': data.get('has_family_event', 0),
        'total_habit_frequency': total_habit_freq,
        'avg_habit_frequency': total_habit_freq / 5,
        'motivation_x_discipline': data.get('motivation_level', 5) * data.get('self_discipline', 5),
        'stress_x_distractions': data.get('weekly_stress', 5) * data.get('study_distractions', 5),
        'support_score': (data.get('family_support', 5) + data.get('friend_support', 5)) / 2,
        'prev_week_performance': data.get('prev_week_performance', 50),
        'rolling_avg_performance': data.get('rolling_avg_performance', 50)
    }
    
    return [features[name] for name in FEATURE_NAMES]

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Kiểm tra health của API"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'model_loaded': model is not None,
        'habits_count': len(habits_db),
        'timestamp': datetime.datetime.utcnow().isoformat()
    }), 200

# ==================== RUN SERVER ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting Habit Tracker API Server")
    print("="*60)
    print(f"✓ Model loaded: {model is not None}")
    print(f"✓ Scaler loaded: {scaler is not None}")
    print("="*60)
    print("📍 Server running on: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)