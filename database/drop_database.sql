-- ============================================
-- Скрипт для удаления базы данных MySQL
-- ВНИМАНИЕ: Этот скрипт полностью удаляет базу данных!
-- ============================================

-- Подключение к MySQL под суперпользователем root
-- mysql -u root -p

-- ВНИМАНИЕ: Команды ниже полностью удаляют базу данных и все данные!
-- Убедитесь что вы действительно хотите это сделать!

-- Показать текущие базы данных перед удалением
SHOW DATABASES;

-- Показать размер базы данных перед удалением
SELECT 
    SCHEMA_NAME as 'Database',
    ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as 'Size (MB)'
FROM information_schema.SCHEMATA s
LEFT JOIN information_schema.TABLES t ON s.SCHEMA_NAME = t.TABLE_SCHEMA
WHERE s.SCHEMA_NAME = 'mind_style'
GROUP BY s.SCHEMA_NAME;

-- Закрытие всех подключений к базе данных (показать текущие подключения)
SELECT 
    ID,
    USER,
    HOST,
    DB,
    COMMAND,
    TIME,
    STATE
FROM information_schema.PROCESSLIST 
WHERE DB = 'mind_style';

-- Если есть активные подключения, их можно завершить:
-- KILL CONNECTION process_id;

-- Удаление базы данных
DROP DATABASE IF EXISTS mind_style;

-- Удаление пользователя (если он был создан - раскомментировать если нужно)
-- DROP USER IF EXISTS 'mind_style_user'@'localhost';
-- FLUSH PRIVILEGES;

-- Проверка что база данных удалена
SELECT 
    'База данных mind_style удалена!' as message,
    CASE 
        WHEN COUNT(*) = 0 THEN 'База данных успешно удалена'
        ELSE 'База данных все еще существует'
    END as deletion_status
FROM information_schema.SCHEMATA 
WHERE SCHEMA_NAME = 'mind_style';

-- Показать оставшиеся базы данных
SELECT 
    SCHEMA_NAME as database_name,
    DEFAULT_CHARACTER_SET_NAME as charset,
    DEFAULT_COLLATION_NAME as collation
FROM information_schema.SCHEMATA 
WHERE SCHEMA_NAME NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
ORDER BY SCHEMA_NAME;

-- Показать размеры оставшихся пользовательских баз данных
SELECT 
    SCHEMA_NAME as 'Database',
    ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as 'Size (MB)',
    COUNT(TABLE_NAME) as 'Tables'
FROM information_schema.SCHEMATA s
LEFT JOIN information_schema.TABLES t ON s.SCHEMA_NAME = t.TABLE_SCHEMA
WHERE s.SCHEMA_NAME NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
GROUP BY s.SCHEMA_NAME
ORDER BY SUM(DATA_LENGTH + INDEX_LENGTH) DESC;

SELECT 
    'Операция удаления завершена!' as final_message,
    NOW() as deletion_time;