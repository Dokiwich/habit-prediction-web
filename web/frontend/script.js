// API Configuration
const API_URL = 'http://localhost:5000/api';
let habits = [];
let currentHabitId = null;

// ==================== Initialization ====================

window.onload = function() {
    loadHabits();
    loadCalendar();
    loadStats();
};

// ==================== API Calls ====================

async function loadHabits() {
    try {
        const response = await fetch(`${API_URL}/habits`);
        const data = await response.json();
        
        if (data.success) {
            habits = data.habits;
            renderHabits();
        }
    } catch (error) {
        console.error('Error loading habits:', error);
    }
}

async function loadCalendar() {
    try {
        const response = await fetch(`${API_URL}/completions/history`);
        const data = await response.json();
        
        if (data.success) {
            renderCalendar(data.history);
        }
    } catch (error) {
        console.error('Error loading calendar:', error);
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();
        
        if (data.success) {
            updateStreakDisplay(data.stats.current_streak);
            renderStats(data.stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadLeaderboard() {
    try {
        const response = await fetch(`${API_URL}/leaderboard`);
        const data = await response.json();
        
        if (data.success) {
            renderLeaderboard(data.leaderboard);
        }
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

// ==================== Render Functions ====================

function renderHabits() {
    const habitList = document.getElementById('habitList');
    
    if (habits.length === 0) {
        habitList.innerHTML = '<p style="text-align: center; padding: 40px; color: var(--gray-600);">Chưa có thói quen nào. Nhấn nút + để thêm!</p>';
        return;
    }
    
    habitList.innerHTML = habits.map(habit => `
        <div class="habit-card">
            <div class="check-btn" id="check-${habit.id}" onclick="toggleCompletion(${habit.id})">
            </div>
            <div class="habit-info">
                <div class="habit-title">${habit.icon} ${habit.name}</div>
                <div class="habit-meta">
                    <span>🔥 ${habit.streak || 0}</span>
                </div>
            </div>
            <button class="predict-btn" onclick="openPredictModal(${habit.id})">🔮 Dự đoán</button>
        </div>
    `).join('');
}

function renderCalendar(history) {
    const calendar = document.getElementById('calendar');
    const days = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
    
    calendar.innerHTML = history.map((day, index) => `
        <div class="day-item">
            <div class="day-label">${days[index]}</div>
            <div class="day-bar ${day.percentage >= 70 ? 'completed' : ''}">
                <div class="day-percentage">${day.percentage}%</div>
            </div>
        </div>
    `).join('');
}

function renderStats(stats) {
    const statsGrid = document.getElementById('statsGrid');
    
    statsGrid.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${stats.total_habits}</div>
            <div class="stat-label">Thói quen đang theo dõi</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.current_streak}</div>
            <div class="stat-label">Chuỗi ngày hiện tại</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.completion_rate}%</div>
            <div class="stat-label">Tỷ lệ hoàn thành</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${stats.longest_streak}</div>
            <div class="stat-label">Chuỗi dài nhất</div>
        </div>
    `;
}

function renderLeaderboard(leaderboard) {
    const list = document.getElementById('leaderboardList');
    
    const medals = { 1: '🥇', 2: '🥈', 3: '🥉' };
    
    list.innerHTML = leaderboard.map(user => `
        <div class="leaderboard-item">
            <div class="rank ${user.rank <= 3 ? 'top' : ''}">${medals[user.rank] || user.rank}</div>
            <div class="leaderboard-avatar">${user.avatar}</div>
            <div class="leaderboard-info">
                <div class="leaderboard-name">${user.name}</div>
                <div class="leaderboard-score">Chuỗi: ${user.streak} ngày • Điểm: ${user.score}</div>
            </div>
        </div>
    `).join('');
}

function updateStreakDisplay(streak) {
    document.getElementById('streakDays').textContent = streak;
}

// ==================== Habit Actions ====================

async function addHabit(event) {
    event.preventDefault();
    
    const name = document.getElementById('habitName').value;
    const icon = document.getElementById('habitIcon').value || '🎯';
    
    try {
        const response = await fetch(`${API_URL}/habits`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, icon })
        });
        
        const data = await response.json();
        
        if (data.success) {
            habits.push(data.habit);
            renderHabits();
            closeModal('addModal');
            
            // Reset form
            document.getElementById('habitName').value = '';
            document.getElementById('habitIcon').value = '';
            
            showToast('✅ Thêm thói quen thành công!');
        }
    } catch (error) {
        showToast('❌ Lỗi khi thêm thói quen!');
        console.error(error);
    }
}

async function toggleCompletion(habitId) {
    const checkBtn = document.getElementById(`check-${habitId}`);
    const isCompleted = checkBtn.classList.contains('completed');
    
    try {
        const response = await fetch(`${API_URL}/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                habit_id: habitId,
                completed: !isCompleted
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            checkBtn.classList.toggle('completed');
            checkBtn.innerHTML = checkBtn.classList.contains('completed') ? '✓' : '';
            
            // Reload stats and calendar
            loadStats();
            loadCalendar();
            
            showToast(checkBtn.classList.contains('completed') ? '✅ Đã hoàn thành!' : '⭕ Đã bỏ tick');
        }
    } catch (error) {
        showToast('❌ Lỗi khi cập nhật!');
        console.error(error);
    }
}

// ==================== Prediction ====================

function openPredictModal(habitId) {
    currentHabitId = habitId;
    document.getElementById('predictForm').style.display = 'block';
    document.getElementById('predictResult').style.display = 'none';
    document.getElementById('predictLoading').style.display = 'none';
    document.getElementById('closeResultBtn').style.display = 'none';
    document.getElementById('predictModal').classList.add('show');
}

async function submitPrediction() {
    // Show loading
    document.getElementById('predictForm').style.display = 'none';
    document.getElementById('predictLoading').style.display = 'block';
    
    const formData = {
        habit_id: currentHabitId,
        motivation_level: parseInt(document.getElementById('motivation_level').value),
        self_discipline: parseInt(document.getElementById('self_discipline').value),
        study_hours_per_week: parseInt(document.getElementById('study_hours').value),
        sleep_hours_per_day: parseFloat(document.getElementById('sleep_hours').value),
        // Default values
        age: 20,
        gender: 'Male',
        year: 2,
        gpa: 3.0,
        stress_level: 5,
        time_management_skill: 5,
        goal_clarity: 5,
        family_support: 5,
        study_environment_quality: 5,
        distance_to_school_km: 10,
        meditation_frequency: 3,
        reading_frequency: 3,
        exercise_frequency: 3,
        meal_planning_frequency: 3,
        journaling_frequency: 2,
        week: 6
    };
    
    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Hide loading, show result
            document.getElementById('predictLoading').style.display = 'none';
            document.getElementById('predictResult').style.display = 'block';
            document.getElementById('closeResultBtn').style.display = 'block';
            
            // Display prediction
            document.getElementById('predictScore').textContent = data.prediction.score;
            document.getElementById('predictCategory').textContent = data.prediction.category;
            document.getElementById('predictRecommendation').textContent = data.prediction.recommendation;
            
            // Set color based on score
            const category = document.getElementById('predictCategory');
            if (data.prediction.score >= 80) {
                category.style.color = 'var(--success)';
            } else if (data.prediction.score >= 60) {
                category.style.color = 'var(--secondary)';
            } else {
                category.style.color = 'var(--danger)';
            }
        }
    } catch (error) {
        showToast('❌ Lỗi khi dự đoán!');
        console.error(error);
        closeModal('predictModal');
    }
}

// ==================== UI Functions ====================

function showTab(tabName) {
    // Update tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Hide all content
    document.getElementById('practiceContent').style.display = 'none';
    document.getElementById('statsContent').style.display = 'none';
    document.getElementById('leaderboardContent').style.display = 'none';
    document.getElementById('dateFilters').style.display = 'none';
    
    // Show selected content
    switch(tabName) {
        case 'practice':
            document.getElementById('practiceContent').style.display = 'block';
            document.getElementById('dateFilters').style.display = 'flex';
            break;
        case 'stats':
            document.getElementById('statsContent').style.display = 'block';
            loadStats();
            break;
        case 'leaderboard':
            document.getElementById('leaderboardContent').style.display = 'block';
            loadLeaderboard();
            break;
    }
}

function showSection(section) {
    // Update menu items
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Reset to practice tab
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab')[0].classList.add('active');
    
    document.getElementById('practiceContent').style.display = 'block';
    document.getElementById('statsContent').style.display = 'none';
    document.getElementById('leaderboardContent').style.display = 'none';
    document.getElementById('dateFilters').style.display = 'flex';
}

function changeDate(type) {
    document.querySelectorAll('.date-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Here you can load data for selected date
    showToast(type === 'today' ? '📅 Hiển thị hôm nay' : '📅 Hiển thị hôm qua');
}

function showAddModal() {
    document.getElementById('addModal').classList.add('show');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('show');
    }
});

// Toast notification
function showToast(message) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast show';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 32px;
        right: 32px;
        background: var(--gray-900);
        color: var(--white);
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
    .spinner {
        border: 4px solid rgba(124, 58, 237, 0.2);
        border-top: 4px solid var(--primary);
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);