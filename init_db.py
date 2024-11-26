from app import create_app, db  # Зробіть правильний імпорт

app = create_app()

with app.app_context():
    db.create_all()  # Це створить всі таблиці в базі даних
    print("База даних ініціалізована!")
