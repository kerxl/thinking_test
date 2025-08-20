# 🚀 Quick Start: Деплой Mind Style Bot + Senler

## Для заказчика: Быстрый старт

### Шаг 1: Подготовка сервера (5 минут)

```bash
# Клонируйте проект на сервер
git clone <repository-url> /opt/mind_style_bot
cd /opt/mind_style_bot

# Установите системные зависимости (Ubuntu/Debian)
sudo apt update && sudo apt install -y python3 python3-venv postgresql nginx certbot python3-certbot-nginx

# Или для CentOS/RHEL:
# sudo yum install -y python3 python3-venv postgresql-server nginx certbot python3-certbot-nginx
```

### Шаг 2: Автоматический деплой (10 минут)

```bash
# Запустите автоматический скрипт деплоя
chmod +x deploy.sh

# Установите переменные окружения и запустите
export DOMAIN="your-bot-domain.com"
export BOT_TOKEN="your_telegram_bot_token"  # Получить у @BotFather
export DB_PASSWORD="your_secure_db_password"
export ADMIN_USER_ID="your_telegram_user_id"

./deploy.sh
```

**Скрипт автоматически:**
- Создаст виртуальное окружение
- Установит зависимости Python  
- Настроит PostgreSQL
- Создаст systemd сервисы
- Настроит Nginx с SSL
- Запустит API сервер + Telegram бота

### Шаг 3: Проверка деплоя (2 минуты)

```bash
# Проверка статуса
./check_status.sh

# Проверка API
curl https://your-domain.com/health
# Ответ: {"status":"healthy","service":"mind_style_bot_api"}
```

## Для заказчика: Настройка Senler (15 минут)

### 1. Создание Telegram бота

1. Найдите **@BotFather** в Telegram
2. Отправьте `/newbot`
3. Укажите название: `Mind Style Test Bot`
4. Укажите username: `@your_mindstyle_bot`
5. **Скопируйте токен** и обновите в `.env` файле

### 2. Регистрация в Senler

1. Перейдите на https://senler.ru/
2. Зарегистрируйтесь (бесплатно до 40 сообщений/день)
3. **Подключите бота**: Настройки → Telegram → добавить токен

### 3. Создание воронки

**Создайте сценарий "Тест стилей мышления":**

1. **Сообщение 1**: Приветствие + кнопка "Узнать подробнее"
2. **Сообщение 2**: Описание тестов + кнопка "Начать тестирование"  
3. **Сообщение 3**: Переход к тесту + **кнопка "🚀 НАЧАТЬ ТЕСТ"**

### 4. Настройка webhook кнопки

Для кнопки **"🚀 НАЧАТЬ ТЕСТ"**:

- **Тип действия**: HTTP запрос
- **URL**: `https://your-domain.com/senler/webhook`
- **Метод**: POST
- **Headers**: `Content-Type: application/json`
- **Тело запроса**:
```json
{
    "user_id": "{{contact.telegram_id}}",
    "username": "{{contact.telegram_username}}",
    "token": "{{contact.senler_token}}"
}
```

## Тестирование (5 минут)

### Быстрый тест

1. **Найдите бота** в Telegram (@your_mindstyle_bot)
2. **Отправьте** `/start` 
3. **Пройдите воронку** до кнопки тестирования
4. **Нажмите "🚀 НАЧАТЬ ТЕСТ"**
5. **Пройдите тесты** полностью

**Ожидается:**
- ✅ Получение нового сообщения от бота (вне Senler)
- ✅ Прохождение всех 3 тестов
- ✅ Показ результатов + автоматический "возврат" в Senler

### Проверка данных

```bash
# На сервере проверьте, что пользователь создался
sudo -u postgres psql mind_style -c "SELECT user_id, username, from_senler FROM users WHERE from_senler = true;"
```

## Управление системой

```bash
# Проверка статуса
./check_status.sh

# Просмотр логов
./view_logs.sh

# Обновление кода
./update_bot.sh

# Перезапуск
sudo systemctl restart mindbot-api
```

## Структура файлов проекта

```
/opt/mind_style_bot/
├── deploy.sh              # Автоматический деплой
├── check_status.sh         # Проверка статуса
├── view_logs.sh           # Просмотр логов  
├── update_bot.sh          # Обновление
├── .env                   # Конфигурация (создается при деплое)
├── src/
│   ├── api/server.py      # FastAPI сервер для Senler
│   ├── bot/main.py        # Telegram бот
│   ├── integration/senler.py # Логика Senler интеграции
│   └── run_with_api.py    # Запуск бот + API вместе
└── database/
    └── add_senler_fields.sql # SQL миграция для Senler
```

## Полная документация

- **DEPLOYMENT_GUIDE.md** - Подробные инструкции по деплою
- **SENLER_INTEGRATION.md** - Техническая документация Senler API
- **TESTING_GUIDE.md** - Полное руководство по тестированию

## Поддержка

**При проблемах:**

1. Проверьте логи: `./view_logs.sh`
2. Проверьте статус: `./check_status.sh`
3. Перезапустите: `sudo systemctl restart mindbot-api`
4. Проверьте API: `curl https://your-domain.com/health`

**Важные URL:**
- Health check: `https://your-domain.com/health`
- Senler webhook: `https://your-domain.com/senler/webhook`  
- API docs: `https://your-domain.com/docs`

---

## 🎯 После выполнения всех шагов:

✅ **Mind Style Bot** готов принимать пользователей из Senler  
✅ **API сервер** обрабатывает webhook запросы  
✅ **Полный цикл** тестирования работает  
✅ **Автоматический возврат** в Senler после завершения

**Система готова к продакшену!** 🚀