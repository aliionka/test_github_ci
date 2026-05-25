from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

db = SQLAlchemy() # объект создаётся без приложения

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app) # связываем БД с приложением

    # Импорт моделей внутри фабрики, чтобы избежать циклических импортов
    from . import models

    # Регистрация blueprints/роутов
    from .views import bp
    app.register_blueprint(bp)

    # Создание таблиц
    with app.app_context():
        db.create_all()

    return app
