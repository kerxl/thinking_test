"""
Комбинированный запуск Telegram бота (polling) и FastAPI сервера для локального тестирования Senler интеграции
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
from src.bot.globals import bot, dp, task_manager
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


async def setup_bot():
    """Настройка Telegram бота для локального тестирования"""
    try:
        await init_db()
        await TaskEntity.priorities.value.load_questions()
        await TaskEntity.inq.value.load_questions()
        await TaskEntity.epi.value.load_questions()

        # Запускаем планировщик ссылок
        await link_scheduler.start()

        logger.info("🤖 Telegram бот настроен для локального тестирования")
        
        # Убираем все webhook для локального тестирования
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🧹 Webhook удален, бот работает в polling режиме")
        
    except Exception as e:
        logger.error(f"❌ Ошибка настройки Telegram бота: {e}")
        raise


async def run_bot():
    """Запуск бота в polling режиме"""
    try:
        logger.info("🤖 Запуск Telegram бота в polling режиме...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка polling бота: {e}")
    finally:
        await link_scheduler.stop()


async def run_api():
    """Запуск FastAPI сервера"""
    try:
        logger.info("🌐 Запуск FastAPI сервера на порту 8000...")
        config = uvicorn.Config(
            app, 
            host="0.0.0.0", 
            port=8000, 
            log_level="info" if DEBUG else "warning"
        )
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        logger.error(f"❌ Ошибка запуска API сервера: {e}")


async def main():
    """Основная функция запуска"""
    # Загружаем сообщения из конфигурации
    with open("config/constants.json", "r", encoding="utf-8") as json_file:
        MESSAGES.update(json.load(json_file))

    logger.info("🚀 Запуск Mind Style Bot с Senler интеграцией (локальное тестирование)")

    # Настраиваем Telegram бота
    await setup_bot()

    # Запускаем bot и API параллельно
    try:
        await asyncio.gather(
            run_bot(),
            run_api()
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        logger.info("🔌 Остановка всех сервисов...")
        await link_scheduler.stop()
        logger.info("✅ Все сервисы остановлены")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Приложение остановлено пользователем")