from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from main import task_manager
from config.const import MESSAGES
from src.core.admin_reports import admin_reports
from src.database.operations import get_or_create_user


async def complete_all_tasks(message: Message, user):
    """
    Завершение всего тестирования
    """
    all_scores = await task_manager.complete_all_tasks(user)

    if not all_scores:
        await message.edit_text(MESSAGES["summary_result_error"])
        return

    result_text = "🎉 <b>Все тесты завершены!</b>\n\n"
    result_text += "📊 <b>Ваши результаты:</b>\n\n"

    result_text += "<b>🧠 Стили мышления:</b>\n"
    inq_scores = {
        k: v
        for k, v in all_scores.items()
        if k in ["Синтетический", "Идеалистический", "Прагматический", "Аналитический", "Реалистический"]
    }
    sorted_inq = sorted(inq_scores.items(), key=lambda x: x[1], reverse=True)

    for i, (style, score) in enumerate(sorted_inq):
        emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "📍"
        result_text += f"{emoji} {style}: {score} баллов\n"

    result_text += f"\n<b>🎭 Темперамент:</b> {all_scores.get('temperament', 'Не определен')}\n"
    result_text += f"<b>📊 E (экстраверсия):</b> {all_scores.get('E', 0)}\n"
    result_text += f"<b>📊 N (нейротизм):</b> {all_scores.get('N', 0)}\n"
    result_text += f"<b>📊 L (шкала лжи):</b> {all_scores.get('L', 0)}\n"

    await message.edit_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=MESSAGES["button_again"], callback_data="start_personal_data")]]
        ),
    )

    updated_user = await get_or_create_user(user_id=user.user_id)
    await admin_reports.send_to_admin(updated_user, all_scores)
