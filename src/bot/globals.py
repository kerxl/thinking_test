"""
Глобальные переменные для бота
"""

from aiogram import Bot
from aiogram.enums import ParseMode
from config.const import dp
from config.settings import BOT_TOKEN
from src.core.task_manager import TaskManager

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
task_manager = TaskManager()
