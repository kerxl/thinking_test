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


async def get_retry_callback_data(user_id: int) -> str:
    """Определяет callback_data для кнопки 'Попробовать снова' на основе текущего состояния"""
    task_state = task_manager.get_task_state(user_id)
    if not task_state:
        return "start_tasks"
    
    current_task = task_state["current_task_type"]
    current_question = task_state["current_question"]
    
    if current_task == TaskType.priorities.value:
        return "retry_priorities"
    elif current_task == TaskType.inq.value:
        return f"retry_inq_{current_question}"
    elif current_task == TaskType.epi.value:
        return f"retry_epi_{current_question}"
    else:
        return "start_tasks"


async def send_error_with_retry(callback: CallbackQuery, error_text: str, user_id: int):
    """Отправляет ошибку с кнопкой 'Попробовать снова'"""
    retry_callback_data = await get_retry_callback_data(user_id)
    
    await callback.message.edit_text(
        f"❌ <b>Ошибка:</b>\n{error_text}\n\nПопробуйте еще раз:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=retry_callback_data)]
            ]
        ),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "start_personal_data")
async def collect_personal_data(callback: CallbackQuery, state: FSMContext):
    """
    Установка фамилии имени пользователя
    """
    # Предварительно кэшируем пользователя для будущих операций
    await task_manager.get_cached_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )
    
    await callback.message.edit_text(MESSAGES["callback_start_collect_personal_data"])
    await state.set_state(PersonalDataStates.waiting_for_name)
    await callback.answer()


@dp.callback_query(F.data == "start_tasks")
async def start_tasks(callback: CallbackQuery):
    # Предварительно кэшируем пользователя
    user = await task_manager.get_cached_user(
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

    user = await task_manager.get_cached_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )

    remaining_categories = task_manager.get_priorities_remaining_categories_data(
        user.user_id
    )

    if new_index >= len(remaining_categories):
        await send_error_with_retry(callback, "Неверный выбор категории", user.user_id)
        return

    original_index = remaining_categories[new_index]["original_index"]
    category_title = remaining_categories[new_index]["category_data"]["title"]

    success, message_text = await task_manager.process_priorities_step_answer(
        user, str(original_index)
    )
    if not success:
        await send_error_with_retry(callback, message_text, user.user_id)
        return

    state = task_manager.get_task_state(user.user_id)
    if not state:
        await send_error_with_retry(callback, "Состояние теста не найдено", user.user_id)
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
    # Предварительно кэшируем пользователя для ускорения последующих операций
    await task_manager.get_cached_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )
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

    user = await task_manager.get_cached_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )

    remaining_data = task_manager.get_inq_remaining_options_data(
        user.user_id, question_num
    )

    if new_index >= len(remaining_data["options"]):
        await send_error_with_retry(callback, "Неверный выбор варианта", user.user_id)
        return

    original_option = remaining_data["options"][new_index]["original_option"]

    success, message_text = await task_manager.process_inq_answer(user, original_option)
    if not success:
        await send_error_with_retry(callback, message_text, user.user_id)
        return

    state = task_manager.get_task_state(user.user_id)
    if not state:
        await send_error_with_retry(callback, "Состояние теста не найдено", user.user_id)
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
    user = await task_manager.get_cached_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )

    success, message_text, new_state = await task_manager.go_back_question(user)
    if not success:
        await send_error_with_retry(callback, message_text, user.user_id)
        return

    await callback.answer(MESSAGES["go_back_completed"])

    if new_state["current_task_type"] == TaskType.priorities.value:
        await send_priorities_task(callback.message, user.user_id)
    elif new_state["current_task_type"] == TaskType.inq.value:
        await send_inq_question(
            callback.message, user.user_id, new_state["current_question"]
        )


# Обработчики для кнопки "Попробовать снова"
@dp.callback_query(F.data == "retry_priorities")
async def retry_priorities_task(callback: CallbackQuery):
    """Повторная попытка теста приоритетов"""
    user = await task_manager.get_cached_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )
    await send_priorities_task(callback.message, user.user_id)


@dp.callback_query(F.data.startswith("retry_inq_"))
async def retry_inq_question(callback: CallbackQuery):
    """Повторная попытка INQ вопроса"""
    question_num = int(callback.data.split("_")[2])
    user = await task_manager.get_cached_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )
    await send_inq_question(callback.message, user.user_id, question_num)


@dp.callback_query(F.data.startswith("retry_epi_"))
async def retry_epi_question(callback: CallbackQuery):
    """Повторная попытка EPI вопроса"""
    question_num = int(callback.data.split("_")[2])
    user = await task_manager.get_cached_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )
    await send_epi_question(callback.message, user.user_id, question_num)


@dp.callback_query(F.data == "start_epi_task")
async def start_epi_task(callback: CallbackQuery):
    """
    Начало EPI теста
    """
    # Предварительно кэшируем пользователя для ускорения последующих операций
    await task_manager.get_cached_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )
    await send_epi_question(callback.message, callback.from_user.id, 0)
    await callback.answer()


@dp.callback_query(F.data.startswith("epi_"))
async def process_epi_answer(callback: CallbackQuery):
    """
    Обработка ответов EPI теста
    """
    _, question_num_str, answer = callback.data.split("_")
    question_num = int(question_num_str)

    user = await task_manager.get_cached_user(
        user_id=callback.from_user.id, username=callback.from_user.username
    )

    success, message_text = await task_manager.process_epi_answer(user, answer)
    if not success:
        await send_error_with_retry(callback, message_text, user.user_id)
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
