from aiogram import types, F
from aiogram.filters.command import Command
from database import *
from keyboards import *
from quiz_data import quiz_questions

# Хранилище для подсчета правильных ответов
user_scores_storage = {}

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

async def handle_start_command(message: types.Message):
    await message.answer(
        "Добро пожаловать в викторину по Python!", 
        reply_markup=get_start_keyboard()
    )

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
        
        await callback_query.message.answer(
            result_message, 
            reply_markup=get_restart_keyboard()
        )

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
        
        await callback_query.message.answer(
            result_message, 
            reply_markup=get_restart_keyboard()
        )

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