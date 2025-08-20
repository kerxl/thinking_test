from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config.const import (
    TaskEntity,
    MESSAGES,
    PRIORITIES_LENGTH_SCORES_PER_QUESTION,
    INQ_SCORES_PER_QUESTION,
    INQ_LENGTH_SCORES_PER_QUESTION,
    PRIORITIES_SCORES_PER_QUESTION,
)

from .globals import task_manager


async def send_priorities_task(message: Message, user_id: int):
    question = TaskEntity.priorities.value.get_question()
    if not question:
        await message.edit_text(MESSAGES["task_not_loaded"])
        return

    state = task_manager.get_task_state(user_id)
    if not state:
        return

    remaining_categories = task_manager.get_priorities_remaining_categories_data(user_id)
    current_step = state["current_step"]
    next_score = (
        PRIORITIES_SCORES_PER_QUESTION[current_step] if current_step < PRIORITIES_LENGTH_SCORES_PER_QUESTION else 1
    )

    text = f"<b>✅Тест 1 из 3: Расстановка приоритетов</b>\n\n"
    text += f"📝 1 / 1\n\n"
    text += f"{question['text']}\n\n"

    for i, item in enumerate(remaining_categories, 1):
        category = item["category_data"]
        text += f"<b>{i}️⃣ {category['title']}</b>\n"
        text += f"{category['description']}\n\n"

    if current_step == 0:
        text += f"<b>Следующий балл: {next_score}</b>\n"
        text += f"<i>Выберите категорию, которой дадите {next_score} баллов:</i>"
    else:
        last_category_title = None
        task_section = state["answers"].get("priorities", {})
        for category_title, score in task_section.items():
            if score == PRIORITIES_SCORES_PER_QUESTION[current_step - 1]:
                last_category_title = category_title
                break

        if last_category_title:
            text += f"✅ Вы дали {PRIORITIES_SCORES_PER_QUESTION[current_step - 1]} баллов категории '{last_category_title}'.\n\n"

        text += f"<b>Следующий балл: {next_score}</b>\n"
        text += f"<i>Выберите категорию, которой дадите {next_score} баллов:</i>"

    keyboard = []
    if remaining_categories:
        keyboard.append(
            [
                InlineKeyboardButton(text=f"{i}️⃣", callback_data=f"priority_new_{i-1}")
                for i in range(1, len(remaining_categories) + 1)
            ]
        )

    if state and state["history"]:
        keyboard.append([InlineKeyboardButton(text=MESSAGES["button_go_back"], callback_data="go_back")])

    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


async def send_inq_question(message: Message, user_id: int, question_num: int):
    question = TaskEntity.inq.value.get_question(question_num)
    if not question:
        await message.edit_text(MESSAGES["task_not_found"])
        return

    state = task_manager.get_task_state(user_id)
    if not state:
        return

    remaining_data = task_manager.get_inq_remaining_options_data(user_id, question_num)
    current_step = state["current_step"]
    next_score = INQ_SCORES_PER_QUESTION[current_step] if current_step < INQ_LENGTH_SCORES_PER_QUESTION else 1

    text = f"<b>✅Тест 2 из 3: Стили мышления</b>\n\n"
    text += f"📝 {question_num + 1} / {TaskEntity.inq.value.get_total_questions()}\n\n"
    text += f"{remaining_data['base_text']}\n\n"

    for i, option_data in enumerate(remaining_data["options"], 1):
        text += f"<b>{i}️⃣ {option_data['text']}</b>\n\n"

    if current_step == 0:
        text += f"<b>Следующий балл: {next_score}</b>\n"
        text += f"<i>Выберите утверждение, которому дашь {next_score} баллов:</i>"
    else:
        last_option_text = None
        task_section = state["answers"].get("inq", {})
        question_key = f"question_{question_num + 1}"
        if question_key in task_section:
            for opt, score in task_section[question_key].items():
                if score == INQ_SCORES_PER_QUESTION[current_step - 1]:
                    full_text = question["text"]
                    for line in full_text.split("\n"):
                        if line.strip().startswith(f"{opt}️⃣"):
                            last_option_text = line.strip().split("️⃣", 1)[1].strip()
                            break
                    break

        if last_option_text:
            text += (
                f"✅ Вы дали {INQ_SCORES_PER_QUESTION[current_step - 1]} баллов утверждению:\n'{last_option_text}'\n\n"
            )

        text += f"<b>Следующий балл: {next_score}</b>\n"
        text += f"<i>Выберите утверждение, которому дашь {next_score} баллов:</i>"

    keyboard = []
    if remaining_data["options"]:
        keyboard.append(
            [
                InlineKeyboardButton(text=f"{i}️⃣", callback_data=f"inq_new_{question_num}_{i-1}")
                for i in range(1, len(remaining_data["options"]) + 1)
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

    text = f"<b>✅Тест 3 из 3: Личностный тест</b>\n\n"
    text += f"📝 {question_num + 1} / {total_questions}\n\n"
    text += f"{question['text']}"

    keyboard = [
        [
            InlineKeyboardButton(text=MESSAGES["button_epi_yes"], callback_data=f"epi_{question_num}_Да"),
            InlineKeyboardButton(text=MESSAGES["button_epi_no"], callback_data=f"epi_{question_num}_Нет"),
        ]
    ]

    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
