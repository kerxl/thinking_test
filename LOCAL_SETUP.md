# Инструкция по локальному запуску бота

## Требования к системе

- Ubuntu 22.04 (или совместимая Linux система)
- Python 3.9+
- PostgreSQL 12+
- Git

## Подготовка окружения

### 1. Клонирование проекта

```bash
cd ~/
git clone <your-repo-url> tg_bot_project
cd tg_bot_project/06.08
```

### 2. Создание и активация виртуального окружения

```bash
# Создание виртуального окружения
python3 -m venv venv

# Активация окружения
source venv/bin/activate

# Для деактивации (когда закончите работу)
# deactivate
```

### 3. Установка зависимостей

```bash
# Обновляем pip
pip install --upgrade pip

# Устанавливаем зависимости проекта
pip install -r requirements.txt
```

## Настройка базы данных PostgreSQL

### 1. Установка PostgreSQL (если не установлен)

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### 2. Создание базы данных

```bash
# Переключаемся на пользователя postgres
sudo -u postgres psql

# В консоли PostgreSQL создаем базу данных
CREATE DATABASE mind_style;
GRANT ALL PRIVILEGES ON DATABASE mind_style TO postgres;
\q
```

### 3. Настройка подключения

Отредактируйте файл `.env` в корневой директории проекта:

```bash
# Откройте файл в редакторе
nano .env
```

Содержимое файла `.env`:

```env
# Telegram Bot Configuration
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/mind_style

# Application Settings
DEBUG=True
ADMIN_USER_ID=YOUR_TELEGRAM_USER_ID

# Optional: для продакшена
# DEBUG=False
```

## Получение Telegram Bot Token

### 1. Создание бота

1. Найдите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в файл `.env`

### 2. Получение вашего User ID

1. Найдите @userinfobot в Telegram
2. Отправьте команду `/start`
3. Скопируйте ваш User ID в файл `.env` как ADMIN_USER_ID

## Проверка конфигурации

### 1. Проверка подключения к базе данных

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Проверьте подключение
python -c "
import asyncio
from src.database.operations import init_db

async def test_db():
    try:
        await init_db()
        print('✅ База данных настроена успешно')
    except Exception as e:
        print(f'❌ Ошибка подключения к БД: {e}')

asyncio.run(test_db())
"
```

### 2. Проверка загрузки вопросов

```bash
python -c "
import asyncio
from config.const import TaskEntity

async def test_questions():
    try:
        await TaskEntity.priorities.value.load_questions()
        await TaskEntity.inq.value.load_questions()
        await TaskEntity.epi.value.load_questions()
        print('✅ Все вопросы загружены успешно')
    except Exception as e:
        print(f'❌ Ошибка загрузки вопросов: {e}')

asyncio.run(test_questions())
"
```

## Запуск бота

### 1. Запуск в режиме разработки

```bash
# Убедитесь что виртуальное окружение активировано
source venv/bin/activate

# Запустите бота
python src/bot/main.py
```

Вы должны увидеть сообщение:
```
🤖 Бот запущен
```

### 2. Проверка работы

1. Найдите вашего бота в Telegram по имени пользователя
2. Отправьте команду `/start`
3. Бот должен ответить приветственным сообщением с кнопкой "🚀 Начать тест"

## Запуск тестов

### 1. Установка дополнительных зависимостей для тестирования

```bash
# Зависимости уже включены в requirements.txt
# Если нужно установить отдельно:
# pip install pytest pytest-asyncio pytest-mock
```

### 2. Запуск всех тестов

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Запустите все тесты
pytest

# Запуск с подробным выводом
pytest -v

# Запуск конкретного файла тестов
pytest tests/test_task_manager.py

# Запуск с покрытием кода (если установлен pytest-cov)
pytest --cov=src
```

### 3. Запуск отдельных типов тестов

```bash
# Только unit тесты
pytest -m unit

# Только интеграционные тесты
pytest -m integration

# Быстрые тесты (исключая медленные)
pytest -m "not slow"
```

## Структура проекта для разработки

```
06.08/
├── src/
│   ├── bot/          # Telegram bot обработчики
│   ├── core/         # Основная бизнес-логика
│   └── database/     # Модели и операции с БД
├── config/           # Конфигурация и константы
├── questions/        # JSON файлы с вопросами тестов
├── tests/           # Тесты проекта
├── requirements.txt # Python зависимости
├── .env            # Переменные окружения
└── pytest.ini     # Конфигурация pytest
```

## Отладка и разработка

### 1. Логирование

По умолчанию логи выводятся в консоль. Для изменения уровня логирования:

```python
# В config/settings.py
DEBUG = True  # INFO уровень
DEBUG = False # WARNING уровень
```

### 2. Работа с PyCharm

1. Откройте проект в PyCharm
2. Настройте интерпретатор Python: `File → Settings → Project → Python Interpreter`
3. Выберите виртуальное окружение: `venv/bin/python`
4. Создайте конфигурацию запуска:
   - `Run → Edit Configurations`
   - Script path: `src/bot/main.py`
   - Working directory: корневая папка проекта

### 3. Переменные окружения в IDE

В PyCharm добавьте переменные окружения в конфигурацию запуска или используйте плагин EnvFile.

## Возможные проблемы и решения

### 1. Ошибка подключения к базе данных

```bash
# Проверьте статус PostgreSQL
sudo systemctl status postgresql

# Перезапустите если нужно
sudo systemctl restart postgresql

# Проверьте настройки pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

### 2. Ошибка "Module not found"

```bash
# Убедитесь что виртуальное окружение активировано
source venv/bin/activate

# Переустановите зависимости
pip install -r requirements.txt
```

### 3. Проблемы с правами доступа

```bash
# Проверьте права на файлы проекта
ls -la

# Измените права если нужно
chmod +x venv/bin/activate
```

### 4. Ошибки в тестах

```bash
# Очистите кэш Python
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Переустановите pytest
pip uninstall pytest pytest-asyncio pytest-mock
pip install pytest pytest-asyncio pytest-mock
```

## Мониторинг и производительность

### 1. Просмотр логов в режиме реального времени

```bash
# Запуск с выводом в файл
python src/bot/main.py 2>&1 | tee bot.log

# Просмотр логов
tail -f bot.log
```

### 2. Мониторинг базы данных

```bash
# Подключение к базе для проверки
psql -U postgres -d mind_style -h localhost

# Просмотр таблиц
\dt

# Просмотр пользователей
SELECT user_id, username, test_completed FROM users LIMIT 10;
```

Это полная инструкция по настройке и запуску проекта локально. Следуя этим шагам, вы сможете запустить бота и начать его тестирование.