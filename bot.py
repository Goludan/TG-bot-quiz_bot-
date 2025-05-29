import asyncio
from aiogram import Bot, Dispatcher
from config import TELEGRAM_BOT_TOKEN
from database import create_quiz_state_database_table, initialize_results_database_tables
from handlers import *

telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Регистрация обработчиков
dp.message.register(handle_start_command, Command("start"))
dp.message.register(start_new_quiz, F.text == "Начать игру")
dp.message.register(show_player_statistics, F.text == "Моя статистика")
dp.callback_query.register(handle_correct_answer, F.data == 'right_answer')
dp.callback_query.register(handle_wrong_answer, F.data == 'wrong_answer')

async def main():
    await create_quiz_state_database_table()
    await initialize_results_database_tables()
    await dp.start_polling(telegram_bot)

if __name__ == '__main__':
    asyncio.run(main())