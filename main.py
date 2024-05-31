import telebot
from telebot import types
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
import pandas as pd
import sqlite3
from datetime import datetime
import threading
import re

recipes = pd.read_csv('recipes_data_with_countries.csv', encoding='utf-8')
bot = telebot.TeleBot('6320105809:AAEZF_4m9JyvvnkAdmCvrJP83jgQhxk-32w')
first_random = 0
all_allergens = []

# Создаем блокировку для базы данных
db_lock = threading.Lock()

# Подключаемся к базе данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу для хранения информации о пользователях, если её нет
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, joined_at TEXT, allergen TEXT)''')


# Функция для сохранения информации о пользователе
def save_user_info(user):
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    joined_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db_lock:
        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, joined_at, allergen) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, first_name, last_name, joined_at, None))
        conn.commit()


# бдшка для сохранения сообщений (шпионская)
cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                  (message_id INTEGER PRIMARY KEY, user_id INTEGER, message_text TEXT, sent_at TEXT)''')


def save_message(message):
    message_id = message.message_id
    user_id = message.from_user.id
    message_text = message.text
    sent_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with db_lock:
        cursor.execute("INSERT INTO messages (message_id, user_id, message_text, sent_at) VALUES (?, ?, ?, ?)",
                       (message_id, user_id, message_text, sent_at))
        conn.commit()


@bot.message_handler(commands=['start'])
def send_welcome(message, rerun=0):
    save_user_info(message.from_user)
    if rerun == 0:
        bot.reply_to(message, f"Добро пожаловать в бота с вкусными рецептами, <b>{message.from_user.first_name}!</b>",
                     parse_mode='html')

    bot.send_message(message.chat.id, "Введите через запятую Ваши аллергены. Например: семечки, яблоко, "
                                      "капуста")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    # сохранение всех сообщений
    message_lower = message.text.lower()
    save_message(message)
    # bot.send_sticker(message.chat.id, "CAACAgIAAxkBAAELxNVl_I_YzLIlvZcNl5jT_M7iEUvBigACVhMAAvNbAUhsonT0E7AAAeQ0BA")



bot.infinity_polling()