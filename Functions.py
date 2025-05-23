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

