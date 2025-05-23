import logging
import aiosqlite
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
import datetime

logging.basicConfig(level=logging.INFO)

# Токен Telegram бота
TELEGRAM_BOT_TOKEN = ''

telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

QUIZ_DATABASE_FILE = 'quiz_bot.db'
RESULTS_DATABASE_FILE = 'quiz_results.db'

# Вопросы для квиза
quiz_questions = [
    {
        'question': 'Что такое Python?',
        'options': ['Язык программирования', 'Тип данных', 'Музыкальный инструмент', 'Змея на английском'],
        'correct_option': 0
    },
    {
        'question': 'Какой тип данных используется для хранения целых чисел?',
        'options': ['int', 'float', 'str', 'object'],
        'correct_option': 0
    },
    {
        'question': 'Какое название носит цикл, вызывающий сам себя, в Python?',
        'options': ['Инфинит', 'Закольцованный', 'Рекурсивный', 'Абстрактный'],
        'correct_option': 2
    },
    {
        'question': 'Какое название носят значения true и false?',
        'options': ['Трикстерные', 'Булевы', 'Бабулевы', 'Объектные'],
        'correct_option': 1
    },
    {
        'question': 'Какой тип данных используется для хранения чисел с плавающей точкой?',
        'options': ['int', 'float', 'str', 'object'],
        'correct_option': 1
    },
    {
        'question': 'С помощью какой команды задаются функции в Python?',
        'options': ['fid', 'if', 'while', 'def'],
        'correct_option': 3
    },
    {
        'question': 'Какая команда используется для запроса данных от пользователя?',
        'options': ['print', 'while', 'qst', 'input'],
        'correct_option': 3
    },
    {
        'question': 'Что означает аббревиатура ML?',
        'options': ['Machine learning', 'Mythic laugh', 'Mamin Largus', 'Martin Lawrence'],
        'correct_option': 0
    },
    {
        'question': 'Какая команда используется для вывода данных?',
        'options': ['stay', 'print', 'paint', 'draw'],
        'correct_option': 1
    },
    {
        'question': 'Мальчика как звали, выжил который?',
        'options': ['Гарри Поттер', 'Северус Снег', 'Бред Питт', 'Йода, ты спалился'],
        'correct_option': 3
    },
]

# Хранилище для подсчета правильных ответов
user_scores_storage = {}

# Создание таблицы для хранения состояния квиза пользователей
async def create_quiz_state_database_table():    
    async with aiosqlite.connect(QUIZ_DATABASE_FILE) as database_connection:
        await database_connection.execute('''CREATE TABLE IF NOT EXISTS quiz_state 
                                         (user_id INTEGER PRIMARY KEY, question_index INTEGER)''')
        await database_connection.commit()

# Получение текущего индекса вопроса для указанного пользователя
async def get_current_question_index_for_user(user_id):
    async with aiosqlite.connect(QUIZ_DATABASE_FILE) as database_connection:
        async with database_connection.execute('SELECT question_index FROM quiz_state WHERE user_id = ?', 
                                             (user_id,)) as database_cursor:
            result = await database_cursor.fetchone()
            return result[0] if result else 0

# Обновление индекса текущего вопроса для пользователя
async def update_question_index_for_user(user_id, new_index):
    async with aiosqlite.connect(QUIZ_DATABASE_FILE) as database_connection:
        await database_connection.execute('''INSERT OR REPLACE INTO quiz_state 
                                         (user_id, question_index) VALUES (?, ?)''', 
                                         (user_id, new_index))
        await database_connection.commit()

# Сохранение информации об игроке в базу данных
async def save_player_information(player_id, username, first_name, last_name):
    async with aiosqlite.connect(RESULTS_DATABASE_FILE) as database_connection:
        await database_connection.execute('''INSERT OR IGNORE INTO players 
                                         (player_id, username, first_name, last_name) 
                                         VALUES (?, ?, ?, ?)''',
                                         (player_id, username, first_name, last_name))
        await database_connection.commit()

# Сохранение результата прохождения квиза
async def save_quiz_result(player_id, score):
    async with aiosqlite.connect(RESULTS_DATABASE_FILE) as database_connection:
        await database_connection.execute('''INSERT INTO quiz_results 
                                         (player_id, quiz_name, score) 
                                         VALUES (?, ?, ?)''',
                                         (player_id, "Python Quiz", score))
        await database_connection.commit()

# Получение последнего результата квиза для пользователя
async def get_last_quiz_result_for_user(user_id):
    async with aiosqlite.connect(RESULTS_DATABASE_FILE) as database_connection:
        async with database_connection.execute('''SELECT score, timestamp FROM quiz_results 
                                               WHERE player_id = ? 
                                               ORDER BY timestamp DESC LIMIT 1''',
                                            (user_id,)) as database_cursor:
            return await database_cursor.fetchone()

# Возвращение статистики игрока
async def get_player_statistics(user_id):
    async with aiosqlite.connect(RESULTS_DATABASE_FILE) as database_connection:
        async with database_connection.execute('''SELECT COUNT(*), AVG(score), MAX(score) 
                                               FROM quiz_results WHERE player_id = ?''',
                                            (user_id,)) as database_cursor:
            return await database_cursor.fetchone()

# Инициализация таблицы в базе данных результатов
async def initialize_results_database_tables():
    async with aiosqlite.connect(RESULTS_DATABASE_FILE) as database_connection:
        await database_connection.execute('''CREATE TABLE IF NOT EXISTS players(
            player_id INTEGER PRIMARY KEY, 
            username TEXT, 
            first_name TEXT, 
            last_name TEXT
        )''')
        await database_connection.execute('''CREATE TABLE IF NOT EXISTS quiz_results(
            result_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            player_id INTEGER, 
            quiz_name TEXT, 
            score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
            FOREIGN KEY (player_id) REFERENCES players(player_id)
        )''')
        await database_connection.commit()

# Генерация клавиатуры с вариантами ответов
async def generate_question_keyboard(answer_options, correct_answer):
    keyboard_builder = InlineKeyboardBuilder()
    for option in answer_options:
        keyboard_builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == correct_answer else "wrong_answer"
        ))
    keyboard_builder.adjust(1)
    return keyboard_builder.as_markup()

# Вопрос пользователю
async def send_question_to_user(message, user_id):
    current_question_index = await get_current_question_index_for_user(user_id)
    question_data = quiz_questions[current_question_index]
    correct_option_index = question_data['correct_option']
    answer_options = question_data['options']
    
    question_keyboard = await generate_question_keyboard(
        answer_options, 
        answer_options[correct_option_index]
    )
    await message.answer(question_data['question'], reply_markup=question_keyboard)

# Обработчик команды /start
@dp.message(Command("start"))
async def handle_start_command(message: types.Message):
    keyboard_builder = ReplyKeyboardBuilder()
    keyboard_builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer(
        "Добро пожаловать в викторину по Python!", 
        reply_markup=keyboard_builder.as_markup(resize_keyboard=True)
    )

# Начинаем новый квиз
@dp.message(F.text == "Начать игру")
async def start_new_quiz(message: types.Message):
    user_id = message.from_user.id
    await save_player_information(
        user_id, 
        message.from_user.username, 
        message.from_user.first_name, 
        message.from_user.last_name
    )
    await update_question_index_for_user(user_id, 0)
    user_scores_storage[user_id] = 0
    await send_question_to_user(message, user_id)

# Обработка правильного ответа
@dp.callback_query(F.data == 'right_answer')
async def handle_correct_answer(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_scores_storage[user_id] = user_scores_storage.get(user_id, 0) + 1
    
    await callback_query.bot.edit_message_reply_markup(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    await callback_query.message.answer('Правильно!')
    
    current_question_index = await get_current_question_index_for_user(user_id)
    current_question_index += 1
    await update_question_index_for_user(user_id, current_question_index)

    if current_question_index < len(quiz_questions):
        await send_question_to_user(callback_query.message, user_id)
    else:
        final_score = user_scores_storage.get(user_id, 0)
        await save_quiz_result(user_id, final_score)
        del user_scores_storage[user_id]
        
        player_stats = await get_player_statistics(user_id)
        last_quiz_result = await get_last_quiz_result_for_user(user_id)
        
        result_message = (
            f"Викторина завершена!\n"
            f"Ваш результат: {final_score} из {len(quiz_questions)}\n"
            f"Последний результат: {last_quiz_result[0] if last_quiz_result else 'нет данных'}\n"
            f"Всего попыток: {player_stats[0] if player_stats else 0}\n"
            f"Средний балл: {round(player_stats[1], 1) if player_stats and player_stats[1] else 'нет данных'}\n"
            f"Лучший результат: {player_stats[2] if player_stats and player_stats[2] else 'нет данных'}"
        )
        
        keyboard_builder = ReplyKeyboardBuilder()
        keyboard_builder.add(types.KeyboardButton(text="Начать игру"))
        keyboard_builder.add(types.KeyboardButton(text="Моя статистика"))
        
        await callback_query.message.answer(
            result_message, 
            reply_markup=keyboard_builder.as_markup(resize_keyboard=True)
        )

# Обработка неправильного ответа
@dp.callback_query(F.data == 'wrong_answer')
async def handle_wrong_answer(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    current_question_index = await get_current_question_index_for_user(user_id)
    correct_option_index = quiz_questions[current_question_index]['correct_option']
    
    await callback_query.bot.edit_message_reply_markup(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )
    
    await callback_query.message.answer(
        f"Неправильно! Правильный ответ: {quiz_questions[current_question_index]['options'][correct_option_index]}"
    )
    
    current_question_index += 1
    await update_question_index_for_user(user_id, current_question_index)

    if current_question_index < len(quiz_questions):
        await send_question_to_user(callback_query.message, user_id)
    else:
        final_score = user_scores_storage.get(user_id, 0)
        await save_quiz_result(user_id, final_score)
        del user_scores_storage[user_id]
        
        player_stats = await get_player_statistics(user_id)
        last_quiz_result = await get_last_quiz_result_for_user(user_id)
        
        result_message = (
            f"Квиз завершен!\n"
            f"Ваш результат: {final_score} из {len(quiz_questions)}\n"
            f"Последний результат: {last_quiz_result[0] if last_quiz_result else 'нет данных'}\n"
            f"Всего попыток: {player_stats[0] if player_stats else 0}\n"
            f"Средний балл: {round(player_stats[1], 1) if player_stats and player_stats[1] else 'нет данных'}\n"
            f"Лучший результат: {player_stats[2] if player_stats and player_stats[2] else 'нет данных'}"
        )
        
        keyboard_builder = ReplyKeyboardBuilder()
        keyboard_builder.add(types.KeyboardButton(text="Начать игру"))
        keyboard_builder.add(types.KeyboardButton(text="Моя статистика"))
        
        await callback_query.message.answer(
            result_message, 
            reply_markup=keyboard_builder.as_markup(resize_keyboard=True)
        )

# Вывод статистики игрока
@dp.message(F.text == "Моя статистика")
async def show_player_statistics(message: types.Message):
    user_id = message.from_user.id
    player_stats = await get_player_statistics(user_id)
    last_quiz_result = await get_last_quiz_result_for_user(user_id)
    
    if not player_stats or player_stats[0] == 0:
        await message.answer("У вас еще нет результатов.")
        return
    
    statistics_message = (
        f"Ваша статистика:\n"
        f"Последний результат: {last_quiz_result[0] if last_quiz_result else 'нет данных'}\n"
        f"Всего попыток: {player_stats[0]}\n"
        f"Средний балл: {round(player_stats[1], 1)}\n"
        f"Лучший результат: {player_stats[2]}"
    )
    
    await message.answer(statistics_message)

# Основная функция
async def main():
    await create_quiz_state_database_table()
    await initialize_results_database_tables()
    await dp.start_polling(telegram_bot)

if __name__ == '__main__':
    asyncio.run(main())