"""
Модуль для интеграции с Senler API
"""

import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

from src.database.operations import get_or_create_user, get_user_by_id, update_user, get_user_by_username
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

    async def try_establish_contact_and_get_user_id(self, username: str, establish_contact: bool = True) -> Optional[int]:
        """
        Пытается установить контакт с пользователем и получить user_id
        
        Args:
            username: Telegram username (без @)
            establish_contact: Попытаться отправить приветственное сообщение для установки контакта
            
        Returns:
            int: Telegram user_id или None если не найден
        """
        try:
            # Убираем @ если он есть
            clean_username = username.lstrip('@') if username else ""
            
            if not clean_username:
                logger.warning("Пустой username для установки контакта")
                return None
            
            logger.info(f"🤝 Попытка установить контакт с @{clean_username}")
            
            timeout = httpx.Timeout(30.0, connect=10.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                if establish_contact:
                    # Пробуем отправить приветственное сообщение
                    welcome_message = {
                        "chat_id": f"@{clean_username}",
                        "text": (
                            "🎯 Привет! Тебя перенаправили к нам из Senler для прохождения теста 'Стили мышления'.\n\n"
                            "Нажми /start когда будешь готов начать тестирование!"
                        ),
                        "disable_notification": False
                    }
                    
                    logger.info(f"📤 Отправляем приветственное сообщение @{clean_username}")
                    response = await client.post(
                        f"{self.telegram_api_url}/sendMessage",
                        json=welcome_message
                    )
                    
                    if response.status_code == 200:
                        msg_data = response.json()
                        if msg_data.get("ok") and "result" in msg_data:
                            chat = msg_data["result"].get("chat", {})
                            user_id = chat.get("id")
                            if user_id:
                                logger.info(f"✅ Контакт установлен! user_id: {user_id} для @{clean_username}")
                                return user_id
                        else:
                            error_description = msg_data.get("description", "Unknown error")
                            logger.info(f"⚠️ Не удалось отправить приветственное сообщение: {error_description}")
                    else:
                        response_data = response.json() if response.status_code != 500 else {}
                        error_description = response_data.get("description", "Unknown error")
                        logger.info(f"⚠️ Ошибка отправки приветственного сообщения: {error_description}")
                
                # Если приветственное сообщение не сработало, используем стандартные методы
                return await self.get_user_id_by_username(clean_username)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка установки контакта с @{clean_username}: {e}")
            return None

    async def get_user_id_by_username(self, username: str) -> Optional[int]:
        """
        Получает user_id через Telegram Bot API используя username
        
        Args:
            username: Telegram username (без @)
            
        Returns:
            int: Telegram user_id или None если не найден
        """
        try:
            # Убираем @ если он есть
            clean_username = username.lstrip('@') if username else ""
            
            if not clean_username:
                logger.warning("Пустой username для поиска user_id")
                return None
            
            logger.info(f"🔍 Ищем user_id для username: @{clean_username}")
            
            timeout = httpx.Timeout(30.0, connect=10.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Метод 1: Пробуем получить информацию о пользователе через getChat
                # Работает только если бот имел контакт с пользователем
                logger.info(f"🔍 Метод 1: Пытаемся getChat для @{clean_username}")
                response = await client.post(
                    f"{self.telegram_api_url}/getChat",
                    json={"chat_id": f"@{clean_username}"}
                )
                
                if response.status_code == 200:
                    chat_data = response.json()
                    if chat_data.get("ok") and "result" in chat_data:
                        user_id = chat_data["result"].get("id")
                        if user_id:
                            logger.info(f"✅ Найден user_id через getChat: {user_id} для @{clean_username}")
                            return user_id
                    else:
                        error_description = chat_data.get("description", "Unknown error")
                        logger.info(f"⚠️  getChat неуспешен: {error_description}")
                else:
                    logger.info(f"⚠️  getChat HTTP {response.status_code}: {response.text[:100]}")
                
                # Метод 2: Пробуем отправить сообщение для получения chat_id из ошибки
                # Этот метод может дать информацию о том, что чат существует
                logger.info(f"🔍 Метод 2: Пытаемся sendMessage для @{clean_username}")
                test_message = {
                    "chat_id": f"@{clean_username}",
                    "text": "test",
                    "disable_notification": True
                }
                
                response = await client.post(
                    f"{self.telegram_api_url}/sendMessage",
                    json=test_message
                )
                
                if response.status_code == 200:
                    msg_data = response.json()
                    if msg_data.get("ok") and "result" in msg_data:
                        chat = msg_data["result"].get("chat", {})
                        user_id = chat.get("id")
                        if user_id:
                            logger.info(f"✅ Найден user_id через sendMessage: {user_id} для @{clean_username}")
                            # Удаляем тестовое сообщение если удалось
                            try:
                                message_id = msg_data["result"].get("message_id")
                                await client.post(
                                    f"{self.telegram_api_url}/deleteMessage",
                                    json={"chat_id": user_id, "message_id": message_id}
                                )
                                logger.info(f"🗑️ Тестовое сообщение удалено")
                            except:
                                logger.info(f"⚠️  Не удалось удалить тестовое сообщение")
                            return user_id
                else:
                    response_data = response.json() if response.status_code != 500 else {}
                    error_description = response_data.get("description", "Unknown error")
                    logger.info(f"⚠️  sendMessage неуспешен: {error_description}")
                
                # Если оба метода не сработали
                logger.warning(f"❌ Не удалось получить user_id для @{clean_username} через Telegram API")
                logger.info(f"💡 Возможные причины:")
                logger.info(f"   - Пользователь не существует")
                logger.info(f"   - Пользователь заблокировал бота")
                logger.info(f"   - Бот не имел контакта с пользователем")
                logger.info(f"   - Пользователь изменил настройки приватности")
                
                return None
                    
        except httpx.ConnectTimeout:
            logger.error(f"⏰ Таймаут подключения при поиске user_id для @{clean_username}")
            return None
        except httpx.ReadTimeout:
            logger.error(f"⏰ Таймаут чтения при поиске user_id для @{clean_username}")
            return None
        except Exception as e:
            logger.error(f"❌ Общая ошибка получения user_id для @{clean_username}: {e}")
            import traceback
            logger.error(f"🐛 Traceback: {traceback.format_exc()}")
            return None

    async def process_webhook_request(self, user_id: int, username: str, senler_token: str) -> Dict[str, Any]:
        """
        Обрабатывает webhook запрос от Senler

        Args:
            user_id: Telegram user ID (может быть виртуальный для Senler пользователей)
            username: Telegram username
            senler_token: Token от Senler для возврата пользователя

        Returns:
            Dict с результатом обработки
        """
        try:
            is_virtual_user = user_id >= 99000000  # Виртуальные user_id начинаются с 99000000
            
            if is_virtual_user:
                logger.info(f"Получен webhook от Senler для ВИРТУАЛЬНОГО пользователя {user_id}")
                logger.info(f"🔧 Рекомендация: настройте передачу реального Telegram User ID в Senler")
            else:
                logger.info(f"Получен webhook от Senler для пользователя {user_id}")

            # Получаем или создаем пользователя
            user = await get_or_create_user(user_id=user_id, username=username)
            
            # Проверяем, был ли пользователь уже в системе
            was_existing_user = user and not user.from_senler
            if was_existing_user:
                logger.info(f"🔗 Пользователь {user_id} уже существует в системе, связываем с Senler")
            else:
                logger.info(f"👤 Новый пользователь {user_id} создан через Senler")

            # Обновляем пользователя с Senler данными
            user = await update_user(user_id=user_id, senler_token=senler_token, from_senler=True)
            
            # Если пользователь был в процессе тестирования, сбрасываем его состояние
            if was_existing_user and user:
                logger.info(f"🔄 Сброс состояния тестирования для существующего пользователя {user_id}")
                # Сбрасываем прогресс тестирования для повторного прохождения
                await update_user(
                    user_id=user_id,
                    current_task_type=None,
                    current_question=None,
                    current_step=None
                )

            if user:
                logger.info(f"Пользователь {user_id} инициализирован из Senler")
            else:
                logger.error(f"Ошибка инициализации пользователя {user_id} из Senler")

            # Для всех пользователей (реальных и виртуальных) запускаем тестирование
            if is_virtual_user:
                logger.info(f"🧪 Запуск тестирования для виртуального пользователя {user_id}")
            else:
                logger.info(f"🧪 Запуск тестирования для реального пользователя {user_id}")
            
            # Запускаем тестирование через отправку стартового сообщения с кнопкой
            await self._send_test_start_message_via_bot(user_id)
            
            return {
                "success": True,
                "message": "Тестирование запущено после прохождения Senler воронки",
                "user_id": user_id,
                "is_virtual": is_virtual_user,
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

    async def _send_test_start_message_via_bot(self, user_id: int):
        """Отправляет сообщение о начале тестирования после Senler воронки"""
        try:
            logger.info(f"📤 Отправка сообщения начала тестирования пользователю {user_id}")

            from src.bot.globals import bot
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

            message_text = (
                "✨ <b>Отлично! Теперь начнем тестирование</b>\n\n"
                "🎯 <b>Тест 'Стили мышления'</b>\n\n"
                "Этот тест поможет определить ваш доминирующий стиль мышления и лучше понять ваши предпочтения в принятии решений.\n\n"
                "📊 Состоит из трех тестов\n"
                "⏱️ Займет около 15-20 минут\n"
                "🎁 В конце получите персональный анализ\n\n"
                "<i>Для начала нам нужно собрать немного информации о вас.</i>"
            )

            # Создаем клавиатуру для начала тестирования
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=MESSAGES.get("button_start", "Начать тестирование"), 
                            callback_data="start_personal_data"
                        )
                    ]
                ]
            )

            await bot.send_message(chat_id=user_id, text=message_text, parse_mode="HTML", reply_markup=markup)

            logger.info(f"✅ Сообщение о начале тестирования отправлено пользователю {user_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения начала тестирования: {e}")
            import traceback
            logger.error(f"🐛 Traceback: {traceback.format_exc()}")

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
