from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
import sqlite3
from data import get_cars, add_user, get_user, load_data, save_data, USERS_FILE
from models import Car
import sys

sys.stdout.reconfigure(encoding='utf-8')


# Ініціалізація Flask додатку
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '1'

# Налаштування SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Використовуйте SQLite або іншу СУБД
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ініціалізація LoginManager після створення об'єкта `app`
login_manager = LoginManager()
login_manager.init_app(app)

# Ініціалізація бази даних
db = SQLAlchemy(app)

app = Flask(__name__)

# Шляхи до файлів з даними
car_file_path = 'static/data/CAR.xlsx'
bus_file_path = 'static/data/BUS.xlsx'
truck_file_path = 'static/data/TRUCK.xlsx'

def is_admin(user):
    return user['role'] == 'admin'

def is_owner(user):
    return user['role'] == 'owner'

def is_user(user):
    return user['role'] == 'user'

# Завантаження даних з Excel-файлів
car_df = pd.read_excel(car_file_path, sheet_name='Sheet1')
bus_df = pd.read_excel(bus_file_path, sheet_name='Аркуш1')
truck_df = pd.read_excel(truck_file_path, sheet_name='Sheet1')

# Перетворення стовпця "Фото" у рядок та заповнення значень за замовчуванням
truck_df['Фото'] = truck_df['Фото'].fillna('default.jpg').astype(str)

@app.route('/your_protected_route')
def your_protected_route():
    if 'user' not in session:
        flash('Ви повинні бути увійшли в систему, щоб переглянути цю сторінку.', 'danger')
        return redirect(url_for('login'))
    return render_template('your_template.html')

@app.route('/assign_role/<int:user_id>', methods=['POST'])
def assign_role(user_id):
    if 'user' not in session or session['role'] != 'owner':
        flash('У вас немає прав для цієї дії.', 'danger')
        return redirect(url_for('home'))

    new_role = request.form['role']
    connection = sqlite3.connect('your_database.db')
    cursor = connection.cursor()
    cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    connection.commit()
    connection.close()

    flash('Роль успішно оновлено.', 'success')
    return redirect(url_for('home'))

@app.route('/admin')
@login_required  # Якщо використовується функціонал для входу
def admin_dashboard():
    if session.get('role') == 'owner':
        return render_template('admin_dashboard.html')
    else:
        flash('У вас немає доступу до цієї сторінки.', 'danger')
        return redirect(url_for('home'))


@app.route('/vehicle/<int:vehicle_id>/reviews/delete/<int:review_id>', methods=['POST'])
def delete_review(vehicle_id, review_id):
    if 'user' not in session:
        flash('Ви повинні бути увійшли в систему, щоб видалити коментар.', 'danger')
        return redirect(request.referrer or url_for('car_details_view', model='Модель_не_знайдена'))

    current_user = session['user']

    connection = sqlite3.connect('your_database.db')
    cursor = connection.cursor()

    # Отримання автора коментаря
    cursor.execute('SELECT username FROM reviews WHERE id = ?', (review_id,))
    author = cursor.fetchone()

    if not author:
        flash('Відгук не знайдено.', 'danger')
        connection.close()
        return redirect(request.referrer or url_for('car_details_view', model='Модель_не_знайдена'))

    # Перевірка ролі користувача
    cursor.execute('SELECT role FROM users WHERE username = ?', (current_user,))
    user_role = cursor.fetchone()

    # Перевірка, чи користувач є автором, адміністратором або власником
    if current_user == author[0] or (user_role and user_role[0] in ['admin', 'owner']):
        cursor.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
        connection.commit()
        flash('Відгук успішно видалено.', 'success')
    else:
        flash('У вас немає прав для видалення цього відгуку.', 'danger')
        connection.close()
        return redirect(request.referrer or url_for('car_details_view', model='Модель_не_знайдена'))

    connection.close()
    return redirect(request.referrer or url_for('car_details_view', model='Модель_не_знайдена'))

@app.route('/get_bus_brands')
def get_bus_brands():
    query = request.args.get('query', '').lower()
    matching_brands = bus_df['Марка'][bus_df['Марка'].str.lower().str.contains(query)].unique().tolist()
    return jsonify({'brands': matching_brands})

@app.route('/get_bus_models')
def get_bus_models():
    brand = request.args.get('brand', '').lower()
    matching_models = bus_df[bus_df['Марка'].str.lower() == brand]['Модель'].unique().tolist()
    return jsonify({'models': matching_models})

@app.route('/bus_info', methods=['GET', 'POST'])
def bus_details_view():
    model = request.args.get('model')
    bus = bus_df[bus_df['Модель'] == model].to_dict(orient='records')
    if not bus:
        return "Модель не знайдена", 404

    # Переконайтеся, що у вашому DataFrame є стовпець 'id'
    vehicle_id = bus[0].get('id')
    if not vehicle_id:
        return "Ідентифікатор транспортного засобу відсутній", 400

    connection = sqlite3.connect('your_database.db')
    cursor = connection.cursor()

    # Отримання відгуків з бази даних
    cursor.execute("SELECT id, username, rating, comment, created_at FROM reviews WHERE vehicle_id = ?", (vehicle_id,))
    reviews = cursor.fetchall()

    avg_rating = sum([review[2] for review in reviews]) / len(reviews) if reviews else 0

    # Логіка додавання нового відгуку при надсиланні форми
    if request.method == 'POST':
        username = request.form['username']
        rating = int(request.form['rating'])
        comment = request.form['comment']

        cursor.execute("INSERT INTO reviews (username, vehicle_id, rating, comment) VALUES (?, ?, ?, ?)",
                       (username, vehicle_id, rating, comment))
        connection.commit()
        connection.close()

        flash('Відгук успішно додано!', 'success')
        return redirect(url_for('bus_details_view', model=model))

    connection.close()
    return render_template('bus_details.html', bus=bus[0], reviews=reviews, avg_rating=avg_rating)

@app.route('/truck_info', methods=['GET', 'POST'])
def truck_details_view():
    model = request.args.get('model')
    truck = truck_df[truck_df['Модель'] == model].to_dict(orient='records')
    if not truck:
        return "Модель не знайдена", 404

    vehicle_id = truck[0].get('id')  # Переконайтеся, що у вашому DataFrame є стовпець 'id'

    connection = sqlite3.connect('your_database.db')
    cursor = connection.cursor()

    cursor.execute("SELECT id, username, rating, comment, created_at FROM reviews WHERE vehicle_id = ?", (vehicle_id,))
    reviews = cursor.fetchall()

    avg_rating = sum([review[2] for review in reviews]) / len(reviews) if reviews else 0

    if request.method == 'POST':
        username = request.form['username']
        rating = int(request.form['rating'])
        comment = request.form['comment']

        cursor.execute("INSERT INTO reviews (username, vehicle_id, rating, comment) VALUES (?, ?, ?, ?)",
                       (username, vehicle_id, rating, comment))
        connection.commit()
        connection.close()

        flash('Відгук успішно додано!', 'success')
        return redirect(url_for('truck_details_view', model=model))

    connection.close()
    return render_template('truck_details.html', truck=truck[0], reviews=reviews, avg_rating=avg_rating)

@app.route('/get_truck_models')
def get_truck_models():
    brand = request.args.get('brand')
    if brand:
        truck_models = truck_df[truck_df['Марка'].str.contains(brand, case=False, na=False)]['Модель'].unique().tolist()
        return jsonify({'models': sorted(truck_models)})
    else:
        return jsonify({'models': []})

@app.route('/get_truck_brands')
def get_truck_brands():
    query = request.args.get('query', '')
    brands = truck_df['Марка'].unique().tolist()
    filtered_brands = [brand for brand in brands if query.lower() in brand.lower()]
    return jsonify({'brands': filtered_brands})

@app.route('/car/<int:car_id>')
def car_details(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template('car_details.html', car=car)

@app.route('/get_models')
def get_models():
    brand = request.args.get('brand')
    models = car_df[car_df['Марка'].str.contains(brand, case=False, na=False)]['Модель'].unique().tolist()
    return jsonify({'models': models})

@app.route('/car_info', methods=['GET', 'POST'])
def car_details_view():
    # Отримання моделі автомобіля з параметра запиту
    model = request.args.get('model')
    car = car_df[car_df['Модель'] == model].to_dict(orient='records')
    if not car:
        return "Модель не знайдена", 404

    # Переконайтеся, що у вашому DataFrame є стовпець 'id'
    vehicle_id = car[0].get('id')
    if not vehicle_id:
        return "Ідентифікатор автомобіля відсутній", 400

    # Підключення до бази даних
    connection = sqlite3.connect('your_database.db')
    cursor = connection.cursor()

    # Отримання відгуків з бази даних
    cursor.execute("SELECT id, username, rating, comment, created_at FROM reviews WHERE vehicle_id = ?", (vehicle_id,))
    reviews = cursor.fetchall()

    # Обчислення середньої оцінки
    avg_rating = sum([review[2] for review in reviews]) / len(reviews) if reviews else 0

    # Додавання нового відгуку при надсиланні форми
    if request.method == 'POST':
        username = request.form['username']
        rating = int(request.form['rating'])
        comment = request.form['comment']

        # Додавання нового відгуку в базу даних
        cursor.execute("INSERT INTO reviews (username, vehicle_id, rating, comment) VALUES (?, ?, ?, ?)",
                       (username, vehicle_id, rating, comment))
        connection.commit()

        flash('Відгук успішно додано!', 'success')
        return redirect(url_for('car_details_view', model=model))

    # Закриття підключення до бази даних
    connection.close()

    # Передача даних у шаблон
    return render_template('car_details.html', car=car[0], reviews=reviews, avg_rating=avg_rating)


@app.route('/get_brands')
def get_brands():
    query = request.args.get('query', '')
    brands = car_df[car_df['Марка'].str.contains(query, case=False, na=False)]['Марка'].unique().tolist()
    return jsonify({'brands': brands})


@app.route('/cars')
def show_cars():
    # Додайте стовпець 'id' зі значеннями від 1 до кількості рядків у DataFrame
    car_df['id'] = range(1, len(car_df) + 1)

    # Перетворіть DataFrame у список словників
    cars_list = car_df.to_dict(orient='records')

    # Запис даних у файл для перевірки
    with open('output_check.txt', 'w', encoding='utf-8') as f:
        f.write(str(cars_list[:5]))

    # Передаємо дані у шаблон
    return render_template('cars.html', cars=cars_list)


@app.route('/buses')
def show_buses():
    return render_template('buses.html', buses=bus_df)

# Ініціалізація Flask додатку
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '1'

@app.route('/')
def home():
    cars = get_cars()  # Отримуємо всі автомобілі з файлу
    return render_template('index.html', cars=cars)

# Реєстрація користувачів
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if get_user(username):
            flash('Це ім’я користувача вже зайнято.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        add_user({'username': username, 'password': hashed_password})

        flash('Успішна реєстрація! Ви можете увійти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'user' not in session:
        flash('Будь ласка, увійдіть, щоб отримати доступ до кабінету.', 'danger')
        return redirect(url_for('login'))

    user = get_user(session['user'])

    if request.method == 'POST':
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        photo = request.files['photo']

        # Збереження фото
        if photo and photo.filename != '':
            photo_path = f'uploads/{photo.filename}'  # Відносний шлях для використання у шаблоні
            photo.save(os.path.join('static', photo_path))
            user['photo'] = photo_path

        # Оновлення даних користувача
        user['phone'] = phone
        user['email'] = email
        user['address'] = address

        # Збереження оновлених даних
        users = load_data(USERS_FILE)
        for u in users:
            if u['username'] == user['username']:
                u['phone'] = user['phone']
                u['email'] = user['email']
                u['address'] = user['address']
                if 'photo' in user:
                    u['photo'] = user['photo']
                break
        save_data(USERS_FILE, users)

        flash('Ваш профіль успішно оновлено!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('user_dashboard.html', user=user)

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/trucks')
def show_trucks():
    # Завантажуємо дані з файлу Excel
    trucks_df = pd.read_excel('static/data/TRUCK.xlsx', sheet_name='Sheet1')
    
    # Перетворюємо DataFrame у список словників для використання у шаблоні
    trucks_list = trucks_df.to_dict(orient='records')
    
    return render_template('trucks.html', trucks=trucks_list)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Збереження повідомлення у текстовий файл
        with open('messages.txt', 'a', encoding='utf-8') as f:
            f.write(f"Ім'я: {name}\nЕлектронна пошта: {email}\nПовідомлення:\n{message}\n{'-'*40}\n")

        flash('Ваше повідомлення було успішно відправлено!', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')

# Авторизація користувачів
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)

        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            session['role'] = user['role']
            flash('Успішний вхід!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Невірне ім’я користувача або пароль.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Ви вийшли з акаунта.', 'success')
    return redirect(url_for('home'))

# Запуск додатку
if __name__ == '__main__':
    app.run(debug=True)
