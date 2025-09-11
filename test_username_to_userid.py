#!/usr/bin/env python3
"""
Скрипт для тестирования функции получения user_id через Telegram Bot API по username
"""

import asyncio
import logging
import sys
import os

# Добавляем корневую директорию проекта в Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.integration.senler import senler_integration

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_username_to_userid():
    """
    Тестирует функцию получения user_id по username
    """
    print("🧪 Тестирование получения user_id через Telegram Bot API")
    print("=" * 60)
    
    # Список тестовых username для проверки
    test_usernames = [
        "kerxl",           # Реальный username
        "@kerxl",          # С @ в начале
        "nonexistent_user_12345",  # Несуществующий username
        "",                # Пустой username
        None,              # None username
    ]
    
    for i, username in enumerate(test_usernames, 1):
        print(f"\n📋 Тест {i}: username = '{username}'")
        print("-" * 40)
        
        try:
            user_id = await senler_integration.get_user_id_by_username(username)
            
            if user_id:
                print(f"✅ Успех! user_id = {user_id}")
            else:
                print(f"❌ user_id не найден для '{username}'")
                
        except Exception as e:
            print(f"🔥 Ошибка: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Тестирование завершено")

async def test_webhook_integration():
    """
    Тестирует интеграцию с webhook обработчиком
    """
    print("\n🔗 Тестирование интеграции с webhook")
    print("=" * 60)
    
    # Тестируем обработку webhook запроса только с username
    test_data = {
        "username": "kerxl",
        "token": "test_token_integration"
    }
    
    print(f"📤 Тестовые данные: {test_data}")
    
    try:
        # Имитируем обработку webhook запроса
        user_id = None
        username = test_data.get("username")
        token = test_data.get("token")
        
        print(f"🔍 Попытка получить user_id для username: {username}")
        
        if not user_id and username:
            telegram_user_id = await senler_integration.get_user_id_by_username(username)
            if telegram_user_id:
                user_id = telegram_user_id
                print(f"✅ Получен user_id через Telegram API: {user_id}")
            else:
                print(f"❌ Не удалось получить user_id через Telegram API")
                
                # Генерируем виртуальный user_id как fallback
                import hashlib
                base_string = username or token or "fallback_test"
                hash_object = hashlib.md5(base_string.encode())
                user_id = 99000000 + int(hash_object.hexdigest()[:8], 16) % 999999
                print(f"🔧 Сгенерирован виртуальный user_id: {user_id}")
        
        print(f"🎯 Итоговый user_id: {user_id}")
        
    except Exception as e:
        print(f"🔥 Ошибка тестирования интеграции: {e}")
    
    print("=" * 60)

async def main():
    """
    Основная функция тестирования
    """
    print("🚀 Запуск тестов получения user_id по username")
    
    await test_username_to_userid()
    await test_webhook_integration()
    
    print("\n🎉 Все тесты завершены!")

if __name__ == "__main__":
    # Проверяем наличие необходимых переменных окружения
    from config.settings import BOT_TOKEN
    
    if not BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не установлен в переменных окружения")
        print("💡 Создайте файл .env с BOT_TOKEN=ваш_токен_бота")
        sys.exit(1)
    
    print(f"✅ BOT_TOKEN найден: {BOT_TOKEN[:10]}...")
    
    # Запускаем тесты
    asyncio.run(main())