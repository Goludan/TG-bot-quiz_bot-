from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import types
from quiz_data import quiz_questions

async def generate_question_keyboard(answer_options, correct_answer):
    keyboard_builder = InlineKeyboardBuilder()
    for option in answer_options:
        keyboard_builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data="right_answer" if option == correct_answer else "wrong_answer"
        ))
    keyboard_builder.adjust(1)
    return keyboard_builder.as_markup()

def get_start_keyboard():
    keyboard_builder = ReplyKeyboardBuilder()
    keyboard_builder.add(types.KeyboardButton(text="Начать игру"))
    return keyboard_builder.as_markup(resize_keyboard=True)

def get_restart_keyboard():
    keyboard_builder = ReplyKeyboardBuilder()
    keyboard_builder.add(types.KeyboardButton(text="Начать игру"))
    keyboard_builder.add(types.KeyboardButton(text="Моя статистика"))
    return keyboard_builder.as_markup(resize_keyboard=True)