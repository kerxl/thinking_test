import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from src.database.models import AsyncSessionLocal, User
from config.settings import BOT_TOKEN, DEBUG
import httpx

logger = logging.getLogger(__name__)


class LinkScheduler:
    """
    Планировщик для отправки отложенных ссылок Senler пользователям
    """

    def __init__(self):
        self.running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Запускает планировщик"""
        if self.running:
            return

        self.running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Link scheduler started")

    async def stop(self):
        """Останавливает планировщик"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Link scheduler stopped")

    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        # В режиме отладки проверяем каждую секунду, иначе каждую минуту
        check_interval = 1 if DEBUG else 60

        while self.running:
            try:
                await self._check_and_send_links()
                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(check_interval)  # Продолжаем работу даже при ошибке

    async def _check_and_send_links(self):
        """Проверяет и отправляет ссылки, время которых настало"""
        async with AsyncSessionLocal() as session:
            # Находим всех пользователей, которым нужно отправить ссылки
            current_time = datetime.now()

            result = await session.execute(
                select(User).where(
                    User.admin_senler_link.is_not(None),
                    User.admin_link_send_time.is_not(None),
                    User.admin_link_send_time <= current_time,
                )
            )

            users_to_notify = result.scalars().all()

            for user in users_to_notify:
                try:
                    await self._send_link_to_user(user)

                    # Очищаем поля после отправки
                    user.admin_senler_link = None
                    user.admin_link_send_time = None

                except Exception as e:
                    logger.error(f"Failed to send link to user {user.user_id}: {e}")

            if users_to_notify:
                await session.commit()
                logger.info(f"Processed {len(users_to_notify)} scheduled links")

    async def _send_link_to_user(self, user: User):
        """Отправляет ссылку конкретному пользователю"""
        message_text = (
            f"🎉 Поздравляю! Теперь у тебя есть собственный личный бот.\n\n"
            f"🔗 Ссылка: {user.admin_senler_link}\n\n"
            f"После перехода в чат он появится в твоей левой колонке. С этого момента, когда захочешь разобраться в каком-то вопросе, просто нажимай на значок с зелёным сердечком — и бот всегда будет рядом, готов помочь.\n\n"
            f"Но прежде чем начать, обязательно загляни в инструкцию ниже. Это займёт всего 10 минут, зато ты сразу освоишь все возможности и фишки. Обещаю, будет интересно 👇"
        )

        # Создаем inline-кнопку для перехода по ссылке
        inline_keyboard = {
            "inline_keyboard": [
                [{"text": "🚀 Ознакомиться", "url": user.admin_senler_link}]
            ]
        }

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": user.user_id,
            "text": message_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
            "reply_markup": inline_keyboard,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30)

            if response.status_code == 200:
                logger.info(f"Link sent successfully to user {user.user_id}")
            else:
                logger.error(
                    f"Failed to send link to user {user.user_id}: {response.status_code} - {response.text}"
                )
                raise Exception(f"Telegram API error: {response.status_code}")


# Глобальный экземпляр планировщика
link_scheduler = LinkScheduler()
