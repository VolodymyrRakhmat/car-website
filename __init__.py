from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Налаштування програми
    app.config['SECRET_KEY'] = '1'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:vovan12@localhost/car_website'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Ініціалізація бази даних
    db.init_app(app)
    with app.app_context():
        from models import Users, Car  # Імпорт моделей
        db.create_all()  # Створюємо таблиці

    return app
