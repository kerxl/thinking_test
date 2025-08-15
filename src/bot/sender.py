from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config.const import (
    TaskEntity,
    MESSAGES,
    TaskSection,
    AnswerOptions,
    PRIORITIES_LENGTH_SCORES_PER_QUESTION,
    INQ_SCORES_PER_QUESTION,
    INQ_LENGTH_SCORES_PER_QUESTION,
)

from main import task_manager


async def send_priorities_task(message: Message, user_id: int):
    question = TaskEntity.priorities.value.get_question()
    if not question:
        await message.edit_text(MESSAGES["task_not_loaded"])
        return

    text = f"<b>Тест 1✅ из 3: Расстановка приоритетов</b>\n\n"
    text += f"📝 1 / 1\n\n"
    text += f"{question['text']}\n\n"

    for i, category in enumerate(question["categories"], 1):
        text += f"<b>{i}️⃣ {category['title']}</b>\n"
        text += f"{category['description']}\n\n"

    state = task_manager.get_task_state(user_id)
    used_scores = []
    answered_categories = set()
    if state and TaskSection.priorities.value in state["answers"]:
        priorities_answers = state["answers"][TaskSection.priorities.value]
        used_scores = set(priorities_answers.values())
        answered_categories = set(priorities_answers.keys())

    keyboard = []
    for i, category in enumerate(question["categories"]):
        category_id = category["id"]
        title = category["title"]

        # Пропускаем категории, для которых уже выбран балл
        if category_id in answered_categories:
            continue

        score_buttons = []
        for score in AnswerOptions.priorities.value:
            if score not in used_scores:
                score_buttons.append(
                    InlineKeyboardButton(text=f"{score}️⃣", callback_data=f"priority_{category_id}_{score}")
                )

        if score_buttons:
            keyboard.append([InlineKeyboardButton(text=f"{i+1}️⃣ {title}", callback_data="dummy")])
            keyboard.append(score_buttons)

    if len(used_scores) == PRIORITIES_LENGTH_SCORES_PER_QUESTION:
        keyboard.append(
            [InlineKeyboardButton(text=MESSAGES["button_finish_priority_task"], callback_data="complete_priorities")]
        )

    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


async def send_inq_question(message: Message, user_id: int, question_num: int):
    question = TaskEntity.inq.value.get_question(question_num)
    if not question:
        await message.edit_text(MESSAGES["task_not_found"])
        return

    state = task_manager.get_task_state(user_id)
    if not state:
        return

    available_options = task_manager.get_inq_available_options(user_id, question_num)
    current_step = state["current_step"]
    next_score = INQ_SCORES_PER_QUESTION[current_step] if current_step < INQ_LENGTH_SCORES_PER_QUESTION else 1

    text = f"<b>Тест 2✅ из 3: Стили мышления</b>\n\n"
    text += f"📝 {question_num + 1} / {TaskEntity.inq.value.get_total_questions()}\n\n"
    text += f"{question['text']}\n\n"

    if current_step == 0:
        text += f"<b>Следующий балл: {next_score}</b>\n"
        text += f"<i>Выберите утверждение, которому дашь {next_score} баллов:</i>"
    else:
        last_option = None
        task_section = state["answers"].get("inq", {})
        question_key = f"question_{question_num + 1}"
        if question_key in task_section:
            for opt, score in task_section[question_key].items():
                if score == INQ_SCORES_PER_QUESTION[current_step - 1]:
                    last_option = opt
                    break

        if last_option:
            text += f"✅ Вы дали {INQ_SCORES_PER_QUESTION[current_step - 1]} баллов утверждению {last_option}.\n\n"

        text += f"<b>Следующий балл: {next_score}</b>\n"
        text += f"<i>Выберите утверждение, которому дашь {next_score} баллов:</i>"

    keyboard = []
    keyboard.append(
        [
            InlineKeyboardButton(text=f"{option}️⃣", callback_data=f"inq_{question_num}_{option}")
            for option in available_options
        ]
    )

    if state and state["history"]:
        keyboard.append([InlineKeyboardButton(text=MESSAGES["button_go_back"], callback_data="go_back")])

    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


async def send_epi_question(message: Message, user_id: int, question_num: int):
    question = TaskEntity.epi.value.get_question(question_num)
    if not question:
        await message.edit_text(MESSAGES["task_not_found"])
        return

    total_questions = TaskEntity.epi.value.get_total_questions()

    text = f"<b>Тест 3✅ из 3: Личностный тест</b>\n\n"
    text += f"📝 {question_num + 1} / {total_questions}\n\n"
    text += f"{question['text']}"

    keyboard = [
        [
            InlineKeyboardButton(text=MESSAGES["button_epi_yes"], callback_data=f"epi_{question_num}_Да"),
            InlineKeyboardButton(text=MESSAGES["button_epi_no"], callback_data=f"epi_{question_num}_Нет"),
        ]
    ]

    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
