import json
import os

# Шлях до файлів
CARS_FILE = 'cars.json'
USERS_FILE = 'users.json'

# Завантаження даних з файлу
def load_data(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Збереження даних до файлу
def save_data(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_cars():
    return load_data(CARS_FILE)

# Робота з користувачами
def add_user(user):
    users = load_data(USERS_FILE)  # Завантажуємо поточних користувачів
    users.append(user)  # Додаємо нового користувача
    save_data(USERS_FILE, users)  # Зберігаємо оновлені дані

def get_user(username):
    users = load_data(USERS_FILE)
    for user in users:
        if user['username'] == username:
            return user
    return None
