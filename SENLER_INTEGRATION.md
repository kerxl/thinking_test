# Интеграция с Senler

## Обзор

Проект Mind Style Bot теперь поддерживает интеграцию с Senler - платформой маркетинговой автоматизации. Это позволяет запускать тесты из воронок Senler и возвращать пользователей обратно после завершения.

## Архитектура интеграции

### Компоненты

1. **FastAPI сервер** (`src/api/server.py`) - обработка webhook запросов от Senler
2. **Senler Integration** (`src/integration/senler.py`) - бизнес-логика интеграции
3. **Обновленная модель User** - поля для хранения Senler данных
4. **Модифицированное завершение тестов** - автоматический возврат в Senler

### Поля базы данных

Добавлены новые поля в таблицу `users`:
- `senler_token` - токен для возврата пользователя в Senler  
- `senler_user_id` - ID пользователя в системе Senler (опционально)
- `from_senler` - флаг, указывающий что пользователь пришел из Senler

## API Endpoints

### 1. Webhook для инициализации теста

**POST** `/senler/webhook`

Принимает запрос от Senler для запуска теста.

**Тело запроса:**
```json
{
    "user_id": 123456789,
    "username": "test_user", 
    "token": "senler_token_12345",
    "senler_user_id": "optional_senler_id"
}
```

**Ответ:**
```json
{
    "success": true,
    "message": "Пользователь успешно инициализирован",
    "user_id": 123456789
}
```

**Что происходит:**
1. Создается или обновляется запись пользователя в БД
2. Сохраняется Senler token и флаг from_senler = true
3. Отправляется стартовое сообщение пользователю в Telegram

### 2. Завершение теста и возврат в Senler

**POST** `/senler/complete/{user_id}`

Завершает тест и возвращает пользователя в Senler.

**Параметры:**
- `user_id` - Telegram ID пользователя
- `message` (опционально) - сообщение для пользователя

**Ответ:**
```json
{
    "success": true,
    "message": "Пользователь успешно возвращен в Senler"
}
```

### 3. Служебные endpoints

**GET** `/` - проверка работы API  
**GET** `/health` - health check

## Настройка и запуск

### 1. Миграция базы данных

Выполните SQL миграцию для добавления новых полей:

```bash
source venv/bin/activate
psql postgresql://postgres:postgres@localhost/mind_style -f database/add_senler_fields.sql
```

### 2. Переменные окружения

Добавьте в `.env`:

```bash
# Senler интеграция
API_HOST=0.0.0.0
API_PORT=8000
WEBHOOK_URL=http://your-domain.com/senler/webhook
```

### 3. Варианты запуска

#### Только API сервер
```bash
source venv/bin/activate
python src/run_api_only.py
```

#### Бот + API сервер вместе
```bash
source venv/bin/activate  
python src/run_with_api.py
```

#### Обычный бот (без API)
```bash
source venv/bin/activate
python src/bot/main.py
```

## Настройка в Senler

1. Создайте воронку в Senler
2. На последнем шаге добавьте кнопку "Начать тест"
3. Настройте webhook на URL: `http://your-domain.com/senler/webhook`
4. Передавайте параметры:
   - `user_id` - Telegram ID пользователя
   - `username` - Telegram username
   - `token` - уникальный токен для возврата пользователя

## Логика работы

### Инициализация из Senler

1. Senler отправляет webhook запрос с данными пользователя
2. API создает/обновляет пользователя в БД с флагом `from_senler=true`
3. Пользователю отправляется стартовое сообщение через Telegram API
4. Пользователь проходит тесты обычным образом

### Завершение тестов

При завершении всех тестов:

1. Если `user.from_senler == true` - показываются результаты
2. Отправляется финальное сообщение 
3. Пользователь автоматически "возвращается" в Senler
4. Кнопка "Начать заново" не показывается

### Обычные пользователи

Пользователи, пришедшие не из Senler (`from_senler=false`):
- Проходят тесты обычным образом
- После завершения видят кнопку "Начать заново"
- Остаются в боте

## Тестирование

### Тест webhook endpoint

```bash
curl -X POST http://localhost:8000/senler/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "username": "test_user",
    "token": "test_token_12345"
  }'
```

### Тест завершения

```bash
curl -X POST http://localhost:8000/senler/complete/123456789 \
  -H "Content-Type: application/json" \
  -d '{"message": "Тест завершен!"}'
```

## Логирование

Все действия интеграции логируются:
- Получение webhook запросов
- Создание/обновление пользователей  
- Отправка сообщений
- Ошибки API

Логи доступны в консоли при запуске сервера.

## Безопасность

- API не требует аутентификации (настройте в Senler безопасную передачу данных)
- Токены Senler сохраняются в БД для возврата пользователя
- Все данные передаются через HTTPS в продакшене

## Масштабирование

- API сервер может работать независимо от Telegram бота
- Поддержка работы в Docker контейнерах
- Готов к развертыванию на облачных платформах

## Поддержка

При возникновении проблем проверьте:
1. Доступность базы данных  
2. Корректность Senler webhook URL
3. Валидность Bot Token для Telegram API
4. Логи API сервера для диагностики ошибок