"""
Модуль для интеграции с Senler API
"""

import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from src.database.operations import get_or_create_user, get_user_by_id, update_user
from config.settings import BOT_TOKEN
from config.const import MESSAGES

# Импорт обработчиков для регистрации роутеров
from src.bot import handler

logger = logging.getLogger(__name__)


class SenlerIntegration:
    """Класс для работы с Senler API"""

    def __init__(self, bot_token: str = BOT_TOKEN):
        self.bot_token = bot_token
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}"

    async def process_webhook_request(self, user_id: int, username: str, senler_token: str) -> Dict[str, Any]:
        """
        Обрабатывает webhook запрос от Senler

        Args:
            user_id: Telegram user ID
            username: Telegram username
            senler_token: Token от Senler для возврата пользователя

        Returns:
            Dict с результатом обработки
        """
        try:
            logger.info(f"Получен webhook от Senler для пользователя {user_id}")

            # Получаем или создаем пользователя
            user = await get_or_create_user(user_id=user_id, username=username)

            # Обновляем пользователя с Senler данными
            user = await update_user(user_id=user_id, senler_token=senler_token, from_senler=True)

            if user:
                logger.info(f"Пользователь {user_id} инициализирован из Senler")
            else:
                logger.error(f"Ошибка инициализации пользователя {user_id} из Senler")

            # Отправляем стартовое сообщение пользователю
            # ВАЖНО: Используем aiogram bot для корректной работы с webhook
            await self._send_start_message_via_bot(user_id)

            return {
                "success": True,
                "message": "Пользователь успешно инициализирован",
                "user_id": user_id,
            }

        except Exception as e:
            logger.error(f"Ошибка обработки webhook от Senler: {e}")
            return {"success": False, "error": str(e)}

    async def _send_start_message(self, user_id: int):
        """Отправляет стартовое сообщение пользователю через Telegram API"""
        try:
            logger.info(f"📤 Отправка стартового сообщения пользователю {user_id}")
            logger.info(f"🔑 Используем Telegram API: {self.telegram_api_url}")

            # Добавляем таймауты для более надежной работы
            timeout = httpx.Timeout(30.0, connect=10.0)

            async with httpx.AsyncClient(timeout=timeout) as client:
                message_text = (
                    "🎯 <b>Добро пожаловать в тест 'Стили мышления'!</b>\n\n"
                    "Этот тест поможет определить ваш доминирующий стиль мышления и лучше понять ваши предпочтения в принятии решений.\n\n"
                    "📊 Состоит из трех тестов\n"
                    "⏱️ Займет около 15-20 минут\n"
                    "🎁 В конце получите персональный анализ\n\n"
                    "<i>Для начала нам нужно собрать немного информации о вас.</i>"
                )

                keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": MESSAGES.get("button_start", "Начать"),
                                "callback_data": "start_personal_data",
                            }
                        ]
                    ]
                }

                request_data = {
                    "chat_id": user_id,
                    "text": message_text,
                    "parse_mode": "HTML",
                    "reply_markup": keyboard,
                }

                logger.info(f"🚀 Отправляем запрос в Telegram API...")

                try:
                    response = await client.post(
                        f"{self.telegram_api_url}/sendMessage",
                        json=request_data,
                    )

                    if response.status_code == 200:
                        response_data = response.json()
                        logger.info(f"✅ Стартовое сообщение отправлено пользователю {user_id}")
                        logger.info(f"📥 Ответ от Telegram API: {response_data}")
                    else:
                        logger.error(f"❌ Ошибка отправки сообщения пользователю {user_id}")
                        logger.error(f"📥 HTTP {response.status_code}: {response.text}")

                        # Если ошибка связана с токеном или доступом - используем альтернативный способ
                        if response.status_code in [401, 403]:
                            logger.warning("🔄 Попытка отправить через aiogram bot...")
                            await self._send_via_aiogram_bot(user_id, message_text, keyboard)

                except httpx.ConnectTimeout:
                    logger.error("⏰ Таймаут подключения к Telegram API")
                    logger.warning("🔄 Попытка отправить через aiogram bot...")
                    await self._send_via_aiogram_bot(user_id, message_text, keyboard)
                except httpx.ReadTimeout:
                    logger.error("⏰ Таймаут чтения ответа от Telegram API")
                    logger.warning("🔄 Попытка отправить через aiogram bot...")
                    await self._send_via_aiogram_bot(user_id, message_text, keyboard)
                except Exception as api_error:
                    logger.error(f"❌ Общая ошибка API: {api_error}")
                    logger.warning("🔄 Попытка отправить через aiogram bot...")
                    await self._send_via_aiogram_bot(user_id, message_text, keyboard)

        except Exception as e:
            logger.error(f"❌ Ошибка отправки стартового сообщения: {e}")
            import traceback

            logger.error(f"🐛 Traceback: {traceback.format_exc()}")

            # Fallback - попытка через aiogram
            try:
                await self._send_via_aiogram_bot(
                    user_id,
                    "🎯 Добро пожаловать в тест 'Стили мышления'!",
                    {"inline_keyboard": [[{"text": "Начать", "callback_data": "start_personal_data"}]]},
                )
            except Exception as fallback_error:
                logger.error(f"❌ Fallback отправка также не удалась: {fallback_error}")

    async def _send_via_aiogram_bot(self, user_id: int, text: str, keyboard: dict):
        """Альтернативный способ отправки через aiogram bot"""
        try:
            from src.bot.globals import bot
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

            # Преобразуем keyboard в aiogram формат
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=btn["text"], callback_data=btn["callback_data"]) for btn in row]
                    for row in keyboard["inline_keyboard"]
                ]
            )

            await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML", reply_markup=markup)
            logger.info(f"✅ Сообщение отправлено через aiogram bot пользователю {user_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка отправки через aiogram: {e}")

    async def _send_start_message_via_bot(self, user_id: int):
        """Отправляет стартовое сообщение только через aiogram bot (для webhook режима)"""
        try:
            logger.info(f"📤 Отправка стартового сообщения через aiogram bot пользователю {user_id}")

            from src.bot.globals import bot
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

            message_text = (
                "🎯 <b>Добро пожаловать в тест 'Стили мышления'!</b>\n\n"
                "Этот тест поможет определить ваш доминирующий стиль мышления и лучше понять ваши предпочтения в принятии решений.\n\n"
                "📊 Состоит из трех тестов\n"
                "⏱️ Займет около 15-20 минут\n"
                "🎁 В конце получите персональный анализ\n\n"
                "<i>Для начала нам нужно собрать немного информации о вас.</i>"
            )

            # Создаем клавиатуру через aiogram
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=MESSAGES.get("button_start", "Начать тест"), callback_data="start_personal_data"
                        )
                    ]
                ]
            )

            await bot.send_message(chat_id=user_id, text=message_text, parse_mode="HTML", reply_markup=markup)

            logger.info(f"✅ Стартовое сообщение отправлено через aiogram bot пользователю {user_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка отправки стартового сообщения через aiogram: {e}")
            import traceback

            logger.error(f"🐛 Traceback: {traceback.format_exc()}")

            # Попытка отправить простое сообщение без клавиатуры
            try:
                from src.bot.globals import bot

                await bot.send_message(
                    chat_id=user_id,
                    text="🎯 Добро пожаловать в тест 'Стили мышления'!\n\nОтправьте команду /start для начала тестирования.",
                    parse_mode="HTML",
                )
                logger.info(f"✅ Отправлено упрощенное сообщение пользователю {user_id}")
            except Exception as fallback_error:
                logger.error(f"❌ Критическая ошибка отправки сообщения: {fallback_error}")

    async def return_user_to_senler(self, user_id: int, message: str = "Спасибо за прохождение теста!") -> bool:
        """
        Возвращает пользователя в Senler после завершения тестов

        Args:
            user_id: Telegram user ID
            message: Сообщение для отправки пользователю

        Returns:
            bool: Успешность операции
        """
        try:
            user = await get_user_by_id(user_id)
            if not user or not user.senler_token:
                logger.warning(f"Пользователь {user_id} не найден или нет Senler token")
                return False

            # Отправляем финальное сообщение пользователю
            await self._send_final_message(user_id, message)

            # Здесь можно добавить логику возврата в Senler через их API
            # Например, отправка POST запроса с senler_token

            logger.info(f"Пользователь {user_id} возвращен в Senler")
            return True

        except Exception as e:
            logger.error(f"Ошибка возврата пользователя {user_id} в Senler: {e}")
            return False

    async def _send_final_message(self, user_id: int, message: str):
        """Отправляет финальное сообщение пользователю"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.telegram_api_url}/sendMessage",
                    json={"chat_id": user_id, "text": message, "parse_mode": "HTML"},
                )

                if response.status_code == 200:
                    logger.info(f"Финальное сообщение отправлено пользователю {user_id}")
                else:
                    logger.error(f"Ошибка отправки финального сообщения: {response.text}")

        except Exception as e:
            logger.error(f"Ошибка отправки финального сообщения: {e}")


# Глобальный экземпляр для использования в других модулях
senler_integration = SenlerIntegration()
