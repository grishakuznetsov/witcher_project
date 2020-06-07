import telebot
import requests
import random
import sqlite3
import os
import markovify
import conf
telebot.apihelper.proxy = conf.PROXY
bot = telebot.TeleBot(conf.TOKEN)


'''
Создаем базу данных и берем данные для отправления картинок и склеиваем тексты для обучения цепи Маркова
'''

content = ''
path = './books'
imgpath = './img'

images = os.listdir(imgpath)


for i in os.listdir(path):
    new_path = os.path.join(path, i)
    with open(new_path, 'r', encoding='utf-8') as f:
        content += f.read()
with open('withcer_all.txt', 'w', encoding='utf-8') as f:
    f.write(content)


''' Обучаем цепь Маркова'''


model = markovify.Text(content)


conn = sqlite3.connect('witcher_stories.db')
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
telegram_id INT, 
username	TEXT,
first_name	TEXT,
last_name	TEXT
);""")

cur.execute("""
CREATE TABLE IF NOT EXISTS stories (
id	INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
user_id INTEGER NOT NULL, 
length	TEXT,
story	TEXT,
FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);""")
conn.commit()
conn.close()


'''Клавиатуры для бота'''


keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard1.add('Длинная', 'Короткая')


keyboard2 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard2.add('Да, послушаю', 'Нет, спасибо')


keyboard3 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard3.add('<вернуться>')


'''Код бота. При старте заносит информацию о пользователе в базу данных, имя, фамилию, username и id'''


@bot.message_handler(commands=['start'])
def start(message):
    to_users = []
    to_users.append(message.from_user.id)
    to_users.append(message.from_user.username)
    to_users.append(message.from_user.first_name)
    to_users.append(message.from_user.last_name)
    conn = sqlite3.connect('witcher_stories.db')
    cur = conn.cursor()  # Заносим в базу данных
    cur.execute('INSERT INTO users (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)', to_users)
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, 'Хочешь послушать одну из моих историй? Какую ты хочешь?', reply_markup=keyboard1)


@bot.message_handler(content_types=['text'])  # Основная функция, по текстам и кнопок выбираем, какую историю рассказать
def text(message):
    if message.text == 'Длинная':
        bot.send_message(message.chat.id, 'Вспомнил одну...')
        story = ''
        for s in range(random.randint(10, 15)):    # Гененрируем историю, длинной в рандмное количество предложений от
            story += model.make_sentence() + '\n'  # 10 до 15 (длинная), отправляем пользователю вместе с картинкой
        bot.send_message(message.chat.id, story)
        bot.send_photo(message.chat.id, photo=open('./img/' + random.choice(images), 'rb'))
        conn = sqlite3.connect('witcher_stories.db')
        cur = conn.cursor()
        to_stories = []
        to_stories.append(message.from_user.id)  # Заносим информацию о истории и берем ID telegram для связи таблиц
        to_stories.append(message.text)          # в базе данных
        to_stories.append(story)
        cur.execute('INSERT INTO stories (user_id, length, story) VALUES (?, ?, ?)', to_stories)
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, 'Ну что, еще одну?', reply_markup=keyboard2)
    elif message.text == 'Короткая':   # То же самое для короткой (от 4 до 8 предложений) истории
        bot.send_message(message.chat.id, 'Вспомнил одну...')
        story = ''
        for s in range(random.randint(4, 8)):
            story += model.make_sentence() + '\n'
        bot.send_message(message.chat.id, story)
        bot.send_photo(message.chat.id, photo=open('./img/' + random.choice(images), 'rb'))
        to_stories = []
        to_stories.append(message.from_user.id)
        to_stories.append(message.text)
        to_stories.append(story)
        conn = sqlite3.connect('witcher_stories.db')
        cur = conn.cursor()
        cur.execute('INSERT INTO stories (user_id, length, story) VALUES (?, ?, ?)', to_stories)
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, 'Ну что, еще одну?', reply_markup=keyboard2)  # Клавиатура для новой истории
    elif message.text == 'Да, послушаю':
        bot.send_message(message.chat.id, 'Хорошо, какую в этот раз?', reply_markup=keyboard1)
    elif message.text == 'Нет, спасибо':
        bot.send_message(message.chat.id, 'Удачи', reply_markup=keyboard3)
    elif message.text == '<вернуться>':  # Возврат в корчму
        bot.send_message(message.chat.id, 'Хочешь послушать одну из моих историй? Какую ты хочешь?',
                         reply_markup=keyboard1)
    elif not message.text.isalpha():
        bot.send_message(message.chat.id, 'Я тебя не понимаю', reply_markup=keyboard1)  # Проверка на плохие инпуты
    else:
        roll = random.randint(1, 10)
        if roll <= 5:
            answer = model.make_sentence()
            bot.send_message(message.chat.id, answer, reply_markup=keyboard1)
        else:
            bot.send_message(message.chat.id, 'Я не в настроении болтать', reply_markup=keyboard1)


bot.polling()
