import asyncio
import json
import logging

# ignore
from . import handler
from . import callback
from . import proccesser

from config.const import TaskEntity, MESSAGES
from config.settings import DEBUG
from src.database.operations import init_db
from .globals import bot, dp, task_manager

logging.basicConfig(
    level=logging.INFO if DEBUG else logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    await init_db()
    await TaskEntity.priorities.value.load_questions()
    await TaskEntity.inq.value.load_questions()
    await TaskEntity.epi.value.load_questions()

    logger.info("🤖 Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    with open("config/constants.json", "r", encoding="utf-8") as json_file:
        MESSAGES.update(json.load(json_file))
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
