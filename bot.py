from datetime import datetime
from core import app, db, bot, MOSCOW_TZ
from models import User, TempCode  # Модели для User и TempCode
from utils import create_profile_image, get_email_by_email_code, get_user_by_telegram_id  # Функции, которые могут быть использованы в коде
import requests
import time

from core import app, db, bot, MOSCOW_TZ

# Обработчик Telegram бота
@bot.message_handler(commands=['start'])
def handle_start(message):
    with app.app_context():  # Добавляем контекст приложения
        user = message.from_user
        telegram_id = user.id
        telegram_username = user.username if user.username else None
        first_name = user.first_name if user.first_name else None
        last_name = user.last_name if user.last_name else None

        try:

            if 'AUTH=' not in message.text:
                bot.reply_to(message, "Для регистрации используйте ссылку с сайта")
                return

            email_code = message.text.split('AUTH=')[1].strip()
            
            # Поиск email по коду
            email = get_email_by_email_code(email_code)
            
            if not email:
                bot.reply_to(message, "❌ Недействительная ссылка")
                return
            
            user_from_db = User.query.filter_by(telegram_id=telegram_id).first()
            
            # Добавляем проверку на существование пользователя
            if user_from_db:
                bot.reply_to(message, "❌ Вы уже зарегистрированы по другим данным")
                return
                
            code_data = TempCode.query.filter_by(email=email).first()
            if not code_data or code_data.is_expired():
                bot.reply_to(message, "⌛ Время действия кода истекло")
                if code_data:
                    db.session.delete(code_data)
                    db.session.commit()
                return

            profile_photo_url = create_profile_image(first_name, last_name, telegram_id)

            bot.send_message(
                message.chat.id,
                f"🔑 Ваш код подтверждения: <code>{code_data.code}</code>\n",
                parse_mode='HTML'
            )

            temp = code_data
            if temp:
                temp.telegram_id = telegram_id
                temp.telegram_username = telegram_username
                temp.first_name = first_name
                temp.last_name = last_name
                temp.photo = profile_photo_url
                db.session.commit()

            else:
                print(f"Запись для {email} не найдена")

        except Exception as e:
            print(f"Ошибка бота: {str(e)}")
            bot.reply_to(message, "⚠️ Ошибка обработки запроса")

def confirmation_code(user_id, verification_code):
    try:
        bot.send_message(
            user_id,
            f"🔑 Ваш код подтверждения: <code>{verification_code}</code>\n",
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка бота: {str(e)}")

def get_email_user(email):
    user = User.query.filter_by(email=email).first()
    return user.telegram_id if user else None

def auth_notification(email, date):
    user_id = get_email_user(email)
    try:
        # Форматируем дату в строку с указанием часового пояса
        formatted_date = date.strftime("%d/%m/%Y %H:%M") + " (МСК)"
        
        bot.send_message(
            user_id,
            f"В ваш аккаунт был выполнен вход: <b>{formatted_date}</b>\n",
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка бота: {str(e)}")

def friends_notification(to_telegram_id, title, message, from_telegram_id):
    try:
        text = f"<b>{title}</b>\n\n{message}"

        bot.send_message(
            to_telegram_id,
            text,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка бота: {str(e)}")

def new_task_notification(to_telegram_id, title, task_date, start_time, end_time, from_telegram_id):
    try:
        from_user = get_user_by_telegram_id(from_telegram_id)
        first_name = from_user['first_name']
        last_name = from_user['last_name']
        full_name = f"{first_name} {last_name}" if last_name else first_name

        def format_time(t):
            try:
                return datetime.strptime(str(t), "%H:%M:%S").strftime("%H:%M")
            except:
                try:
                    return datetime.strptime(str(t), "%H:%M").strftime("%H:%M")
                except:
                    return str(t)

        def format_date(d):
            try:
                return datetime.strptime(str(d), "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                return str(d)

        print(start_time)
        print(end_time)
        print(task_date)

        start_time_str = format_time(start_time)
        end_time_str = format_time(end_time)
        task_date_str = format_date(task_date)

        telegram_name = f'<a href="tg://user?id={from_user["telegram_id"]}">{full_name}</a>'
        text = (
            f"<b>Совместная задача с {telegram_name}!</b>\n\n"
            f"<b>Описание:</b> {title}\n\n"
            f"<b>Время:</b> {start_time_str} - {end_time_str}\n"
            f"<b>Дата:</b> {task_date_str}"
        )

        bot.send_message(
            chat_id=to_telegram_id,
            text=text,
            parse_mode='HTML'
        )

    except Exception as e:
        print(f"Ошибка при отправке уведомления: {str(e)}")


def run_bot():
    while True:
        try:
            print("Запуск бота...")
            bot.polling(none_stop=True, timeout=30)  # Увеличьте таймаут
        except requests.exceptions.ConnectTimeout as e:
            print(f"Ошибка подключения: {e}. Повтор через 10 секунд...")
            time.sleep(10)
        except Exception as e:
            print(f"Неизвестная ошибка: {e}. Перезапуск...")
            time.sleep(10)