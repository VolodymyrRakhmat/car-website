from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    photo = db.Column(db.String(150), nullable=True)
    role = db.Column(db.String(50), nullable=False, default='user')  # Додано поле для ролі

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Car(db.Model):
    __tablename__ = 'cars'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)  # Виробник
    body_type = db.Column(db.String(100), nullable=False)  # Тип кузова
    engine_power = db.Column(db.Integer, nullable=False)  # Потужність двигуна
    acceleration = db.Column(db.Float, nullable=False)  # Прискорення 0-100 км/год
    top_speed = db.Column(db.Float, nullable=False)  # Максимальна швидкість
    fuel_consumption = db.Column(db.Float, nullable=False)  # Розхід палива (л/100 км)
    weight = db.Column(db.Float, nullable=False)  # Маса автомобіля (кг)
    trunk_volume = db.Column(db.Float, nullable=False)  # Об'єм багажника (л)
    price = db.Column(db.Float, nullable=False)  # Ціна
    description = db.Column(db.String(300), nullable=False)  # Короткий опис
    image = db.Column(db.String(150), nullable=True)  # Фото

class News(db.Model):
    __tablename__ = 'news'  # Таблиця для новин
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)
