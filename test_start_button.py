#!/usr/bin/env python3
"""
Тест кнопки "Начать тест" - отправляет сообщение с кнопкой напрямую
"""

import asyncio
import sys
import os
import logging

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.bot.globals import bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.settings import ADMIN_USER_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_start_button():
    """Тестирует кнопку 'Начать тест'"""
    
    user_id = ADMIN_USER_ID
    logger.info(f"🧪 Тестирование кнопки 'Начать тест' для пользователя {user_id}")
    
    try:
        message_text = (
            "🎯 <b>Тест кнопки 'Начать тест'</b>\n\n"
            "Нажмите кнопку ниже для проверки работы callback обработчика."
        )

        # Создаем клавиатуру
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🚀 Начать тест", 
                callback_data="start_personal_data"
            )]
        ])
        
        logger.info("📤 Отправляем тестовое сообщение с кнопкой...")
        
        await bot.send_message(
            chat_id=user_id,
            text=message_text,
            parse_mode="HTML",
            reply_markup=markup
        )
        
        logger.info("✅ Тестовое сообщение отправлено!")
        logger.info("💡 Нажмите кнопку и проверьте логи бота")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки тестового сообщения: {e}")
        import traceback
        logger.error(f"🐛 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_start_button())