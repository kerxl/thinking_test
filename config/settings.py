import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://root:password@localhost/mind_style_bot")
DEBUG = os.getenv("DEBUG", "True") == "True"

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

# Настройки для Senler интеграции
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000/senler/webhook")
# SENLER_FUNNEL_URL - НЕ ИСПОЛЬЗУЕТСЯ (Senler сам перехватывает /start)
# SENLER_FUNNEL_URL = os.getenv("SENLER_FUNNEL_URL", "https://your-senler-funnel-url.com")
