from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from car_website import db
from car_website.models import Car, Like


# Створюємо Blueprint для головних маршрутів
main_routes = Blueprint('main', __name__)

# Маршрут для перегляду списку автомобілів
@main_routes.route('/cars')
def view_cars():
    cars = Car.query.all()
    return render_template('cars.html', cars=cars)


