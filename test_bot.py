import unittest
from unittest.mock import patch, MagicMock
import telebot
from datetime import datetime
import sqlite3
import threading
import pandas as pd

# Импортируем наш бот и необходимые функции
from main import bot, save_user_info, save_message, send_welcome, get_rec, get_similar_rec

# Создаем блокировку для базы данных
db_lock = threading.Lock()

# Подключаемся к базе данных
conn = sqlite3.connect(':memory:', check_same_thread=False)
cursor = conn.cursor()

recipes = pd.read_csv('recipes_data_with_countries.csv', encoding='utf-8')

class TestBot(unittest.TestCase):
    @patch('telebot.TeleBot.send_message')
    @patch('telebot.TeleBot.reply_to')
    def test_send_welcome(self, mock_reply_to, mock_send_message):
        message = MagicMock()
        message.from_user.first_name = 'TestUser'
        message.chat.id = 1
        send_welcome(message)
        
        # Проверяем, что сообщение отправлено
        mock_reply_to.assert_called_with(message, 'Добро пожаловать в бота с вкусными рецептами, <b>TestUser!</b>', parse_mode='html')
        mock_send_message.assert_called_with(message.chat.id, "Введите через запятую Ваши аллергены. Например: семечки, яблоко, капуста. Если их нет, напишите: нет.")

    def test_save_user_info(self):
        user = MagicMock()
        user.id = 1
        user.username = 'testuser'
        user.first_name = 'Test'
        user.last_name = 'User'
        
        save_user_info(user)
        
        with db_lock:
            cursor.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
            result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[1], 'testuser')
        self.assertEqual(result[2], 'Test')
        self.assertEqual(result[3], 'User')

    def test_save_message(self):
        message = MagicMock()
        message.message_id = 1
        message.from_user.id = 1
        message.text = 'Hello, World!'
        
        save_message(message)
        
        with db_lock:
            cursor.execute("SELECT * FROM messages WHERE message_id=?", (message.message_id,))
            result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[2], 'Hello, World!')

    @patch('telebot.TeleBot.send_message')
    def test_get_rec(self, mock_send_message):
        chat_id = 1
        id = 0
        get_rec(chat_id, id)
        
        mock_send_message.assert_called()

    @patch('telebot.TeleBot.send_message')
    def test_get_similar_rec(self, mock_send_message):
        chat_id = 1
        dish = 'Борщ'
        get_similar_rec(chat_id, dish)
        
        mock_send_message.assert_called()

if name == 'main':
    unittest.main()
