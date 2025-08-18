import logging
from typing import Dict
import asyncio

import httpx
import random

from config.settings import ADMIN_USER_ID, BOT_TOKEN
from src.database.models import User

logger = logging.getLogger(__name__)


class AdminReports:
    def __init__(self):
        self.counter = 1
        self.style_mapping = {
            "Синтетический": "Синтетик",
            "Идеалистический": "Идеалист",
            "Прагматический": "Прагматик",
            "Аналитический": "Аналитик",
            "Реалистический": "Реалист",
        }
        self.temperaments = ["Сангвиник", "Холерик", "Флегматик", "Меланхолик"]

    def determine_inq_type(self, scores: Dict[str, int]) -> str:
        numeric_scores = {k: v for k, v in scores.items() if isinstance(v, (int, float))}
        if len(numeric_scores) < 2:
            return "Неопределен"

        sorted_scores = sorted(numeric_scores.items(), key=lambda x: x[1], reverse=True)

        first_style, first_score = sorted_scores[0]
        second_style, second_score = sorted_scores[1]

        total_score = sum(numeric_scores.values())

        if total_score > 0:
            score_diff_percent = ((first_score - second_score) / total_score) * 100
        else:
            score_diff_percent = 100

        first_style_name = self.get_style_short_name(first_style)
        second_style_name = self.get_style_short_name(second_style)

        if score_diff_percent < 10:
            return f"{first_style_name}-{second_style_name}"
        else:
            return first_style_name

    def get_style_short_name(self, style_key: str) -> str:
        return self.style_mapping.get(style_key, style_key)

    def get_temperament_type(self, user_data: User) -> str:
        if user_data.age:
            return self.temperaments[user_data.age % len(self.temperaments)]
        return random.choice(self.temperaments)

    def format_admin_report(self, user_data: User, scores: Dict[str, int]) -> str:
        inq_type = self.determine_inq_type(scores)

        username_display = f"@{user_data.username}" if user_data.username else "нет username"

        full_name = f"{user_data.first_name or 'Не указано'} {user_data.last_name or ''}"
        full_name = full_name.strip()

        temperament = self.get_temperament_type(user_data)

        report = f"Отправка № {self.counter:03d}\n\n"
        report += f"User_id - {user_data.user_id}\n"
        report += f"tg: {username_display}\n\n"
        report += f"Имя фамилия: {full_name}\n"
        report += f"Возраст = {user_data.age or 'Не указан'}\n\n"

        # Получаем реальные данные EPI из scores
        e_level = scores.get('E', 0)
        n_level = scores.get('N', 0)
        l_level = scores.get('L', 0)
        actual_temperament = scores.get('temperament', temperament)

        report += f"🧠 InQ-тип = {inq_type}\n"
        report += f"🎭 Темперамент = {actual_temperament}\n"
        report += f"📊 E = {e_level} - уровень экстраверсии\n"
        report += f"📊 N = {n_level} - уровень нейротизма\n"
        report += f"📊 L = {l_level} - социальная одобряемость\n\n"

        report += "📊 Детальные результаты:\n"

        numeric_scores = {k: v for k, v in scores.items() if isinstance(v, (int, float))}
        text_scores = {k: v for k, v in scores.items() if not isinstance(v, (int, float))}

        sorted_scores = sorted(numeric_scores.items(), key=lambda x: x[1], reverse=True)

        for style_key, score in sorted_scores:
            report += f"• {style_key}: {score} баллов\n"

        for style_key, value in text_scores.items():
            report += f"• {style_key}: {value}\n"

        if user_data.test_start and user_data.test_end:
            duration = user_data.test_end - user_data.test_start
            duration_minutes = int(duration.total_seconds() / 60)
            report += f"\n⏱ Время прохождения: {duration_minutes} минут\n"
            report += f"📅 Завершен: {user_data.test_end.strftime('%d.%m.%Y %H:%M')}"

        self.counter += 1
        return report

    async def send_to_admin(self, user_data: User, scores: Dict[str, int]) -> bool:

        if not ADMIN_USER_ID or ADMIN_USER_ID == 0:
            logger.warning("ADMIN_USER_ID не настроен - отчет не отправлен")
            return False

        max_retries = 3
        base_delay = 1

        for attempt in range(max_retries):
            try:
                report = self.format_admin_report(user_data, scores)

                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

                payload = {
                    "chat_id": ADMIN_USER_ID,
                    "text": report,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, timeout=30)

                    if response.status_code == 200:
                        logger.info(f"Отчет отправлен администратору для пользователя {user_data.user_id}")
                        return True
                    elif response.status_code == 429:
                        # Rate limit exceeded
                        try:
                            response_data = response.json()
                            retry_after = response_data.get("parameters", {}).get("retry_after", 60)
                        except:
                            retry_after = 60

                        logger.warning(f"Rate limit (попытка {attempt + 1}/{max_retries}). Жду {retry_after} секунд...")

                        if attempt < max_retries - 1:  # Не ждем на последней попытке
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            logger.error(f"Превышен лимит попыток отправки отчета для пользователя {user_data.user_id}")
                            return False
                    else:
                        logger.error(f"Ошибка отправки отчета администратору: {response.status_code} - {response.text}")

                        # Для других ошибок делаем экспоненциальную задержку
                        if attempt < max_retries - 1:
                            delay = base_delay * (2**attempt)
                            logger.info(f"Повторная попытка через {delay} секунд...")
                            await asyncio.sleep(delay)
                            continue
                        return False

            except Exception as e:
                logger.error(f"Ошибка при отправке отчета администратору (попытка {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    logger.info(f"Повторная попытка через {delay} секунд...")
                    await asyncio.sleep(delay)
                    continue
                return False

        return False


admin_reports = AdminReports()
