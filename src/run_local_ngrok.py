"""
Запуск бота в webhook режиме для локального тестирования с ngrok
ВАЖНО: Перед запуском запустите ngrok http 8000 в отдельном терминале
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

# ЗАМЕНИТЕ НА ВАШ NGROK URL!
NGROK_URL = "https://8224dace9452.ngrok-free.app"


async def setup_local_webhook_bot():
    """Настройка Telegram бота для работы через ngrok webhook"""
    try:
        await init_db()
        await TaskEntity.priorities.value.load_questions()
        await TaskEntity.inq.value.load_questions()
        await TaskEntity.epi.value.load_questions()

        # Запускаем планировщик ссылок
        await link_scheduler.start()

        logger.info("🤖 Telegram бот настроен для локального webhook режима")

        # Проверяем, что NGROK_URL изменен
        if "YOUR_NGROK_URL" in NGROK_URL:
            logger.error("❌ ОШИБКА: Замените YOUR_NGROK_URL на реальный ngrok URL!")
            logger.error("   1. Запустите: ngrok http 8000")
            logger.error("   2. Скопируйте HTTPS URL из вывода ngrok")
            logger.error("   3. Замените NGROK_URL в файле src/run_local_ngrok.py")
            raise ValueError("NGROK_URL не настроен")

        # Устанавливаем webhook для получения обновлений через ngrok
        webhook_url = f"{NGROK_URL}/webhook"
        await bot.set_webhook(webhook_url)
        logger.info(f"🔌 Локальный webhook установлен: {webhook_url}")

        # Также покажем Senler webhook URL
        senler_webhook = f"{NGROK_URL}/senler/webhook"
        logger.info(f"📡 Senler webhook доступен на: {senler_webhook}")

    except Exception as e:
        logger.error(f"❌ Ошибка настройки Telegram бота: {e}")
        raise


async def main():
    """Основная функция запуска в локальном webhook режиме"""
    # Загружаем сообщения из конфигурации
    with open("config/constants.json", "r", encoding="utf-8") as json_file:
        MESSAGES.update(json.load(json_file))

    logger.info("🚀 Запуск Mind Style Bot для ЛОКАЛЬНОГО тестирования с ngrok")
    logger.info("📋 Инструкции:")
    logger.info("   1. Убедитесь что ngrok запущен: ngrok http 8000")
    logger.info("   2. Обновите NGROK_URL в файле src/run_local_ngrok.py")
    logger.info("   3. Для тестирования Senler отправляйте POST на /senler/webhook")

    # Настраиваем Telegram бота для webhook
    await setup_local_webhook_bot()

    # Запускаем API сервер в том же процессе
    try:
        logger.info("🌐 Запуск FastAPI сервера для локального тестирования...")
        logger.info(f"📡 API docs: http://localhost:8000/docs")
        logger.info(f"🌍 Внешний доступ: {NGROK_URL}/docs")

        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info" if DEBUG else "warning")
        server = uvicorn.Server(config)
        await server.serve()

    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    finally:
        logger.info("🔌 Удаление webhook...")
        await bot.delete_webhook()
        logger.info("🔌 Остановка планировщика...")
        await link_scheduler.stop()
        logger.info("✅ Все сервисы остановлены")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Приложение остановлено пользователем")
