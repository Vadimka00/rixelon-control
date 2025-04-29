# Flask и база данных
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# SQLAlchemy — расширенные инструменты
from sqlalchemy import ForeignKey, CheckConstraint, extract, func, Interval
from sqlalchemy.orm import validates, relationship
from sqlalchemy.ext.hybrid import hybrid_property

# Telegram Bot
from telebot import TeleBot
from threading import Thread

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

# Работа с изображениями
from PIL import Image, ImageDraw, ImageFont

# Веб-запросы
import requests

# Часовые пояса
import pytz


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['BOT_TOKEN'] = os.getenv('BOT_TOKEN')

app.config['SERVER_NAME'] = os.getenv('SERVER_NAME')
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'https'


app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

csrf = CSRFProtect(app)
db = SQLAlchemy(app)
bot = TeleBot(app.config['BOT_TOKEN'])

MOSCOW_TZ = pytz.timezone('Europe/Moscow')
