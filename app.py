import os
import logging
from datetime import datetime
from flask import Flask, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# Создание базового класса для моделей SQLAlchemy
class Base(DeclarativeBase):
    pass

# Инициализация объектов
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Создание приложения
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "юридическая_компания_секретный_ключ")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Настройка подключения к базе данных
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///legal_company.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Инициализация расширений
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, авторизуйтесь для доступа к этой странице.'

# Импорт моделей и маршрутов
with app.app_context():
    import models
    from routes import register_routes
    
    # Регистрация маршрутов
    register_routes(app)
    
    # Создание таблиц в базе данных
    db.create_all()

# Настройка загрузчика пользователей для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.get(User, int(user_id))

# Middleware для записи времени последнего активности пользователя
@app.before_request
def update_last_active():
    if current_user.is_authenticated:
        from models import User
        current_user.last_active = datetime.now()
        db.session.commit()

# Обработчик ошибки 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Обработчик ошибки 500
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Импорт для handler'а выше
from flask import render_template

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
