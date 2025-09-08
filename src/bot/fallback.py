"""
Fallback обработчики для необработанных событий
"""

import logging
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from .globals import dp
from config.const import MESSAGES

logger = logging.getLogger(__name__)


@dp.message()
async def fallback_message_handler(message: Message, state: FSMContext):
    """
    Fallback обработчик для всех необработанных сообщений
    Срабатывает последним, если никакой другой обработчик не сработал
    """
    user_id = message.from_user.id
    text = message.text or message.caption or "[медиа]"
    
    logger.info(f"🔄 Fallback: необработанное сообщение от пользователя {user_id}: '{text[:30]}...'")
    
    # Получаем текущее состояние
    current_state = await state.get_state()
    logger.info(f"   Текущее состояние FSM: {current_state}")
    
    # Сбрасываем состояние и предлагаем начать заново
    await state.clear()
    
    await message.reply(
        "🤖 Привет! Я не понимаю это сообщение.\n\n"
        "Для начала психологического тестирования отправьте команду /start",
        reply_markup=None
    )


@dp.callback_query()
async def fallback_callback_handler(callback: CallbackQuery, state: FSMContext):
    """
    Fallback обработчик для всех необработанных callback запросов
    Срабатывает последним, если никакой другой обработчик не сработал
    """
    user_id = callback.from_user.id
    data = callback.data or "unknown"
    
    logger.info(f"🎯 Fallback: необработанный callback от пользователя {user_id}: '{data}'")
    
    # Получаем текущее состояние
    current_state = await state.get_state()
    logger.info(f"   Текущее состояние FSM: {current_state}")
    
    # Отвечаем на callback чтобы убрать "загрузку"
    await callback.answer("⚠️ Эта кнопка больше не активна")
    
    # Сбрасываем состояние
    await state.clear()
    
    # Отправляем новое сообщение с инструкцией
    await callback.message.edit_text(
        "🔄 Сессия истекла или произошла ошибка.\n\n"
        "Давайте начнем тестирование заново!\n"
        "Отправьте команду /start для продолжения.",
        reply_markup=None
    )