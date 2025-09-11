# Получение user_id по username через Telegram Bot API

## Обзор

Реализован функционал для получения Telegram user_id по username через Telegram Bot API. Это позволяет Senler webhook работать даже если передается только username пользователя без user_id.

## Как это работает

### 1. Автоматическое определение user_id в webhook

Когда в Senler webhook приходят данные без user_id, система пытается определить его в следующем порядке:

1. **Поиск в полях данных** - ищет числовые значения похожие на Telegram user_id
2. **Получение через Telegram API** - использует username для получения user_id
3. **Генерация виртуального ID** - создает виртуальный user_id как fallback

### 2. Методы получения user_id через Telegram API

Функция `get_user_id_by_username()` использует два метода:

#### Метод 1: getChat
```python
response = await client.post(
    f"{telegram_api_url}/getChat",
    json={"chat_id": "@username"}
)
```
- Работает только если бот имел контакт с пользователем
- Самый надежный метод если доступен

#### Метод 2: sendMessage + deleteMessage  
```python
# Отправляем тестовое сообщение
response = await client.post(
    f"{telegram_api_url}/sendMessage", 
    json={"chat_id": "@username", "text": "test", "disable_notification": True}
)
# Сразу удаляем его
await client.post(
    f"{telegram_api_url}/deleteMessage",
    json={"chat_id": user_id, "message_id": message_id}
)
```
- Попытка отправки сообщения для получения chat_id из ответа
- Автоматически удаляет тестовое сообщение

## Интеграция с Senler webhook

### Обновленная логика webhook обработки

В `/senler/webhook` добавлена следующая логика:

```python
# Если user_id не найден и есть username - пытаемся получить через Telegram API
if not user_id and username:
    logger.info(f"🔍 Попытка получить user_id через Telegram API для username: @{username}")
    telegram_user_id = await senler_integration.get_user_id_by_username(username)
    if telegram_user_id:
        user_id = telegram_user_id
        logger.info(f"✅ Получен user_id через Telegram API: {user_id} для @{username}")
    else:
        logger.warning(f"❌ Не удалось получить user_id через Telegram API для @{username}")
```

### Поддерживаемые поля в Senler webhook

Система распознает следующие варианты полей:

**user_id:**
- `user_id`, `userid`, `telegram_user_id`, `tg_user_id`

**username:** 
- `username`, `user_name`, `telegram_username`

**token:**
- `token`, `senler_token`, `return_token`

## Тестирование

### Запуск тестов

```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Тестируем функцию получения user_id
python test_username_to_userid.py

# Тестируем webhook endpoints
./test_senler_webhook.sh
```

### Новые тестовые сценарии в webhook

Добавлены тесты для проверки получения user_id по username:

```bash
# Тест 8: Webhook с получением user_id по username
curl -X POST "$NGROK_URL/senler/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "kerxl",
    "token": "test_token_username_lookup"  
  }'

# Тест 9: Webhook только с username
curl -X POST "$NGROK_URL/senler/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_username": "kerxl"
  }'
```

## Ограничения Telegram Bot API

### Когда метод работает:
- ✅ Бот имел контакт с пользователем (пользователь писал боту)
- ✅ Пользователь не заблокировал бота
- ✅ Username существует и активен

### Когда метод НЕ работает:
- ❌ Пользователь никогда не общался с ботом
- ❌ Пользователь заблокировал бота  
- ❌ Пользователь изменил настройки приватности
- ❌ Username не существует или неактивен

### Fallback стратегия

Если получить user_id через API не удалось, система генерирует виртуальный ID:

```python
import hashlib
base_string = username or token or "fallback_default"
hash_object = hashlib.md5(base_string.encode())
user_id = 99000000 + int(hash_object.hexdigest()[:8], 16) % 999999
```

Виртуальные user_id начинаются с `99000000` для избежания конфликтов с реальными ID.

## Логирование и отладка

Система подробно логирует процесс получения user_id:

```
🔍 Ищем user_id для username: @kerxl
🔍 Метод 1: Пытаемся getChat для @kerxl  
✅ Найден user_id через getChat: 1524374551 для @kerxl
```

Или в случае неудачи:

```
🔍 Метод 1: Пытаемся getChat для @nonexistent
⚠️  getChat неуспешен: Chat not found
🔍 Метод 2: Пытаемся sendMessage для @nonexistent
⚠️  sendMessage неуспешен: Chat not found
❌ Не удалось получить user_id для @nonexistent через Telegram API
💡 Возможные причины:
   - Пользователь не существует
   - Пользователь заблокировал бота  
   - Бот не имел контакта с пользователем
   - Пользователь изменил настройки приватности
```

## Настройка в Senler

### Рекомендуемая конфигурация webhook в Senler:

**Если есть возможность передавать user_id:**
```json
{
    "user_id": "{{telegram_user_id}}",
    "username": "{{telegram_username}}",
    "token": "{{unique_token}}"
}
```

**Если user_id недоступен:**
```json
{
    "username": "{{telegram_username}}",  
    "token": "{{unique_token}}"
}
```

### Поля для webhook URL

В Senler настройте webhook для отправки на:
```
https://ваш_домен.com/senler/webhook
```

С телом запроса содержащим максимум доступной информации о пользователе.

## Преимущества решения

1. **Гибкость** - работает с различными комбинациями входных данных
2. **Надежность** - несколько методов получения user_id с fallback
3. **Детальное логирование** - легко отлаживать проблемы
4. **Совместимость** - поддерживает различные варианты названий полей
5. **Fallback стратегия** - всегда генерирует какой-то user_id для продолжения работы

## Мониторинг

Рекомендуется мониторить логи для:
- Частота успешных получений user_id через API
- Количество fallback на виртуальные ID  
- Ошибки API и их причины
- Производительность запросов к Telegram API

Это поможет оптимизировать настройки Senler для передачи максимума нужной информации.