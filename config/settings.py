import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/mind_style")
DEBUG = os.getenv("DEBUG", "True") == "True"

ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
