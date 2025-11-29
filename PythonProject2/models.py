# ВАЖНО: Мы импортируем объект 'db' из файла config.py,
# так как там же инициализированы игровые модели.
from config import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# --- МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ ---

class User(db.Model, UserMixin):
    """Модель пользователя для авторизации."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    # Храним хеш пароля, а не сам пароль
    password = db.Column(db.String(255), nullable=False)
    zodiac = db.Column(db.String(20), nullable=True)

    # Явный конструктор для улучшения совместимости с PyCharm и ясности
    def __init__(self, username, password, zodiac):
        self.username = username
        self.password = password
        self.zodiac = zodiac

    def get_id(self):
        """Обязательный метод для Flask-Login."""
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username}>'