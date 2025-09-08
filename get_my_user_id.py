#!/usr/bin/env python3
"""
Простой скрипт для получения вашего Telegram User ID
"""

import asyncio
import httpx
from config.settings import BOT_TOKEN


async def get_bot_updates():
    """Получает последние обновления бота для определения User ID"""
    
    try:
        async with httpx.AsyncClient() as client:
            telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            
            response = await client.get(telegram_api_url, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("result"):
                    print("📱 Найдены следующие пользователи:")
                    print("=" * 50)
                    
                    user_ids = set()
                    for update in data["result"]:
                        if "message" in update and "from" in update["message"]:
                            user = update["message"]["from"]
                            user_id = user["id"]
                            username = user.get("username", "Нет username")
                            first_name = user.get("first_name", "")
                            
                            if user_id not in user_ids:
                                user_ids.add(user_id)
                                print(f"👤 User ID: {user_id}")
                                print(f"   Имя: {first_name}")
                                print(f"   Username: @{username}")
                                print(f"   Для тестирования: python test_senler_webhook.py {user_id}")
                                print("-" * 30)
                    
                    if not user_ids:
                        print("❌ Пользователи не найдены в истории сообщений")
                        print("💡 Отправьте любое сообщение боту и запустите скрипт снова")
                        
                else:
                    print("❌ Нет обновлений от бота")
                    print("💡 Отправьте /start боту и запустите скрипт снова")
                    
            else:
                print(f"❌ Ошибка API: {response.json()}")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def main():
    print("🔍 Поиск вашего Telegram User ID...")
    print("💡 Если не найдется - сначала напишите боту /start")
    print("=" * 50)
    
    await get_bot_updates()


if __name__ == "__main__":
    asyncio.run(main())