#!/usr/bin/env python3
"""
Скрипт для проверки готовности системы к запуску
"""

import asyncio
import sys
from pathlib import Path


def check_python_version():
    """Проверка версии Python"""
    print("🔍 Проверка версии Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - требуется Python 3.9+")
        return False


def check_env_file():
    """Проверка файла .env"""
    print("\n🔍 Проверка файла .env...")
    env_path = Path(".env")

    if not env_path.exists():
        print("❌ Файл .env не найден")
        return False

    required_vars = ["BOT_TOKEN", "DATABASE_URL", "ADMIN_USER_ID"]
    missing_vars = []

    with open(env_path, "r") as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content:
                missing_vars.append(var)

    if missing_vars:
        print(f"❌ Отсутствуют переменные в .env: {', '.join(missing_vars)}")
        return False

    print("✅ Файл .env настроен корректно")
    return True


def check_required_files():
    """Проверка наличия обязательных файлов"""
    print("\n🔍 Проверка обязательных файлов...")

    required_files = [
        "requirements.txt",
        "config/constants.json",
        "questions/first_task.json",
        "questions/second_task.json",
        "questions/third_task.json",
        "src/bot/main.py",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        return False

    print("✅ Все обязательные файлы найдены")
    return True


def check_dependencies():
    """Проверка установленных зависимостей"""
    print("\n🔍 Проверка зависимостей...")

    required_packages = ["aiogram", "sqlalchemy", "asyncpg", "dotenv", "aiofiles"]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
        print("Установите их командой: pip install -r requirements.txt")
        return False

    print("✅ Все зависимости установлены")
    return True


async def check_database_connection():
    """Проверка подключения к базе данных"""
    print("\n🔍 Проверка подключения к базе данных...")

    try:
        from src.database.operations import init_db

        await init_db()
        print("✅ Подключение к базе данных успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False


async def check_questions_loading():
    """Проверка загрузки вопросов"""
    print("\n🔍 Проверка загрузки вопросов...")

    try:
        from config.const import TaskEntity

        await TaskEntity.priorities.value.load_questions()
        await TaskEntity.inq.value.load_questions()
        await TaskEntity.epi.value.load_questions()

        # Проверяем что вопросы действительно загрузились
        priorities_loaded = TaskEntity.priorities.value.loaded
        inq_loaded = TaskEntity.inq.value.loaded
        epi_loaded = TaskEntity.epi.value.loaded

        if priorities_loaded and inq_loaded and epi_loaded:
            print("✅ Все вопросы загружены успешно")

            # Проверяем количество вопросов
            inq_count = TaskEntity.inq.value.get_total_questions()
            epi_count = TaskEntity.epi.value.get_total_questions()

            print(f"📊 Загружено INQ вопросов: {inq_count}")
            print(f"📊 Загружено EPI вопросов: {epi_count}")
            return True
        else:
            print("❌ Не все вопросы загружены")
            return False

    except Exception as e:
        print(f"❌ Ошибка загрузки вопросов: {e}")
        return False


def check_bot_token():
    """Проверка токена бота"""
    print("\n🔍 Проверка токена бота...")

    try:
        from config.settings import BOT_TOKEN

        if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ BOT_TOKEN не настроен в .env файле")
            return False

        # Проверяем формат токена (должен быть как 123456:ABC-DEF...)
        if ":" not in BOT_TOKEN:
            print("❌ Неверный формат BOT_TOKEN")
            return False

        print("✅ BOT_TOKEN настроен корректно")
        return True

    except Exception as e:
        print(f"❌ Ошибка при проверке токена: {e}")
        return False


async def run_full_check():
    """Запуск полной проверки системы"""
    print("🚀 Запуск проверки готовности системы к работе...\n")

    checks = [
        ("Python версия", check_python_version()),
        ("Файл .env", check_env_file()),
        ("Обязательные файлы", check_required_files()),
        ("Зависимости", check_dependencies()),
        ("Токен бота", check_bot_token()),
        ("База данных", await check_database_connection()),
        ("Загрузка вопросов", await check_questions_loading()),
    ]

    passed_checks = 0
    total_checks = len(checks)

    for check_name, result in checks:
        if isinstance(result, bool):
            if result:
                passed_checks += 1
        else:
            # Для синхронных функций
            if result:
                passed_checks += 1

    print(f"\n{'='*50}")
    print(f"📋 РЕЗУЛЬТАТ ПРОВЕРКИ: {passed_checks}/{total_checks} тестов пройдено")

    if passed_checks == total_checks:
        print("🎉 Система готова к запуску!")
        print("\nДля запуска бота используйте:")
        print("python src/bot/main.py")
        return True
    else:
        print("⚠️  Система НЕ готова к запуску")
        print("Исправьте ошибки выше и запустите проверку снова")
        return False


if __name__ == "__main__":
    # Убеждаемся что запускаем из правильной директории
    if not Path("src/bot/main.py").exists():
        print("❌ Запустите скрипт из корневой директории проекта (06.08/)")
        sys.exit(1)

    try:
        result = asyncio.run(run_full_check())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Проверка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
