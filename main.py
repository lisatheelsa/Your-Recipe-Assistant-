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
                                      "капуста. Если их нет, напишите: нет.")

def get_rec(chat_id, id):
    bot.send_message(chat_id,
                     f"<b>Кухня:</b> {recipes.iloc[id, 0]}\n"
                     f"\n<b>Название блюда:</b> {recipes.iloc[id, 1]}\n"
                     f"\n<b>Ингредиенты:</b> {recipes.iloc[id, 2]}\n"
                     f"\n<b>Время готовки:</b> {recipes.iloc[id, 3]}\n"
                     f"\n<b>Калории:</b> {recipes.iloc[id, 4]}\n"
                     f"\n<b>и сам рецепт)):</b> {recipes.iloc[id, 5]}", parse_mode='html'
                     )

def get_similar_rec(chat_id, dish):
    vectorizer = TfidfVectorizer()

    # Преобразуйте текстовые данные в матрицу TF-IDF
    tfidf_matrix = vectorizer.fit_transform(recipes['Название блюда'])

    # Преобразуйте введенное слово в вектор TF-IDF
    word_vector = vectorizer.transform([dish])

    # Вычислите косинусное сходство между вектором введенного слова и всеми векторами блюд
    cosine_similarities = cosine_similarity(word_vector, tfidf_matrix).flatten()

    # Найдите индексы блюд с косинусным сходством на 50% и больше
    similar_indices = [i for i, similarity in enumerate(cosine_similarities) if similarity >= 0.5]
    final_similarity_indices = []

    for index in similar_indices:
        flag = True
        for recipe in recipes.iloc[index, 2]:
            if recipe not in all_allergens:
                flag = False
        if flag:
            final_similarity_indices.append(index)

# Выведите названия блюд со сходством на 50% и больше
    bot.send_message(chat_id, f"По вашему запросу было найдено {len(final_similarity_indices)} блюд:")
    for index in final_similarity_indices:
        get_rec(chat_id, index)


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    # сохранение всех сообщений
    message_lower = message.text.lower()
    save_message(message)
    # bot.send_sticker(message.chat.id, "CAACAgIAAxkBAAELxNVl_I_YzLIlvZcNl5jT_M7iEUvBigACVhMAAvNbAUhsonT0E7AAAeQ0BA")

    if message_lower in 'рандом':
        random_rec = random.randint(0, len(recipes) - 1)
        get_rec(message.chat.id, random_rec)
        bot.send_message(message.chat.id, "Для нового случайного рецепта напиши слово  <b>рандом</b>\n\n"
                                          "Для поиска блюда напиши 'хочу Название блюда'", parse_mode='html')
    elif 'хочу' in message_lower.split():
        dish = re.search(r'хочу\s+(.+)', message.text).group(1)
        get_similar_rec(message.chat.id, dish)
        bot.send_message(message.chat.id, "Для нового случайного рецепта напиши слово  <b>рандом</b>\n\n"
                                          "Для поиска блюда напиши 'хочу Название блюда'", parse_mode='html')
    else:
        # сохранение аллергенов в бдшку
        allergens = message.text
        if allergens.lower() == 'нет':
            bot.send_message(message.chat.id, 'У вас нет аллергенов')

        all_allergens = allergens.split(',')
        bot.send_message(message.chat.id,
                         f"Ваши аллергены {allergens.split(',')} были сохранены. Если хотите их изменить, "
                         f"просто напиши их заново")

        with db_lock:
            cursor.execute("UPDATE users SET allergen = ? WHERE user_id = ?", (allergens, message.from_user.id))
            conn.commit()

        # после аллергенов челику можно рекомендовать то что он хочет
        bot.send_message(message.chat.id,
                         "Теперь ты можешь выбрать что будешь кушать\n\n"
                         "Для случайного рецепта напишите слово <b>рандом</b>\n\n"
                         "Для поиска блюда напиши 'хочу Название блюда' (в именительном падеже,"
                         "единственном числе)", parse_mode='html')


bot.infinity_polling()
