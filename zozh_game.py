"""
Магическое приложение для ЗОЖ - Веб-версия
Запускается в браузере, затем можно превратить в мобильное приложение
"""

from flask import Flask, render_template, request, jsonify, session
import json
import os
import random
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ===== Класс для хранения данных =====

class HealthData:
    def __init__(self):
        self.categories = []
        self.activities = []
        self.history = []
        self.points = 0
        self.level = 1
        self.streak = 0
        self.last_activity_date = None
        self.achievements = []
        
    def add_category(self, name, icon="✨"):
        if not any(c["name"] == name for c in self.categories):
            self.categories.append({"name": name, "icon": icon})
            return True
        return False
        
    def remove_category(self, index):
        if 0 <= index < len(self.categories):
            category_name = self.categories[index]["name"]
            self.activities = [a for a in self.activities if a["category"] != category_name]
            self.categories.pop(index)
            return True
        return False
            
    def add_activity(self, name, category, points, description=""):
        if name and category and points > 0:
            self.activities.append({
                "name": name,
                "category": category,
                "points": points,
                "description": description,
                "completed": False
            })
            return True
        return False
        
    def remove_activity(self, index):
        if 0 <= index < len(self.activities):
            self.activities.pop(index)
            return True
        return False
            
    def complete_activity(self, index):
        if 0 <= index < len(self.activities):
            activity = self.activities[index]
            if not activity["completed"]:
                activity["completed"] = True
                self.points += activity["points"]
                self.history.append({
                    "activity": activity["name"],
                    "points": activity["points"],
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                
                if self.points >= self.level * 100:
                    self.level += 1
                    self.achievements.append(f"Достигнут уровень {self.level}!")
                    
                today = datetime.now().date()
                if self.last_activity_date:
                    try:
                        last_date = datetime.strptime(self.last_activity_date, "%Y-%m-%d").date()
                        if (today - last_date).days == 1:
                            self.streak += 1
                        elif (today - last_date).days > 1:
                            self.streak = 0
                    except:
                        self.streak = 1
                else:
                    self.streak = 1
                self.last_activity_date = today.strftime("%Y-%m-%d")
                
                return True
        return False
        
    def reset_activity(self, index):
        if 0 <= index < len(self.activities):
            activity = self.activities[index]
            if activity["completed"]:
                activity["completed"] = False
                self.points -= activity["points"]
                return True
        return False
        
    def get_statistics(self):
        completed = sum(1 for a in self.activities if a["completed"])
        total = len(self.activities)
        return {
            "completed": completed,
            "total": total,
            "progress": (completed / total * 100) if total > 0 else 0,
            "points": self.points,
            "level": self.level,
            "streak": self.streak,
            "achievements": self.achievements
        }
        
    def save_data(self, filename="health_data.json"):
        try:
            data = {
                "categories": self.categories,
                "activities": self.activities,
                "history": self.history,
                "points": self.points,
                "level": self.level,
                "streak": self.streak,
                "last_activity_date": self.last_activity_date,
                "achievements": self.achievements
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False
            
    def load_data(self, filename="health_data.json"):
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.categories = data.get("categories", [])
                    self.activities = data.get("activities", [])
                    self.history = data.get("history", [])
                    self.points = data.get("points", 0)
                    self.level = data.get("level", 1)
                    self.streak = data.get("streak", 0)
                    self.last_activity_date = data.get("last_activity_date", None)
                    self.achievements = data.get("achievements", [])
                return True
            except Exception as e:
                print(f"Ошибка загрузки: {e}")
                return False
        return False

# Создаем экземпляр данных
data = HealthData()
data.load_data()

# ===== Функция для заполнения примерами =====
def setup_sample_data():
    """Создание примеров активностей и категорий"""
    if not data.categories:
        categories = [
            ("Физическая активность", "🏃"),
            ("Питание", "🥗"),
            ("Духовное развитие", "🧘"),
            ("Сон", "😴")
        ]
        for name, icon in categories:
            data.add_category(name, icon)
        
        activities = [
            ("Утренняя зарядка", "Физическая активность", 10),
            ("Пробежка", "Физическая активность", 20),
            ("Съесть фрукт", "Питание", 5),
            ("Выпить воды", "Питание", 3),
            ("Медитация", "Духовное развитие", 15),
            ("Чтение книги", "Духовное развитие", 10),
            ("Ранний сон", "Сон", 10)
        ]
        for name, category, points in activities:
            data.add_activity(name, category, points)
        
        data.save_data()

# Заполняем примерами
setup_sample_data()

# ===== Маршруты Flask =====

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    return jsonify(data.get_statistics())

@app.route('/api/activities')
def get_activities():
    return jsonify(data.activities)

@app.route('/api/categories')
def get_categories():
    return jsonify(data.categories)

@app.route('/api/history')
def get_history():
    return jsonify(data.history[-50:])

@app.route('/api/achievements')
def get_achievements():
    return jsonify(data.achievements)

@app.route('/api/activity/add', methods=['POST'])
def add_activity():
    try:
        name = request.json.get('name')
        category = request.json.get('category')
        points = request.json.get('points', 0)
        
        if data.add_activity(name, category, int(points)):
            data.save_data()
            return jsonify({'success': True, 'message': 'Активность добавлена!'})
        return jsonify({'success': False, 'message': 'Ошибка добавления'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/activity/delete/<int:index>', methods=['DELETE'])
def delete_activity(index):
    if data.remove_activity(index):
        data.save_data()
        return jsonify({'success': True, 'message': 'Активность удалена!'})
    return jsonify({'success': False, 'message': 'Ошибка удаления'})

@app.route('/api/activity/complete/<int:index>', methods=['POST'])
def complete_activity(index):
    if data.complete_activity(index):
        data.save_data()
        return jsonify({
            'success': True, 
            'message': 'Активность выполнена!', 
            'points': data.activities[index]['points']
        })
    return jsonify({'success': False, 'message': 'Уже выполнено'})

@app.route('/api/activity/reset/<int:index>', methods=['POST'])
def reset_activity(index):
    if data.reset_activity(index):
        data.save_data()
        return jsonify({'success': True, 'message': 'Сброшено!'})
    return jsonify({'success': False, 'message': 'Ошибка'})

@app.route('/api/category/add', methods=['POST'])
def add_category():
    try:
        name = request.json.get('name')
        icon = request.json.get('icon', '✨')
        
        if data.add_category(name, icon):
            data.save_data()
            return jsonify({'success': True, 'message': 'Категория добавлена!'})
        return jsonify({'success': False, 'message': 'Категория уже существует'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/category/delete/<int:index>', methods=['DELETE'])
def delete_category(index):
    if data.remove_category(index):
        data.save_data()
        return jsonify({'success': True, 'message': 'Категория удалена!'})
    return jsonify({'success': False, 'message': 'Ошибка удаления'})

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    data.history.clear()
    data.save_data()
    return jsonify({'success': True, 'message': 'История очищена!'})

@app.route('/api/reset_all', methods=['POST'])
def reset_all():
    global data
    data = HealthData()
    setup_sample_data()
    data.save_data()
    return jsonify({'success': True, 'message': 'Всё сброшено!'})

if __name__ == '__main__':
    print("=" * 50)
    print("✨ Магический ЗОЖ приложение запущено!")
    print("📱 Откройте в браузере: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)