# Основная функция
async def main():
    await create_quiz_state_database_table()
    await initialize_results_database_tables()
    await dp.start_polling(telegram_bot)

if __name__ == '__main__':
    asyncio.run(main())