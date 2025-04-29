# Flask и база данных
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# SQLAlchemy — расширенные инструменты
from sqlalchemy import ForeignKey, CheckConstraint, extract, func, Interval
from sqlalchemy.orm import validates, relationship
from sqlalchemy.ext.hybrid import hybrid_property

# Работа с файлами и путями
from urllib.parse import unquote, quote_plus
from dotenv import load_dotenv
import os
import secrets

# Работа с файлами и путями
from urllib.parse import unquote, quote_plus
from dotenv import load_dotenv
import os
import secrets

# Время и дата
from datetime import datetime, timedelta, date, time
import time  # для time.sleep()

# Хэширование и безопасность
import hashlib
import re

# Логирование и отладка
import logging
import traceback

# Веб-запросы
import requests

from threading import Thread

from bot import run_bot, friends_notification, new_task_notification, auth_notification, confirmation_code
from utils import get_user_by_id, get_user_by_telegram_id, count_user_notifications, save_temp_code, verify_reg_code, create_user_from_temp, generate_code, email_to_code  
from models import User, UserLogin, TempCode, Task, FriendRequest, Friendship, Notification   # Модели для User и TempCode
from core import app, db, bot, MOSCOW_TZ

# Настройка логгера
logging.basicConfig(
    filename='logs/error_log.txt',
    level=logging.INFO,  # INFO чтобы видеть и обычные действия
    format='%(asctime)s [%(levelname)s] %(message)s',
    encoding='utf-8'
)

# Отключение кэширования
@app.after_request
def add_no_cache_headers(response):
    if request.path in ['/', '/dashboard']:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
    return response

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return render_template('index.html')
    
    user = get_user_by_id(session['user_id'])
    
    # Получаем уведомления для текущего пользователя или общие уведомления
    notifications = Notification.query.filter(
        (Notification.to_telegram_id == user['telegram_id']) | 
        (Notification.to_telegram_id.is_(None))
    ).order_by(Notification.timestamp.desc()).all()
    
    notifications_list = []
    for notification in notifications:
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'timestamp': notification.timestamp.isoformat(),
            'from_telegram_id': notification.from_telegram_id
        }
        
        # Если есть отправитель, добавляем его имя
        if notification.from_telegram_id:
            sender = User.query.filter_by(telegram_id=notification.from_telegram_id).first()
            if sender:
                notification_data['sender_name'] = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
        
        notifications_list.append(notification_data)
    
    return jsonify(notifications_list)

    

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        count_notif = count_user_notifications(user['telegram_id'])
        if user:
            return render_template('dashboard.html', role=user['role'], user=user, count_notif=count_notif)
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    user_id = session.get('user_id')
    current_user = get_user_by_id(session['user_id'])
    if not current_user:
        return jsonify([])

    search_query = f"%{query}%"

    # Найдём telegram_id пользователей, с которыми уже дружит текущий
    friends = db.session.query(Friendship).filter(
        db.or_(
            Friendship.user1_telegram_id == current_user['telegram_id'],
            Friendship.user2_telegram_id == current_user['telegram_id']
        )
    ).all()

    friend_ids = {
        f.user1_telegram_id if f.user1_telegram_id != current_user['telegram_id'] else f.user2_telegram_id
        for f in friends
    }

    # Найдём запросы, отправленные текущим пользователем
    requested_ids = {
        r.to_telegram_id for r in FriendRequest.query.filter_by(from_telegram_id=current_user['telegram_id']).all()
    }

    users = User.query.filter(
        db.or_(
            (User.first_name + " " + db.func.coalesce(User.last_name, "")).ilike(search_query),
            User.telegram_username.ilike(search_query)
        )
    ).limit(20).all()

    results = []
    for user in users:
        if user.telegram_id == current_user['telegram_id']:
            continue
        if user.telegram_id in friend_ids:
            continue  # уже в друзьях

        full_name = user.first_name
        if user.last_name:
            full_name += f" {user.last_name}"

        results.append({
            "full_name": full_name.strip(),
            "username": user.telegram_username or "",
            "photo": user.photo or "",
            "telegram_id": user.telegram_id,
            "requested": user.telegram_id in requested_ids
        })

    return jsonify(results)

@app.route('/add_friend', methods=['POST'])
def add_friend():
    try:
        data = request.get_json()
        logging.info(f"📥 Получен запрос на добавление в друзья: {data}")

        if not data:
            logging.warning("⚠️ Нет данных в теле запроса")
            return jsonify(success=False, error="Нет данных в запросе"), 400

        telegram_id = data.get('telegram_id')
        if not telegram_id:
            logging.warning(f"⚠️ Нет telegram_id в запросе: {data}")
            return jsonify(success=False, error="Нет telegram_id"), 400

        user_id = session.get('user_id')
        current_user = get_user_by_id(user_id)
        if not current_user:
            logging.warning(f"⚠️ Пользователь не найден в сессии: {user_id}")
            return jsonify(success=False, error="Пользователь не найден в сессии"), 400

        logging.info(f"🔍 Проверка на существующий запрос от {current_user['telegram_id']} к {telegram_id}")
        existing = FriendRequest.query.filter_by(
            from_telegram_id=current_user['telegram_id'],
            to_telegram_id=telegram_id
        ).first()

        if existing:
            logging.info(f"✅ Запрос уже существует от {current_user['telegram_id']} к {telegram_id}")
            return jsonify(success=True)

        # Сохраняем запрос
        new_request = FriendRequest(
            from_telegram_id=current_user['telegram_id'],
            to_telegram_id=telegram_id
        )
        db.session.add(new_request)
        logging.info(f"💾 Запрос в друзья сохранён от {current_user['telegram_id']} к {telegram_id}")

        user = get_user_by_telegram_id(current_user['telegram_id'])
        if not user:
            logging.warning(f"⚠️ Пользователь с telegram_id {telegram_id} не найден")
            return jsonify(success=False, error="Пользователь не найден"), 404

        first_name = user['first_name']
        last_name = user['last_name']
        full_name = f"{first_name} {last_name}" if last_name else first_name

        telegram_name = f'<a href="@{current_user["telegram_username"]}">{full_name}</a>'

        title = "Заявка в друзья"
        message = f"Привет, у тебя новая заявка в друзья от {telegram_name}!"

        # Уведомление
        notification = Notification(
            title=title,
            message="Привет, у тебя новая заявка в друзья от ",
            to_telegram_id=telegram_id,
            from_telegram_id=current_user['telegram_id']
        )
        db.session.add(notification)
        db.session.commit()
        logging.info(f"📬 Уведомление создано и сохранено: '{title}' для {telegram_id}")

        friends_notification(telegram_id, title, message, current_user['telegram_id'])
        logging.info(f"📨 Уведомление отправлено пользователю {telegram_id}")

        return jsonify(success=True)

    except Exception as e:
        logging.error(f"❌ Ошибка в /add_friend: {e}", exc_info=True)
        return jsonify(success=False, error="Ошибка сервера"), 500

@app.route('/friends')
def get_friends():
    if 'user_id' not in session:
        return render_template('index.html')

    current_user = get_user_by_id(session['user_id'])
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Получаем друзей и их данные за один запрос
    friends = db.session.query(
        User,
        Friendship
    ).join(
        Friendship,
        db.or_(
            db.and_(
                Friendship.user1_telegram_id == current_user['telegram_id'],
                Friendship.user2_telegram_id == User.telegram_id
            ),
            db.and_(
                Friendship.user2_telegram_id == current_user['telegram_id'],
                Friendship.user1_telegram_id == User.telegram_id
            )
        )
    ).all()
    
    # Получаем исходящие запросы (которые мы отправили)
    outgoing_requests = db.session.query(
        User,
        FriendRequest
    ).join(
        FriendRequest,
        FriendRequest.to_telegram_id == User.telegram_id
    ).filter(
        FriendRequest.from_telegram_id == current_user['telegram_id']
    ).all()
    
    # Получаем входящие запросы (которые нам отправили)
    incoming_requests = db.session.query(
        User,
        FriendRequest
    ).join(
        FriendRequest,
        FriendRequest.from_telegram_id == User.telegram_id
    ).filter(
        FriendRequest.to_telegram_id == current_user['telegram_id']
    ).all()
    
    return jsonify({
        'friends': [{
            'name': f"{user.first_name} {user.last_name}" if user.last_name else user.first_name,
            'username': user.telegram_username,
            'photo': user.photo,
            'telegram_id': user.telegram_id
        } for user, _ in friends],
        'outgoing_requests': [{
            'name': f"{user.first_name} {user.last_name}" if user.last_name else user.first_name,
            'username': user.telegram_username,
            'photo': user.photo,
            'telegram_id': user.telegram_id,
            'request_id': request.id  # ID запроса для обработки
        } for user, request in outgoing_requests],
        'incoming_requests': [{
            'name': f"{user.first_name} {user.last_name}" if user.last_name else user.first_name,
            'username': user.telegram_username,
            'photo': user.photo,
            'telegram_id': user.telegram_id,
            'request_id': request.id  # ID запроса для обработки
        } for user, request in incoming_requests],
        'current_user': {
            'first_name': current_user['first_name'],
            'last_name': current_user['last_name'],
            'username': current_user['telegram_username'],
            'photo': current_user['photo']
        }
    })

@app.route('/friend-tasks')
def get_friend_tasks():
    if 'user_id' not in session:
        return render_template('index.html')

    current_user = get_user_by_id(session['user_id'])
    if not current_user:
        return jsonify({'error': 'User not found'}), 404

    friends = db.session.query(User, Friendship).join(
        Friendship,
        db.or_(
            db.and_(
                Friendship.user1_telegram_id == current_user['telegram_id'],
                Friendship.user2_telegram_id == User.telegram_id
            ),
            db.and_(
                Friendship.user2_telegram_id == current_user['telegram_id'],
                Friendship.user1_telegram_id == User.telegram_id
            )
        )
    ).all()

    return jsonify({
        'friends': [{
            'name': f"{user.first_name} {user.last_name or ''}".strip(),
            'username': user.telegram_username,
            'photo': user.photo,
            'telegram_id': user.telegram_id
        } for user, _ in friends],
    })

@app.route('/reject_request', methods=['POST'])
def reject_request():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    data = request.get_json()
    user_id = data.get('user_id')
    
    # Находим запрос
    friend_request = db.session.execute(
        db.select(FriendRequest)
        .where(
            db.or_(
                db.and_(
                    FriendRequest.from_telegram_id == user['telegram_id'],
                    FriendRequest.to_telegram_id == user_id
                ),
                db.and_(
                    FriendRequest.from_telegram_id == user_id,
                    FriendRequest.to_telegram_id == user['telegram_id']
                )
            )
        )
    ).scalar_one_or_none()
    if not friend_request:
        return jsonify({'error': 'Request not found'}), 404
    
    # Находим и удаляем уведомление о заявке в друзья
    notification = db.session.execute(
        db.select(Notification)
        .where(
            db.and_(
                Notification.title == "Заявка в друзья",
                Notification.from_telegram_id == user_id,
                Notification.to_telegram_id == user['telegram_id']
            )
        )
    ).scalar_one_or_none()
    
    if notification:
        db.session.delete(notification)
        logging.info(f"🗑 Уведомление о заявке удалено для пользователя {user['telegram_id']}")
    
    # Удаляем запрос
    db.session.delete(friend_request)
    
    db.session.commit()

    return jsonify({'success': True})

@app.route('/accept_request', methods=['POST'])
def accept_request():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = get_user_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    data = request.get_json()
    user_id = data.get('user_id')
    
    # Находим запрос
    friend_request = db.session.execute(
        db.select(FriendRequest)
        .where(
            db.or_(
                db.and_(
                    FriendRequest.from_telegram_id == user['telegram_id'],
                    FriendRequest.to_telegram_id == user_id
                ),
                db.and_(
                    FriendRequest.from_telegram_id == user_id,
                    FriendRequest.to_telegram_id == user['telegram_id']
                )
            )
        )
    ).scalar_one_or_none()
    if not friend_request:
        return jsonify({'error': 'Request not found'}), 404
    
    # Находим и удаляем уведомление о заявке в друзья
    notification = db.session.execute(
        db.select(Notification)
        .where(
            db.and_(
                Notification.title == "Заявка в друзья",
                Notification.from_telegram_id == user_id,
                Notification.to_telegram_id == user['telegram_id']
            )
        )
    ).scalar_one_or_none()
    
    if notification:
        db.session.delete(notification)
        logging.info(f"🗑 Уведомление о заявке удалено для пользователя {user['telegram_id']}")
    
    # Создаем дружбу
    new_friendship = Friendship(
        user1_telegram_id=user['telegram_id'],
        user2_telegram_id=user_id
    )
    db.session.add(new_friendship)
    
    # Удаляем запрос
    db.session.delete(friend_request)
    
    # Подготавливаем данные для уведомления
    first_name = user['first_name']
    last_name = user['last_name']
    full_name = f"{first_name} {last_name}" if last_name else first_name
    telegram_name = f'<a href="@{user["telegram_username"]}">{full_name}</a>'

    message = f"{telegram_name} принял вашу заявку в друзья!"

    # Создаем уведомление о принятии заявки
    notification = Notification(
        title="Заявка принята",
        message=" принял вашу заявку в друзья!",
        to_telegram_id=user_id,
        from_telegram_id=user['telegram_id']
    )
    db.session.add(notification)
    
    db.session.commit()
    logging.info(f"📬 Новое уведомление создано: 'Заявка принята' для {user_id}")

    # Отправляем уведомление через Telegram (если функция friends_notification реализована)
    friends_notification(user_id, "Заявка принята", message, user['telegram_id'])
    logging.info(f"📨 Уведомление отправлено пользователю {user_id}")

    return jsonify({'success': True})

@app.route('/add/new_task', methods=['POST'])
def add_new_task():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    current_user = get_user_by_id(session['user_id'])
    if not current_user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    print('Полученные данные задачи:', data)

    try:
        category_map = {
            'work': 'Работа',
            'study': 'Учеба',
            'home': 'Дом',
            'health': 'Здоровье',
            'social': 'Встреча',
            'hobby': 'Хобби',
            'sleep': 'Сон'
        }

        # Валидация обязательных полей
        if not all([data.get('time_start'), data.get('time_end'), data.get('description')]):
            return jsonify({'error': 'Missing required fields'}), 400

        start_time = datetime.strptime(data['time_start'], '%H:%M').time()
        end_time = datetime.strptime(data['time_end'], '%H:%M').time()
        
        if start_time >= end_time:
            return jsonify({'error': 'Start time must be before end time'}), 400

        task_date_str = data.get('task_date')
        task_date = datetime.strptime(task_date_str, '%Y-%m-%d').date() if task_date_str else None
        description = data.get('description', '').strip()
        category_key = data.get('category')
        collaborator_id = data.get('friend_id')

        # Получаем русское название категории
        category_name = category_map.get(category_key) if category_key else None
        if category_key and not category_name:
            return jsonify({'error': 'Invalid category'}), 400

        def create_task(telegram_id, collaborator_id=None):
            return Task(
                telegram_id=telegram_id,
                collaborator_id=collaborator_id,
                category=category_name,
                category_filter=category_key,
                task_date=task_date,
                start_time=start_time,
                end_time=end_time,
                title=description
            )

        # Создаем задачу для текущего пользователя
        task = create_task(current_user['telegram_id'], collaborator_id)
        db.session.add(task)
        
        # Если есть collaborator, создаем задачу и для него
        if collaborator_id:
            collaborator_task = create_task(collaborator_id, current_user['telegram_id'])
            db.session.add(collaborator_task)
            new_task_notification(collaborator_id, description, task_date, start_time, end_time, current_user['telegram_id'])
        
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Task added successfully'})

    except ValueError as e:
        print('Ошибка формата данных:', e)
        return jsonify({'error': 'Invalid data format'}), 400
    except Exception as e:
        db.session.rollback()
        print('Ошибка при добавлении задачи:', e)
        return jsonify({'error': 'Server error'}), 500
    finally:
        db.session.close()


@app.route('/tasks-main')
def get_all_tasks():
    if 'user_id' not in session:
        return render_template('index.html')

    user = get_user_by_id(session['user_id'])
    
    # Получаем все задачи пользователя
    tasks = Task.query.filter_by(
        telegram_id=user['telegram_id']
    ).options(
        db.joinedload(Task.collaborator)
    ).all()
    
    result = []
    for task in tasks:
        task_data = {
            'id': task.id,
            'title': task.title,
            'category_filter': task.category_filter,
            'category': task.category,
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None,
            'task_date': task.task_date.isoformat() if task.task_date else None,
            'collaborator_info': None
        }
        
        if task.collaborator:
            task_data['collaborator_info'] = {
                'telegram_username': task.collaborator.telegram_username,
                'first_name': task.collaborator.first_name,
                'last_name': task.collaborator.last_name or '',
                'photo': task.collaborator.photo
            }
        
        result.append(task_data)
    
    return jsonify(result)

@app.route('/tasks')
def get_tasks():
    if 'user_id' not in session:
        return render_template('index.html')

    user = get_user_by_id(session['user_id'])
    date = request.args.get('date')

    print(user['telegram_id'], date)
    
    # Получаем задачи с JOIN к collaborator
    tasks = Task.query.filter_by(
        telegram_id=user['telegram_id'],
        task_date=date
    ).options(
        db.joinedload(Task.collaborator)  # Жадно загружаем связанного collaborator
    ).all()
    
    result = []
    for task in tasks:
        task_data = {
            'id': task.id,
            'title': task.title,
            'category_filter': task.category_filter,
            'category': task.category,
            'start_time': task.start_time.isoformat(),
            'end_time': task.end_time.isoformat(),
            'collaborator_info': None
        }
        
        if task.collaborator:
            task_data['collaborator_info'] = {
                'telegram_username': task.collaborator.telegram_username,
                'first_name': task.collaborator.first_name,
                'last_name': task.collaborator.last_name,
                'photo': task.collaborator.photo
            }
        
        result.append(task_data)
    
    return jsonify(result)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/check_email', methods=['POST'])
def check_email():
    email = request.json.get('email', '')[:100] # Ограничение длины
    
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return jsonify({'status': 'error', 'message': 'Неверный формат email'}), 400
    
    try:
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Генерируем коды
            verification_code = generate_code()
            email_code = email_to_code(email)
            
            # Сохраняем код с временем жизни
            save_temp_code(email, verification_code, role='user', ttl_minutes=3)
            print(verification_code, email)

            # Получаем пользователя из базы по email
            user_from_db = User.query.filter_by(email=email).first()
            confirmation_code(user_from_db.telegram_id, verification_code)
            print(f"{user_from_db.telegram_id}")
            
            
            return jsonify({
                'status': 'confirmation',
                'code': verification_code
            })
        else:
            # Генерируем коды
            verification_code = generate_code()
            email_code = email_to_code(email)
            
            # Сохраняем код с временем жизни
            save_temp_code(email, verification_code, role='user', ttl_minutes=3)
            print(verification_code, email)

            return jsonify({
                'status': 'not_found',
                'code': verification_code,
                'email_code': email_code
            })
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/verify_code', methods=['POST'])
def verify_code():
    try:
        data = request.json
        email = data.get('email')
        code = data.get('code')[:6]

        if not email or not code:
            return jsonify({'success': False, 'error': 'Неверные данные'}), 400

        result = verify_reg_code(email, code)
        print(result)
        if not result['success']:
            return jsonify({'success': False, 'error': result['error']}), 400

        # Проверяем существование пользователя
        user_from_db = User.query.filter_by(email=email).first()
        
        if not user_from_db:
            # Создаем нового пользователя, если не существует
            new_user = create_user_from_temp(email)

            # Создаем запись о входе
            login_record = UserLogin(
                user_id=new_user.id,
                email=new_user.email,
                last_login=datetime.now(MOSCOW_TZ)
            )
            db.session.add(login_record)
            db.session.commit()
            session['user_id'] = new_user.id
        else:
            date = datetime.now(MOSCOW_TZ)
            auth_notification(email, date)
            user_from_db.login_record.last_login = datetime.now(MOSCOW_TZ)
            session['user_id'] = user_from_db.id
            db.session.commit()

        temp = TempCode.query.filter_by(email=email).first()
        if temp:
            db.session.delete(temp)
            db.session.commit()

        return jsonify({'success': True, 'redirect': '/dashboard'})

    except Exception as e:
        db.session.rollback()  # Важно откатить сессию при ошибке
        traceback.print_exc()  # Печать полной ошибки в консоль
        return jsonify({'success': False, 'error': str(e)}), 500

