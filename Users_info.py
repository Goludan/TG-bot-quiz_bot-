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