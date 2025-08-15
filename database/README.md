# База данных - SQL скрипты

Этот каталог содержит SQL скрипты для управления базой данных PostgreSQL проекта.

## 📁 Описание файлов

### Основные скрипты

- **`create_database.sql`** - Создание базы данных и пользователя
- **`create_tables.sql`** - Создание таблиц и индексов
- **`clean_database.sql`** - Очистка данных (несколько вариантов)
- **`drop_database.sql`** - Полное удаление базы данных

### Вспомогательные скрипты

- **`sample_data.sql`** - Вставка тестовых данных для разработки
- **`queries.sql`** - Полезные запросы для анализа данных

## 🚀 Порядок выполнения

### Первая установка

1. **Создание базы данных** (от имени суперпользователя postgres):
```bash
sudo -u postgres psql -f database/create_database.sql
```

2. **Создание таблиц**:
```bash
psql -U postgres -d mind_style -f database/create_tables.sql
```

3. **[Опционально] Добавление тестовых данных**:
```bash
psql -U postgres -d mind_style -f database/sample_data.sql
```


Также обновите файл `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/mind_style
```

## 🧹 Очистка данных

### Вариант 1: Очистка всех данных
```bash
psql -U postgres -d mind_style -f database/clean_database.sql
```

### Вариант 2: Выборочная очистка
Откройте файл `clean_database.sql` и раскомментируйте нужные строки для:
- Удаления только завершенных тестов
- Удаления тестовых пользователей
- Удаления старых записей

### Вариант 3: Полное пересоздание
```bash
# Удаление базы данных
sudo -u postgres psql -f database/drop_database.sql

# Создание заново
sudo -u postgres psql -f database/create_database.sql
psql -U postgres -d mind_style -f database/create_tables.sql
```

## 📊 Анализ данных

Выполните готовые запросы для анализа:
```bash
psql -U postgres -d mind_style -f database/queries.sql
```

Или подключитесь к базе интерактивно:
```bash
psql -U postgres -d mind_style
```

### Полезные интерактивные команды:

```sql
-- Общая статистика
SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE test_completed = TRUE) as completed FROM users;

-- Последние пользователи
SELECT user_id, username, created_at FROM users ORDER BY created_at DESC LIMIT 5;

-- Распределение по темпераментам
SELECT temperament, COUNT(*) FROM users WHERE temperament IS NOT NULL GROUP BY temperament;
```

## 🔒 Безопасность

### Рекомендации:
1. **Смените пароль по умолчанию** в `create_database.sql`
2. **Ограничьте подключения** в `pg_hba.conf` если нужно
3. **Регулярно делайте бэкапы**:
```bash
pg_dump -U postgres mind_style > backup_$(date +%Y%m%d_%H%M%S).sql
```

4. **Восстановление из бэкапа**:
```bash
psql -U postgres -d mind_style < backup_file.sql
```

## 🐛 Отладка

### Проблемы с правами доступа:
```sql
-- Проверка текущего пользователя
SELECT current_user, current_database();

-- Проверка прав на таблицы
SELECT grantee, table_name, privilege_type 
FROM information_schema.role_table_grants 
WHERE table_name = 'users';
```

### Проблемы с подключением:
```bash
# Проверка статуса PostgreSQL
sudo systemctl status postgresql

# Проверка портов
sudo netstat -tlnp | grep 5432

# Проверка логов PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

## 🎯 Структура таблицы users

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | SERIAL PRIMARY KEY | Внутренний ID |
| `user_id` | BIGINT UNIQUE | ID пользователя в Telegram |
| `username` | VARCHAR(255) | @username в Telegram |
| `first_name` | VARCHAR(255) | Имя пользователя |
| `last_name` | VARCHAR(255) | Фамилия пользователя |
| `age` | INTEGER | Возраст пользователя |
| `test_start` | TIMESTAMP | Время начала тестирования |
| `test_end` | TIMESTAMP | Время завершения тестирования |
| `answers_json` | JSONB | Все ответы пользователя |
| `inq_scores_json` | JSONB | Результаты INQ теста |
| `epi_scores_json` | JSONB | Результаты EPI теста |
| `priorities_json` | JSONB | Результаты теста приоритетов |
| `temperament` | VARCHAR(50) | Определенный темперамент |
| `current_task_type` | INTEGER | Текущий тип теста (1-3) |
| `current_question` | INTEGER | Номер текущего вопроса |
| `current_step` | INTEGER | Текущий шаг в вопросе |
| `test_completed` | BOOLEAN | Флаг завершения всех тестов |
| `created_at` | TIMESTAMP | Время создания записи |
| `updated_at` | TIMESTAMP | Время последнего обновления |