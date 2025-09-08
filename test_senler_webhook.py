#!/usr/bin/env python3
"""
Скрипт для локального тестирования Senler webhook интеграции
"""

import asyncio
import httpx
import sys
from config.settings import BOT_TOKEN

# Настройки для тестирования
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = 123456789  # Замените на ваш реальный Telegram ID для тестирования
TEST_USERNAME = "test_user"
TEST_SENLER_TOKEN = "test_senler_token_12345"


async def test_senler_webhook():
    """Тестирует webhook endpoint /senler/webhook"""
    
    print("🧪 Тестируем Senler webhook интеграцию...")
    print(f"📡 API URL: {API_BASE_URL}")
    print(f"👤 Test User ID: {TEST_USER_ID}")
    print(f"🎫 Senler Token: {TEST_SENLER_TOKEN}")
    print("=" * 50)
    
    webhook_data = {
        "user_id": TEST_USER_ID,
        "username": TEST_USERNAME,
        "token": TEST_SENLER_TOKEN,
        "senler_user_id": "senler_123"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Отправляем webhook запрос
            print("📤 Отправляем webhook запрос...")
            response = await client.post(
                f"{API_BASE_URL}/senler/webhook",
                json=webhook_data,
                timeout=10.0
            )
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📋 Response: {response.json()}")
            
            if response.status_code == 200:
                print("✅ Webhook запрос успешно обработан!")
                print("\n🤖 Теперь откройте Telegram и найдите бота.")
                print("📱 Должно прийти стартовое сообщение с кнопкой 'Начать'")
                print("🎯 Нажмите кнопку и проверьте, что тест запускается корректно")
            else:
                print(f"❌ Ошибка webhook: {response.text}")
                
    except httpx.ConnectError:
        print("❌ Не удалось подключиться к API серверу!")
        print("💡 Убедитесь, что API сервер запущен: make run-with-api")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def test_api_health():
    """Проверяет доступность API сервера"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API сервер работает: {data}")
                return True
            else:
                print(f"⚠️ API сервер вернул код {response.status_code}")
                return False
    except httpx.ConnectError:
        print("❌ API сервер недоступен на localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки API: {e}")
        return False


async def send_direct_telegram_message():
    """Отправляет прямое сообщение через Telegram API для сравнения"""
    print("\n🔄 Отправляем прямое сообщение через Telegram API...")
    
    try:
        async with httpx.AsyncClient() as client:
            telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            
            message_data = {
                "chat_id": TEST_USER_ID,
                "text": "🧪 <b>Тестовое сообщение</b>\n\nЭто прямое сообщение от бота для проверки связи.",
                "parse_mode": "HTML"
            }
            
            response = await client.post(telegram_api_url, json=message_data, timeout=10.0)
            
            if response.status_code == 200:
                print("✅ Прямое сообщение отправлено успешно!")
            else:
                print(f"❌ Ошибка отправки: {response.json()}")
                
    except Exception as e:
        print(f"❌ Ошибка Telegram API: {e}")


async def main():
    """Главная функция тестирования"""
    print("🚀 Запуск тестирования Senler интеграции")
    print("=" * 50)
    
    # 1. Проверяем доступность API
    print("1️⃣ Проверяем доступность API сервера...")
    api_available = await test_api_health()
    
    if not api_available:
        print("\n💡 Для запуска API сервера используйте:")
        print("   make run-with-api")
        print("   или")
        print("   python src/run_with_api.py")
        return
    
    print("\n" + "=" * 50)
    
    # 2. Тестируем webhook
    print("2️⃣ Тестируем Senler webhook...")
    await test_senler_webhook()
    
    print("\n" + "=" * 50)
    
    # 3. Отправляем прямое сообщение для сравнения
    print("3️⃣ Отправляем прямое сообщение для проверки...")
    await send_direct_telegram_message()
    
    print("\n" + "=" * 50)
    print("✨ Тестирование завершено!")
    print("\n📝 Что проверить в Telegram:")
    print("   1. Получили ли вы стартовое сообщение с кнопкой 'Начать'?")
    print("   2. При нажатии кнопки 'Начать тест' - запускается ли тест приоритетов?")
    print("   3. Или сразу показывается сообщение о завершении?")


if __name__ == "__main__":
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == "--user-id" and len(sys.argv) > 2:
            TEST_USER_ID = int(sys.argv[2])
        elif sys.argv[1].isdigit():
            TEST_USER_ID = int(sys.argv[1])
    
    print(f"🔧 Используется User ID: {TEST_USER_ID}")
    print("💡 Для изменения User ID: python test_senler_webhook.py YOUR_USER_ID")
    print()
    
    asyncio.run(main())