# Модели БД
from datetime import datetime, date, time
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from core import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telegram_id = db.Column(db.String(50), unique=True)
    telegram_username = db.Column(db.String(50))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role = db.Column(db.String(50))
    reg_date = db.Column(db.DateTime, nullable=False)
    photo = db.Column(db.String(512), nullable=True)

class UserLogin(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    last_login = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', backref=db.backref('login_record', uselist=False))

class TempCode(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    code = db.Column(db.String(10), nullable=False)
    role = db.Column(db.String(50), default='user')
    expires = db.Column(db.DateTime, nullable=False)
    telegram_id = db.Column(db.BigInteger, nullable=True)
    telegram_username = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    photo = db.Column(db.String(512), nullable=True)

    def is_expired(self):
        return datetime.now() > self.expires

class Task(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), ForeignKey('user.telegram_id'), nullable=False)
    collaborator_id = db.Column(db.String(50), ForeignKey('user.telegram_id'), nullable=True)
    category_filter = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    task_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    title = db.Column(db.Text, nullable=False)
    
    user = relationship('User', foreign_keys=[telegram_id], backref='tasks')
    collaborator = relationship('User', foreign_keys=[collaborator_id])

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_telegram_id = db.Column(db.String(50), nullable=False)
    to_telegram_id = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_telegram_id = db.Column(db.String(50), nullable=False)
    user2_telegram_id = db.Column(db.String(50), nullable=False)
    since = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    to_telegram_id = db.Column(db.String(50), nullable=True)  # null = для всех
    from_telegram_id = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)