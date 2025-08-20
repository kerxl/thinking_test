"""
Комбинированный запуск Telegram бота и FastAPI сервера для Senler интеграции
"""
import asyncio
import json
import logging
import uvicorn
from multiprocessing import Process
import sys
import os

# Добавляем путь к корню проекта для корректных импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.const import TaskEntity, MESSAGES
from config.settings import DEBUG
from src.database.operations import init_db
from src.bot.globals import bot, dp, task_manager
from src.api.server import app

logging.basicConfig(
    level=logging.INFO if DEBUG else logging.WARNING, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_bot():
    """Запуск Telegram бота"""
    try:
        await init_db()
        await TaskEntity.priorities.value.load_questions()
        await TaskEntity.inq.value.load_questions()
        await TaskEntity.epi.value.load_questions()

        logger.info("🤖 Telegram бот запущен")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска Telegram бота: {e}")


def run_api_server():
    """Запуск FastAPI сервера"""
    try:
        logger.info("🌐 Запуск FastAPI сервера...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info" if DEBUG else "warning"
        )
    except Exception as e:
        logger.error(f"❌ Ошибка запуска API сервера: {e}")


async def main():
    """Основная функция запуска"""
    # Загружаем сообщения из конфигурации
    with open("config/constants.json", "r", encoding="utf-8") as json_file:
        MESSAGES.update(json.load(json_file))
    
    logger.info("🚀 Запуск Mind Style Bot с Senler интеграцией")
    
    # Запускаем API сервер в отдельном процессе
    api_process = Process(target=run_api_server)
    api_process.start()
    
    try:
        # Запускаем Telegram бота в основном процессе
        await run_bot()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    finally:
        logger.info("🔌 Остановка API сервера...")
        api_process.terminate()
        api_process.join()
        logger.info("✅ Все сервисы остановлены")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Приложение остановлено пользователем")