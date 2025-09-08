-- ============================================
-- Миграция для добавления полей Senler интеграции в таблицу users (MySQL)
-- Выполнить эту миграцию для поддержки Senler интеграции
-- ============================================

-- Подключение к базе данных
-- mysql -u root -p mind_style

-- Установка кодировки для сессии
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Создаем процедуру для безопасного добавления столбцов
DELIMITER $$
CREATE PROCEDURE AddSenlerFields()
BEGIN
    -- Проверяем и добавляем поле senler_token
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'senler_token'
    ) THEN
        ALTER TABLE users ADD COLUMN senler_token VARCHAR(500) 
        COMMENT 'Token для возврата пользователя в Senler';
    END IF;
    
    -- Проверяем и добавляем поле senler_user_id
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'senler_user_id'
    ) THEN
        ALTER TABLE users ADD COLUMN senler_user_id VARCHAR(255) 
        COMMENT 'ID пользователя в системе Senler';
    END IF;
    
    -- Проверяем и добавляем поле from_senler
    IF NOT EXISTS (
        SELECT * FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'users' 
        AND COLUMN_NAME = 'from_senler'
    ) THEN
        ALTER TABLE users ADD COLUMN from_senler BOOLEAN DEFAULT FALSE 
        COMMENT 'Флаг указывающий что пользователь пришел из Senler';
    END IF;
END$$
DELIMITER ;

-- Выполняем процедуру добавления полей
CALL AddSenlerFields();

-- Удаляем процедуру после использования
DROP PROCEDURE AddSenlerFields;

-- Создаем индексы для быстрого поиска (с проверкой существования)
SET @indexExists := (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users' 
    AND INDEX_NAME = 'idx_users_senler_token'
);

SET @sql = IF(@indexExists = 0, 
    'CREATE INDEX idx_users_senler_token ON users(senler_token)', 
    'SELECT "Index idx_users_senler_token already exists" as message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Создаем индекс для from_senler
SET @indexExists := (
    SELECT COUNT(*) 
    FROM information_schema.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'users' 
    AND INDEX_NAME = 'idx_users_from_senler'
);

SET @sql = IF(@indexExists = 0, 
    'CREATE INDEX idx_users_from_senler ON users(from_senler)', 
    'SELECT "Index idx_users_from_senler already exists" as message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Проверяем добавленные поля
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'users' 
AND COLUMN_NAME IN ('senler_token', 'senler_user_id', 'from_senler')
ORDER BY ORDINAL_POSITION;

-- Показываем созданные индексы
SELECT 
    INDEX_NAME,
    COLUMN_NAME,
    NON_UNIQUE
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'users' 
AND INDEX_NAME LIKE '%senler%'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

SELECT 'Поля Senler интеграции успешно добавлены!' as message;