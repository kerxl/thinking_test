-- ============================================
-- Скрипт для очистки базы данных
-- ВНИМАНИЕ: Этот скрипт удаляет ВСЕ данные!
-- ============================================

-- Подключение к базе данных
-- psql -U postgres -d mind_style

-- ============================================
-- ВАРИАНТ 1: Очистка данных с сохранением структуры
-- ============================================

-- Очистка таблицы users (удаление всех записей)
TRUNCATE TABLE users RESTART IDENTITY CASCADE;

-- Проверка что таблица пуста
SELECT 
    'Таблица users очищена!' as message,
    COUNT(*) as remaining_records
FROM users;

-- ============================================
-- ВАРИАНТ 2: Выборочная очистка
-- ============================================

-- Удаление только завершенных тестов (раскомментировать если нужно)
-- DELETE FROM users WHERE test_completed = TRUE;

-- Удаление тестовых пользователей (раскомментировать если нужно)
-- DELETE FROM users WHERE username LIKE 'test_%' OR first_name LIKE 'Тест%';

-- Удаление пользователей старше определенной даты (раскомментировать если нужно)
-- DELETE FROM users WHERE created_at < CURRENT_DATE - INTERVAL '30 days';

-- Удаление незавершенных тестов старше 24 часов (раскомментировать если нужно)
-- DELETE FROM users 
-- WHERE test_completed = FALSE 
--   AND created_at < CURRENT_TIMESTAMP - INTERVAL '24 hours';

-- ============================================
-- ВАРИАНТ 3: Сброс счетчиков
-- ============================================

-- Сброс автоинкремента ID (если использовался TRUNCATE, то автоматически)
-- ALTER SEQUENCE users_id_seq RESTART WITH 1;

-- ============================================
-- ВАРИАНТ 4: Удаление и пересоздание таблиц
-- ============================================

-- ВНИМАНИЕ: Полностью удаляет структуру таблиц!
-- Раскомментировать только если нужно полностью пересоздать структуру

-- DROP TABLE IF EXISTS users CASCADE;
-- DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- После этого нужно будет выполнить create_tables.sql заново

-- ============================================
-- Статистика после очистки
-- ============================================

-- Показать размер таблицы после очистки
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE tablename = 'users';

-- Показать информацию о таблице
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

-- Проверить что данные действительно удалены
SELECT 
    'База данных очищена успешно!' as message,
    (SELECT COUNT(*) FROM users) as total_users;