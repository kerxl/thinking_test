"""
Запуск бота в режиме webhook для production с Senler интеграцией
"""

import asyncio
import json
import logging
import uvicorn
import sys
import os

# Добавляем путь к корню проекта для корректных импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.const import TaskEntity, MESSAGES
from config.settings import DEBUG
from src.database.operations import init_db
from src.bot.globals import bot, task_manager
from src.api.server import app
from src.core.scheduler import link_scheduler

# Импорт обработчиков для регистрации роутеров
from src.bot import handler
from src.bot import callback
from src.bot import proccesser
from src.bot import fallback  # Fallback обработчики (должны быть последними)

logging.basicConfig(
    level=logging.INFO if DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def setup_webhook_bot():
    """Настройка Telegram бота для работы через webhook"""
    try:
        await init_db()
        await TaskEntity.priorities.value.load_questions()
        await TaskEntity.inq.value.load_questions()
        await TaskEntity.epi.value.load_questions()

        # Запускаем планировщик ссылок
        await link_scheduler.start()

        logger.info("🤖 Telegram бот настроен для webhook режима")
        
        # Устанавливаем webhook для получения обновлений через FastAPI
        webhook_url = "https://wikisound.store/webhook"
        await bot.set_webhook(webhook_url)
        logger.info(f"🔌 Webhook установлен: {webhook_url}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки Telegram бота: {e}")
        raise


async def main():
    """Основная функция запуска в webhook режиме"""
    # Загружаем сообщения из конфигурации
    with open("config/constants.json", "r", encoding="utf-8") as json_file:
        MESSAGES.update(json.load(json_file))

    logger.info("🚀 Запуск Mind Style Bot в webhook режиме с Senler интеграцией")

    # Настраиваем Telegram бота для webhook
    await setup_webhook_bot()

    # Запускаем API сервер в том же процессе
    try:
        logger.info("🌐 Запуск FastAPI сервера в webhook режиме...")
        config = uvicorn.Config(
            app, 
            host="0.0.0.0", 
            port=8000, 
            log_level="info" if DEBUG else "warning"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    finally:
        logger.info("🔌 Остановка планировщика...")
        await link_scheduler.stop()
        logger.info("✅ Все сервисы остановлены")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Приложение остановлено пользователем")