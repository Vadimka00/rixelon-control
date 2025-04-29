import os
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from flask import url_for
from models import User, TempCode, Notification  # Импорт моделей
from core import app, db, MOSCOW_TZ  # Импорт базы данных и часового пояса


# Вспомогательные функции

# Получаем данные пользователя
def get_user_by_id(user_id):
    user= db.session.get(User, user_id)
    if user:
        return {
            'id': user.id,
            'email': user.email,
            'telegram_id': user.telegram_id,
            'telegram_username': user.telegram_username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'reg_date': user.reg_date,
            'photo': user.photo
        }
    return None

def get_user_by_telegram_id(telegram_id):
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if user:
        return {
            'id': user.id,
            'email': user.email,
            'telegram_id': user.telegram_id,
            'telegram_username': user.telegram_username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'reg_date': user.reg_date,
            'photo': user.photo
        }
    return None

def count_user_notifications(telegram_id):
    if not telegram_id:
        raise ValueError("telegram_id не может быть пустым")

    count = Notification.query.filter_by(to_telegram_id=telegram_id).count()
    return count

# Сохраняем код авторизации
def save_temp_code(email, code, role='user', ttl_minutes=3):
    expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
    existing = TempCode.query.filter_by(email=email).first()
    if existing:
        existing.code = code
        existing.role = role
        existing.expires = expires_at
    else:
        new_entry = TempCode(email=email, code=code, role=role, expires=expires_at)
        db.session.add(new_entry)
    db.session.commit()

# Проверка кода авторизации
def verify_reg_code(email, code):
    temp = TempCode.query.filter_by(email=email).first()
    if not temp or temp.code != code:
        return {'success': False, 'error': 'Неверный код'}
    if temp.is_expired():
        db.session.delete(temp)
        db.session.commit()
        return {'success': False, 'error': 'Код устарел'}
    
    return {'success': True, 'data': temp}

# Поиск по email коду
def get_email_by_email_code(email_code):
    all_codes = TempCode.query.all()
    for entry in all_codes:
        if email_to_code(entry.email) == email_code:
            return entry.email
    return None

# Создание пользователя
def create_user_from_temp(email):
    temp = TempCode.query.filter_by(email=email).first()
    if not temp:
        return None
    user = User(
        email=email,
        telegram_id=temp.telegram_id,
        telegram_username=temp.telegram_username,
        first_name=temp.first_name,
        last_name=temp.last_name,
        role=temp.role,
        reg_date=datetime.now(MOSCOW_TZ),
        photo=temp.photo
    )
    db.session.add(user)
    db.session.commit()
    return user


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def generate_code():
    return f"{secrets.randbelow(999_999):06d}"  # Криптографически безопасный код

def email_to_code(email):
    # Создаем хеш SHA-256 от email
    hash_object = hashlib.sha256(email.encode())
    hash_bytes = hash_object.digest()  # Получаем бинарное представление (32 байта)
    
    # Преобразуем все байты хеша в одно большое целое число
    full_number = int.from_bytes(hash_bytes, byteorder='big')  # 256-битное число
    
    # Генерируем 6-значный код из всех битов хеша
    code = 0
    for i, byte in enumerate(hash_bytes):
        # Используем каждый байт для формирования кода
        code = (code * 10 + (byte % 10)) % 1000000000000000000
    
    return f"{code:018d}"  # Всегда 18 цифр

def add_initials_to_image(image, first_name, last_name):
    """Добавляет инициалы ровно по центру изображения 500x500."""
    draw = ImageDraw.Draw(image)
    font_path = os.path.join( app.root_path,'static', 'fonts', 'KronaOne-Regular.ttf')
    font = ImageFont.truetype(font_path, 250)  # Размер шрифта 200

    initials = ""
    if first_name:
        initials += first_name[0].upper()
    if last_name:
        initials += last_name[0].upper()
    
    # Если нет ни имени, ни фамилии, используем 'R' по умолчанию
    if not initials:
        initials = "R"

    # Получаем точные границы текста
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Центрируем (500x500 - размер изображения)
    x = (500 - text_width) / 2
    y = (500 - text_height) / 2 - 50

    # Рисуем текст (fill - цвет текста, например, белый (255, 255, 255))
    draw.text((x, y), initials, font=font, fill=(255, 255, 255))

    return image

def create_profile_image(first_name, last_name, telegram_id, width=500, height=500):
    """Создает изображение с фоновым изображением и инициалами пользователя и сохраняет его."""
    # Загружаем фоновое изображение
    bg_path = os.path.join( app.root_path,'static', 'images', 'bg', 'profile_bg.png')
    try:
        background = Image.open(bg_path).convert('RGB')
        # Ресайзим если нужно (хотя лучше использовать изображение нужного размера)
        background = background.resize((width, height))
    except FileNotFoundError:
        # Если фоновое изображение не найдено, создаем градиентный фон как запасной вариант
        background = Image.new('RGB', (width, height))
        for y in range(height):
            r = int(141 + (163 - 141) * y / height)
            g = int(114 + (161 - 114) * y / height)
            b = int(225 + (246 - 225) * y / height)
            for x in range(width):
                background.putpixel((x, y), (r, g, b))

    # Добавляем инициалы
    profile_image = add_initials_to_image(background, first_name, last_name)

    # Путь для сохранения изображения
    relative_path = os.path.join( app.root_path,'static', 'images', 'uploads', 'profile_photo', f'{telegram_id}_profile_photo.jpg')
    
    # Создаем директорию, если её не существует
    os.makedirs(os.path.dirname(relative_path), exist_ok=True)

    # Сохраняем файл
    profile_image.save(relative_path)

    # Формируем ссылку на изображение
    profile_photo_url = url_for('static', filename=f'images/uploads/profile_photo/{telegram_id}_profile_photo.jpg', _external=True)

    return profile_photo_url