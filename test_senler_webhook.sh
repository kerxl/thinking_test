#!/bin/bash

# Скрипт для тестирования Senler webhook endpoint

NGROK_URL="https://3095393d4deb.ngrok-free.app"  # Замените на ваш ngrok URL
# Или для локального тестирования:
# LOCAL_URL="http://localhost:8000"

echo "🧪 Тестирование Senler webhook endpoints"
echo "📡 URL: $NGROK_URL"

# Замените YOUR_USER_ID на ваш реальный Telegram user ID
YOUR_USER_ID="1524374551"

echo
echo "📋 Тест 1: Debug endpoint (JSON данные)"
curl -X POST "$NGROK_URL/senler/debug" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": '$YOUR_USER_ID',
    "username": "kerxl",
    "token": "test_token_123"
  }' | jq .

echo
echo "📋 Тест 2: Debug endpoint (Form данные)"
curl -X POST "$NGROK_URL/senler/debug" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "user_id=$YOUR_USER_ID&username=kerxl&token=test_token_123" | jq .

echo
echo "📋 Тест 3: Основной webhook (JSON)"
curl -X POST "$NGROK_URL/senler/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": '$YOUR_USER_ID',
    "username": "kerxl",
    "token": "test_token_123"
  }' | jq .

echo
echo "📋 Тест 4: Webhook с различными именами полей"
curl -X POST "$NGROK_URL/senler/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_user_id": '$YOUR_USER_ID',
    "telegram_username": "kerxl",
    "return_token": "test_token_456"
  }' | jq .

echo
echo "📋 Тест 5: Webhook с null значениями (тестируем автогенерацию)"
curl -X POST "$NGROK_URL/senler/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": null,
    "username": null,
    "token": null
  }' | jq .

echo
echo "📋 Тест 6: Webhook только с user_id"
curl -X POST "$NGROK_URL/senler/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": '$YOUR_USER_ID'
  }' | jq .

echo
echo "📋 Тест 7: Webhook с автоопределением user_id"
curl -X POST "$NGROK_URL/senler/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": '$YOUR_USER_ID',
    "some_field": "test",
    "another_id": 123
  }' | jq .

echo
echo "📋 Тест 8: Webhook с получением user_id по username"
curl -X POST "$NGROK_URL/senler/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "kerxl",
    "token": "test_token_username_lookup"
  }' | jq .

echo
echo "📋 Тест 9: Webhook только с username (тестируем полную цепочку)"
curl -X POST "$NGROK_URL/senler/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_username": "kerxl"
  }' | jq .

echo
echo "📋 Тест 10: Установка контакта с пользователем"
curl -X POST "$NGROK_URL/senler/establish-contact" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "kerxl"
  }' | jq .

echo
echo "✅ Тесты завершены"
echo "💡 Проверьте логи сервера для деталей"
echo "📖 См. SENLER_SETUP.md для инструкций по настройке Senler"