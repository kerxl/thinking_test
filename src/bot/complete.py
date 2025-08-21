from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from .globals import task_manager
from config.const import MESSAGES
from src.core.admin_reports import admin_reports
from src.database.operations import get_or_create_user
from src.integration.senler import senler_integration


async def complete_all_tasks(message: Message, user):
    """
    Завершение всего тестирования
    """
    all_scores = await task_manager.complete_all_tasks(user)

    if not all_scores:
        await message.edit_text(MESSAGES["summary_result_error"])
        return

    result_text = "🎉 <b>Все тесты завершены!✅</b>\n\n"
    result_text += "📊 <b>Ваши результаты:</b>\n\n"

    result_text += "<b>🧠 Стили мышления:</b>\n"
    inq_scores = {
        k: v
        for k, v in all_scores.items()
        if k
        in [
            "Синтетический",
            "Идеалистический",
            "Прагматический",
            "Аналитический",
            "Реалистический",
        ]
    }
    sorted_inq = sorted(inq_scores.items(), key=lambda x: x[1], reverse=True)

    for i, (style, score) in enumerate(sorted_inq):
        emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "📍"
        result_text += f"{emoji} {style}: {score} баллов\n"

    result_text += (
        f"\n<b>🎭 Темперамент:</b> {all_scores.get('temperament', 'Не определен')}\n"
    )
    result_text += f"<b>📊 E (экстраверсия):</b> {all_scores.get('E', 0)}\n"
    result_text += f"<b>📊 N (нейротизм):</b> {all_scores.get('N', 0)}\n"
    result_text += f"<b>📊 L (шкала лжи):</b> {all_scores.get('L', 0)}\n"

    # Устанавливаем время отправки персональной ссылки через 24 часа для пользователей не из Senler
    if not user.from_senler:
        from datetime import datetime, timedelta
        from config.settings import DEBUG
        from src.database.operations import update_user as update_user_db

        # В режиме отладки - отправка через 5 секунд, иначе через 24 часа
        if DEBUG:
            send_time = datetime.now() + timedelta(seconds=5)
        else:
            send_time = datetime.now() + timedelta(hours=24)

        # Устанавливаем время отправки ссылки
        await update_user_db(user_id=user.user_id, admin_link_send_time=send_time)

    # Проверяем, пришел ли пользователь из Senler
    if user.from_senler:
        # Если пользователь из Senler, показываем результаты и возвращаем в Senler
        result_text += "\n\n✨ <b>Спасибо за прохождение теста!</b>\n"
        result_text += "<i>Сейчас мы вернем вас в Senler...</i>"

        await message.edit_text(result_text)

        # Возвращаем пользователя в Senler
        await senler_integration.return_user_to_senler(
            user.user_id, "Спасибо за прохождение теста! Ваши результаты сохранены."
        )
    else:
        # Обычное завершение для пользователей не из Senler
        result_text += "\n\n🎁 <b>Спасибо за прохождение теста!</b>\n"
        result_text += "📧 <i>Через 24 часа вам придет персональная ссылка с дополнительной информацией.</i>"

        await message.edit_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=MESSAGES["button_again"],
                            callback_data="start_personal_data",
                        )
                    ]
                ]
            ),
        )

    from sqlalchemy import select
    from src.database.models import AsyncSessionLocal, User

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user.user_id))
        updated_user = result.scalar_one_or_none()

    if updated_user:
        await admin_reports.send_to_admin(updated_user, all_scores)
