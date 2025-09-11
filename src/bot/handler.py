from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from config.const import MESSAGES, dp


@dp.message(CommandStart())
async def start_handler(message: Message):
    """
    Обрабатывает команду /start - запускает стандартное тестирование
    Senler может перехватить управление через webhook позже
    """
    await message.answer(
        "🎯 <b>Добро пожаловать в тест 'Стили мышления'!</b>\n\n"
        "Этот тест поможет определить ваш доминирующий стиль мышления и лучше понять ваши предпочтения в принятии решений.\n\n"
        "📊 Состоит из трех тестов\n"
        "⏱️ Займет около 15-20 минут\n"
        "🎁 В конце получите персональный анализ\n\n"
        "<i>Для начала нам нужно собрать немного информации о вас.</i>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=MESSAGES["button_start"],
                        callback_data="start_personal_data",
                    )
                ]
            ]
        ),
    )
