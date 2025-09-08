-- ============================================
-- Скрипт для создания базы данных MySQL
-- ============================================

-- Подключение к MySQL под суперпользователем root
-- mysql -u root -p

-- Создание базы данных с правильной кодировкой
CREATE DATABASE IF NOT EXISTS mind_style
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Создание пользователя для работы с базой (опционально)
-- CREATE USER IF NOT EXISTS 'mind_style_user'@'localhost' IDENTIFIED BY 'secure_password';
-- GRANT ALL PRIVILEGES ON mind_style.* TO 'mind_style_user'@'localhost';
-- FLUSH PRIVILEGES;

-- Переключение на созданную базу данных
USE mind_style;

-- Установка кодировки для текущей сессии
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET collation_connection = utf8mb4_unicode_ci;

-- Настройка SQL режимов для совместимости
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO';

-- Информация об успешном создании
SELECT 
    'База данных mind_style успешно создана!' as message,
    DATABASE() as database_name,
    USER() as current_user,
    VERSION() as mysql_version,
    @@character_set_database as charset,
    @@collation_database as collation;

-- Проверка настроек базы данных
SHOW VARIABLES LIKE 'character_set%';
SHOW VARIABLES LIKE 'collation%';

-- Показать размер базы данных
SELECT 
    SCHEMA_NAME as 'Database',
    ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as 'Size (MB)'
FROM information_schema.SCHEMATA s
LEFT JOIN information_schema.TABLES t ON s.SCHEMA_NAME = t.TABLE_SCHEMA
WHERE s.SCHEMA_NAME = 'mind_style'
GROUP BY s.SCHEMA_NAME;