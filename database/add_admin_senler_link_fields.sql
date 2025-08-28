-- Миграция для добавления полей админских ссылок на Senler в таблицу users (MySQL)
-- Выполнить эту миграцию для поддержки отложенной отправки ссылок от администратора

-- Добавляем новые поля для админских ссылок Senler
-- MySQL не поддерживает IF NOT EXISTS для ADD COLUMN, поэтому используем процедуру
DELIMITER $$
CREATE PROCEDURE AddColumnIfNotExists()
BEGIN
    -- Проверяем существование столбца admin_senler_link
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'admin_senler_link'
    ) THEN
        ALTER TABLE users ADD COLUMN admin_senler_link VARCHAR(500) COMMENT 'Ссылка на Senler добавленная администратором для отправки пользователю';
    END IF;
    
    -- Проверяем существование столбца admin_link_send_time
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'admin_link_send_time'
    ) THEN
        ALTER TABLE users ADD COLUMN admin_link_send_time TIMESTAMP NULL COMMENT 'Время когда должна быть отправлена ссылка пользователю (случайно от 15 до 24 часов)';
    END IF;
END$$
DELIMITER ;

-- Выполняем процедуру
CALL AddColumnIfNotExists();

-- Удаляем процедуру после использования
DROP PROCEDURE AddColumnIfNotExists;

-- Создаем индекс для быстрого поиска пользователей с отложенными ссылками
-- Сначала проверяем, не существует ли индекс
SET @indexExists := (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users' 
    AND INDEX_NAME = 'idx_users_admin_link_send_time'
);

SET @sql = IF(@indexExists = 0, 
    'CREATE INDEX idx_users_admin_link_send_time ON users(admin_link_send_time)', 
    'SELECT "Index already exists" as message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;