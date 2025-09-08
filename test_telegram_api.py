#!/usr/bin/env python3
"""
Тест подключения к Telegram Bot API
"""

import asyncio
import httpx
import sys
import os

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import BOT_TOKEN

async def test_telegram_api():
    """Тестирует подключение к Telegram Bot API"""
    
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    print(f"🔑 Тестируем токен: {BOT_TOKEN[:10]}...")
    print(f"🌐 API URL: {api_url}")
    
    timeout = httpx.Timeout(30.0, connect=10.0)
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            print("\n📡 Тест 1: getMe (информация о боте)")
            response = await client.get(f"{api_url}/getMe")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Бот найден: {data['result']['first_name']} (@{data['result']['username']})")
                print(f"🤖 ID бота: {data['result']['id']}")
                print(f"📋 Может читать все сообщения: {data['result']['can_read_all_group_messages']}")
            else:
                print(f"❌ Ошибка getMe: HTTP {response.status_code}")
                print(f"📄 Ответ: {response.text}")
                return False
            
            print("\n📡 Тест 2: getWebhookInfo (информация о webhook)")
            response = await client.get(f"{api_url}/getWebhookInfo")
            
            if response.status_code == 200:
                data = response.json()
                webhook_url = data['result'].get('url', 'Не установлен')
                pending_updates = data['result'].get('pending_update_count', 0)
                print(f"🔗 Текущий webhook: {webhook_url}")
                print(f"📬 Ожидающие обновления: {pending_updates}")
                
                if pending_updates > 0:
                    print(f"⚠️  Есть необработанные обновления: {pending_updates}")
            else:
                print(f"❌ Ошибка getWebhookInfo: HTTP {response.status_code}")
                print(f"📄 Ответ: {response.text}")
                
            print("\n🎯 Тест завершен успешно!")
            return True
            
    except httpx.ConnectTimeout:
        print("❌ Таймаут подключения к Telegram API")
        print("💡 Возможные причины:")
        print("   - Проблемы с интернет-соединением")
        print("   - Блокировка Telegram API провайдером")
        print("   - Неправильный токен бота")
        return False
    except httpx.ReadTimeout:
        print("❌ Таймаут чтения ответа от Telegram API")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Тестирование подключения к Telegram Bot API\n")
    result = asyncio.run(test_telegram_api())
    
    if result:
        print("\n✅ Все тесты прошли успешно!")
        print("💡 Telegram API доступен и токен корректный")
    else:
        print("\n❌ Тесты не пройдены!")
        print("💡 Проверьте интернет-соединение и токен бота")
        sys.exit(1)