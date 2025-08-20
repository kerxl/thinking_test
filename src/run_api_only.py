"""
Запуск только FastAPI сервера для Senler интеграции
"""
import uvicorn
import sys
import os

# Добавляем путь к корню проекта для корректных импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.server import app
from config.settings import DEBUG

if __name__ == "__main__":
    if DEBUG:
        uvicorn.run(
            "src.api.server:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True
        )
    else:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="warning"
        )