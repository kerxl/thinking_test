import asyncio
import json
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config.const import TaskEntity
from config.settings import DEBUG, BOT_TOKEN
from src.database.operations import init_db

logging.basicConfig(
    level=logging.INFO if DEBUG else logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def main():
    await init_db()
    await TaskEntity.priorities.value.load_questions()
    await TaskEntity.inq.value.load_questions()
    await TaskEntity.epi.value.load_questions()

    logger.info("🤖 Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    with open("config/constants.json", "r", encoding="utf-8") as json_file:
        MESSAGES = json.load(json_file)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
