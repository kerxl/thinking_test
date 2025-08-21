from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from .globals import task_manager, dp
from config.const import (
    MESSAGES,
    PersonalDataStates,
    AdminStates,
    INQ_SCORES_PER_QUESTION,
    TaskEntity,
    TaskType,
    PRIORITIES_SCORES_PER_QUESTION,
)
from .complete import complete_all_tasks
from .sender import send_priorities_task, send_inq_question, send_epi_question
from src.database.operations import get_or_create_user


@dp.callback_query(F.data == "start_personal_data")
async def collect_personal_data(callback: CallbackQuery, state: FSMContext):
    """
    Установка фамилии имени пользователя
    """
    await callback.message.edit_text(MESSAGES["callback_start_collect_personal_data"])
    await state.set_state(PersonalDataStates.waiting_for_name)
    await callback.answer()


@dp.callback_query(F.data == "start_tasks")
async def start_tasks(callback: CallbackQuery):
    user = await get_or_create_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )

    success = await task_manager.start_tasks(user)
    if not success:
        await callback.message.edit_text(MESSAGES["task_not_loaded"])
        return

    await send_priorities_task(callback.message, user.user_id)
    await callback.answer()


@dp.callback_query(F.data.startswith("priority_new_"))
async def process_priorities_answer(callback: CallbackQuery):
    """
    Обработка ответов на тест приоритетов
    """
    _, _, new_index_str = callback.data.split("_")
    new_index = int(new_index_str)

    user = await get_or_create_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )

    remaining_categories = task_manager.get_priorities_remaining_categories_data(
        user.user_id
    )

    if new_index >= len(remaining_categories):
        await callback.answer("❌ Неверный выбор категории", show_alert=True)
        return

    original_index = remaining_categories[new_index]["original_index"]
    category_title = remaining_categories[new_index]["category_data"]["title"]

    success, message_text = await task_manager.process_priorities_step_answer(
        user, str(original_index)
    )
    if not success:
        await callback.answer(f"❌ {message_text}", show_alert=True)
        return

    state = task_manager.get_task_state(user.user_id)
    if not state:
        await callback.answer(MESSAGES["task_incorrect"], show_alert=True)
        return

    score = PRIORITIES_SCORES_PER_QUESTION[state["current_step"] - 1]
    await callback.answer(f"✅ '{category_title}' получила {score} баллов")

    if task_manager.is_priorities_task_completed(user.user_id):
        await callback.message.edit_text(
            "🎉 <b>Тест 1 завершен!✅</b>\n\n" "Переходим к следующему тесту...",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=MESSAGES["button_inq_task_start"],
                            callback_data="start_inq_task",
                        )
                    ]
                ]
            ),
        )
        await task_manager.move_to_next_task(user.user_id)
    else:
        await send_priorities_task(callback.message, user.user_id)


@dp.callback_query(F.data == "start_inq_task")
async def start_inq_task(callback: CallbackQuery):
    """
    Начало INQ теста
    """
    await send_inq_question(callback.message, callback.from_user.id, 0)
    await callback.answer()


@dp.callback_query(F.data.startswith("inq_new_"))
async def process_inq_answer(callback: CallbackQuery):
    """
    Обработка ответов INQ теста
    """
    parts = callback.data.split("_")
    question_num = int(parts[2])
    new_index = int(parts[3])

    user = await get_or_create_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )

    remaining_data = task_manager.get_inq_remaining_options_data(
        user.user_id, question_num
    )

    if new_index >= len(remaining_data["options"]):
        await callback.answer("❌ Неверный выбор варианта", show_alert=True)
        return

    original_option = remaining_data["options"][new_index]["original_option"]

    success, message_text = await task_manager.process_inq_answer(user, original_option)
    if not success:
        await callback.answer(f"❌ {message_text}", show_alert=True)
        return

    state = task_manager.get_task_state(user.user_id)
    if not state:
        await callback.answer(MESSAGES["task_incorrect"], show_alert=True)
        return

    score = INQ_SCORES_PER_QUESTION[state["current_step"] - 1]
    await callback.answer(f"✅ Вариант получил {score} баллов")

    if task_manager.is_inq_question_completed(user.user_id, question_num):
        if question_num + 1 < TaskEntity.inq.value.get_total_questions():
            await task_manager.move_to_next_question(user.user_id)
            await send_inq_question(callback.message, user.user_id, question_num + 1)
        else:
            await task_manager.move_to_next_task(user.user_id)
            await callback.message.edit_text(
                "🎉 <b>Тест 2 завершен!✅</b>\n\n" "Переходим к финальному тесту...",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=MESSAGES["button_epi_task_start"],
                                callback_data="start_epi_task",
                            )
                        ]
                    ]
                ),
            )
    else:
        await send_inq_question(callback.message, user.user_id, question_num)


@dp.callback_query(F.data == "go_back")
async def go_back(callback: CallbackQuery):
    """
    Обработка кнопки "Назад"
    """
    user = await get_or_create_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )

    success, message_text, new_state = await task_manager.go_back_question(user)
    if not success:
        await callback.answer(f"❌ {message_text}", show_alert=True)
        return

    await callback.answer(MESSAGES["go_back_completed"])

    if new_state["current_task_type"] == TaskType.priorities.value:
        await send_priorities_task(callback.message, user.user_id)
    elif new_state["current_task_type"] == TaskType.inq.value:
        await send_inq_question(
            callback.message, user.user_id, new_state["current_question"]
        )


@dp.callback_query(F.data == "start_epi_task")
async def start_epi_task(callback: CallbackQuery):
    """
    Начало EPI теста
    """
    await send_epi_question(callback.message, callback.from_user.id, 0)
    await callback.answer()


@dp.callback_query(F.data.startswith("epi_"))
async def process_epi_answer(callback: CallbackQuery):
    """
    Обработка ответов EPI теста
    """
    _, question_num_str, answer = callback.data.split("_")
    question_num = int(question_num_str)

    user = await get_or_create_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )

    success, message_text = await task_manager.process_epi_answer(user, answer)
    if not success:
        await callback.answer(f"❌ {message_text}", show_alert=True)
        return

    await callback.answer(f"✅ Ответ: {answer}")

    if question_num + 1 < TaskEntity.epi.value.get_total_questions():
        await send_epi_question(callback.message, user.user_id, question_num + 1)
    else:
        await complete_all_tasks(callback.message, user)


@dp.callback_query(F.data.startswith("add_senler_link_"))
async def add_senler_link_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработка нажатия кнопки для добавления ссылки Senler администратором
    """
    # Проверяем, что это админ
    from config.settings import ADMIN_USER_ID

    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer(
            "❌ У вас нет прав для выполнения этого действия", show_alert=True
        )
        return

    # Извлекаем user_id из callback_data
    user_id = int(callback.data.split("_")[-1])

    # Сохраняем user_id в состояние для дальнейшего использования
    await state.update_data(target_user_id=user_id)

    # Устанавливаем состояние ожидания ссылки
    await state.set_state(AdminStates.waiting_for_senler_link)

    # Просим админа ввести ссылку
    await callback.message.reply(
        f"📝 Введите ссылку на Senler для пользователя {user_id}:\n\n"
        "Ссылка будет отправлена пользователю через 24 часа."
    )

    await callback.answer("✅ Ожидаю ввод ссылки")
