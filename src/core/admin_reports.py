import logging
from typing import Dict

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
        report += f"User_id - {user_data.user_id}\n\n"
        report += f"tg: {username_display}\n\n"
        report += f"Имя фамилия: {full_name}\n\n"
        report += f"Возраст = {user_data.age or 'Не указан'}\n"
        report += f"Темперамент = {temperament}\n\n"

        report += f"🧠 InQ-тип = {inq_type}\n"

        e_level = random.randint(0, 24)
        n_level = random.randint(0, 24)
        l_level = random.randint(0, 9)

        report += f"E = {e_level} - уровень экстраверсии\n"
        report += f"N = {n_level} - уровень нейротизма\n"
        report += f"L = {l_level} - социальная одобряемость\n"

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

        try:
            report = self.format_admin_report(user_data, scores)

            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

            payload = {"chat_id": ADMIN_USER_ID, "text": report, "parse_mode": "HTML", "disable_web_page_preview": True}

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30)

                if response.status_code == 200:
                    logger.info(f"Отчет отправлен администратору для пользователя {user_data.user_id}")
                    return True
                else:
                    logger.error(f"Ошибка отправки отчета администратору: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Ошибка при отправке отчета администратору: {e}")
            return False


admin_reports = AdminReports()
