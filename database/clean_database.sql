-- ============================================
-- Скрипт для очистки базы данных MySQL
-- ВНИМАНИЕ: Этот скрипт удаляет ВСЕ данные!
-- ============================================

-- Подключение к базе данных
-- mysql -u root -p mind_style

-- Установка кодировки для сессии
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Переключение на базу данных
USE mind_style;

-- ============================================
-- ВАРИАНТ 1: Очистка данных с сохранением структуры
-- ============================================

-- Отключаем проверки внешних ключей для ускорения операций
SET FOREIGN_KEY_CHECKS = 0;

-- Очистка таблицы users (удаление всех записей и сброс AUTO_INCREMENT)
TRUNCATE TABLE users;

-- Включаем обратно проверки внешних ключей
SET FOREIGN_KEY_CHECKS = 1;

-- Проверка что таблица пуста
SELECT 
    'Таблица users очищена!' as message,
    COUNT(*) as remaining_records,
    'AUTO_INCREMENT сброшен до 1' as auto_increment_status
FROM users;

-- ============================================
-- ВАРИАНТ 2: Выборочная очистка
-- ============================================

-- Удаление только завершенных тестов (раскомментировать если нужно)
-- DELETE FROM users WHERE test_completed = TRUE;

-- Удаление тестовых пользователей (раскомментировать если нужно)  
-- DELETE FROM users WHERE username LIKE 'test_%' OR first_name LIKE 'Тест%';

-- Удаление пользователей старше определенной даты (раскомментировать если нужно)
-- DELETE FROM users WHERE created_at < DATE_SUB(CURDATE(), INTERVAL 30 DAY);

-- Удаление незавершенных тестов старше 24 часов (раскомментировать если нужно)
-- DELETE FROM users 
-- WHERE test_completed = FALSE 
--   AND created_at < DATE_SUB(NOW(), INTERVAL 24 HOUR);

-- Удаление пользователей из Senler (для тестирования, раскомментировать если нужно)
-- DELETE FROM users WHERE from_senler = TRUE;

-- ============================================
-- ВАРИАНТ 3: Сброс счетчиков AUTO_INCREMENT
-- ============================================

-- Сброс автоинкремента ID (если не использовался TRUNCATE)
-- ALTER TABLE users AUTO_INCREMENT = 1;

-- ============================================
-- ВАРИАНТ 4: Удаление и пересоздание таблиц
-- ============================================

-- ВНИМАНИЕ: Полностью удаляет структуру таблиц!
-- Раскомментировать только если нужно полностью пересоздать структуру

-- SET FOREIGN_KEY_CHECKS = 0;
-- DROP TABLE IF EXISTS users;
-- SET FOREIGN_KEY_CHECKS = 1;

-- После этого нужно будет выполнить create_tables.sql заново

-- ============================================
-- Статистика после очистки
-- ============================================

-- Показать размер таблицы после очистки
SELECT 
    TABLE_SCHEMA as database_name,
    TABLE_NAME as table_name,
    ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) as size_mb,
    TABLE_ROWS as row_count,
    AUTO_INCREMENT as next_auto_increment
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users';

-- Показать информацию о структуре таблицы
SELECT 
    COLUMN_NAME as column_name,
    DATA_TYPE as data_type,
    IS_NULLABLE as is_nullable,
    COLUMN_DEFAULT as default_value,
    COLUMN_COMMENT as comment
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users' 
ORDER BY ORDINAL_POSITION;

-- Показать индексы таблицы
SELECT 
    INDEX_NAME as index_name,
    COLUMN_NAME as column_name,
    NON_UNIQUE as non_unique,
    INDEX_TYPE as index_type
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

-- Проверить что данные действительно удалены
SELECT 
    'База данных очищена успешно!' as message,
    (SELECT COUNT(*) FROM users) as total_users,
    NOW() as cleanup_time;

-- Показать общую статистику базы данных
SELECT 
    SCHEMA_NAME as 'Database',
    ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as 'Size (MB)',
    COUNT(TABLE_NAME) as 'Tables Count'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE()
GROUP BY SCHEMA_NAME;