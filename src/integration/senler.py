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

logger = logging.getLogger(__name__)


class SenlerIntegration:
    """Класс для работы с Senler API"""

    def __init__(self, bot_token: str = BOT_TOKEN):
        self.bot_token = bot_token
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}"

    async def process_webhook_request(
        self, user_id: int, username: str, senler_token: str
    ) -> Dict[str, Any]:
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
            user = await update_user(
                user_id=user_id, senler_token=senler_token, from_senler=True
            )

            if user:
                logger.info(f"Пользователь {user_id} инициализирован из Senler")
            else:
                logger.error(f"Ошибка инициализации пользователя {user_id} из Senler")

            # Отправляем стартовое сообщение пользователю через Telegram API
            await self._send_start_message(user_id)

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
            async with httpx.AsyncClient() as client:
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

                response = await client.post(
                    f"{self.telegram_api_url}/sendMessage",
                    json={
                        "chat_id": user_id,
                        "text": message_text,
                        "parse_mode": "HTML",
                        "reply_markup": keyboard,
                    },
                )

                if response.status_code == 200:
                    logger.info(
                        f"Стартовое сообщение отправлено пользователю {user_id}"
                    )
                else:
                    logger.error(
                        f"Ошибка отправки сообщения пользователю {user_id}: {response.text}"
                    )

        except Exception as e:
            logger.error(f"Ошибка отправки стартового сообщения: {e}")

    async def return_user_to_senler(
        self, user_id: int, message: str = "Спасибо за прохождение теста!"
    ) -> bool:
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
                    logger.info(
                        f"Финальное сообщение отправлено пользователю {user_id}"
                    )
                else:
                    logger.error(
                        f"Ошибка отправки финального сообщения: {response.text}"
                    )

        except Exception as e:
            logger.error(f"Ошибка отправки финального сообщения: {e}")


# Глобальный экземпляр для использования в других модулях
senler_integration = SenlerIntegration()
