# Настройка Senler для интеграции с ботом

## Обязательные поля для webhook

### 1. **user_id** (обязательно)
- **Что это**: Telegram User ID пользователя (числовой)
- **Пример**: `1524374551`
- **Как получить в Senler**: 
  - В переменной `{{user.telegram_id}}` или `{{contact.telegram_id}}`
  - Или через переменную `{{user_id}}`

### 2. **token** (обязательно для возврата в воронку)
- **Что это**: Уникальный токен для возврата пользователя в Senler
- **Пример**: `"senler_abc123def456"`
- **Как генерировать в Senler**:
  - Можно использовать `{{contact.id}}` + случайную строку
  - Или создать переменную `{{return_token}}`

### 3. **username** (опционально)
- **Что это**: Telegram username пользователя (без @)
- **Пример**: `"kerxl"`
- **Как получить**: `{{user.telegram_username}}`

## Настройка webhook в Senler

### URL для webhook:
```
https://wikisound.store/senler/webhook
```

### Формат данных (JSON):
```json
{
  "user_id": {{user.telegram_id}},
  "username": "{{user.telegram_username}}",
  "token": "{{return_token}}"
}
```

### Пример настройки в Senler:

#### Вариант 1: С полными данными
```json
{
  "user_id": {{contact.telegram_id}},
  "username": "{{contact.telegram_username}}",
  "token": "senler_{{contact.id}}_{{timestamp}}"
}
```

#### Вариант 2: Минимальный (только user_id)
```json
{
  "user_id": {{user.telegram_id}}
}
```

## Автоматические fallback значения

Если поля отсутствуют или равны null, бот автоматически:

1. **user_id**: 
   - Ищет числовое значение длиной 8+ цифр в любом поле
   - Если не найдет - использует ID администратора для тестирования
   
2. **username**: 
   - Генерирует как `senler_user_{{user_id}}`
   
3. **token**: 
   - Генерирует как `senler_token_{{random}}_{{user_id}}`

## Тестирование webhook

### Локально (через ngrok):
```bash
curl -X POST https://your-ngrok-url.ngrok.io/senler/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1524374551,
    "username": "kerxl",
    "token": "test_token_123"
  }'
```

### Production:
```bash
curl -X POST https://wikisound.store/senler/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1524374551,
    "username": "kerxl", 
    "token": "test_token_123"
  }'
```

## Возврат пользователя в Senler

После завершения теста бот может вернуть пользователя в воронку через:

### Endpoint:
```
POST /senler/complete/{{user_id}}
```

### Пример:
```json
{
  "message": "Спасибо за прохождение теста! Ваши результаты готовы."
}
```

## Debug endpoint

Для отладки данных используйте:
```
POST /senler/debug
```

Он покажет все полученные данные и поможет настроить правильный формат.

## Часто возникающие проблемы

### 1. 422 Unprocessable Entity
- **Причина**: Неправильный формат данных
- **Решение**: Проверьте JSON синтаксис и типы данных

### 2. 400 Bad Request "Отсутствует user_id"
- **Причина**: Не передан или равен null
- **Решение**: Убедитесь что `{{user.telegram_id}}` доступен

### 3. Пользователь не получает сообщения
- **Причина**: Неправильный user_id или бот заблокирован
- **Решение**: Проверьте ID и убедитесь что пользователь не заблокировал бота

## Рекомендуемая настройка в Senler

```json
{
  "user_id": {{contact.telegram_id}},
  "username": "{{contact.telegram_username}}",
  "token": "return_{{contact.id}}_{{random_string}}"
}
```

Где:
- `{{contact.telegram_id}}` - Telegram ID пользователя
- `{{contact.telegram_username}}` - Telegram username  
- `{{random_string}}` - случайная строка для уникальности токена