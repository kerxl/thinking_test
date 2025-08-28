-- ============================================
-- Скрипт для создания таблиц MySQL
-- Выполняется после создания базы данных
-- ============================================

-- Подключение к базе данных
-- mysql -u username -p database_name

-- Установка кодировки для сессии
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Удаление таблицы если существует (осторожно!)
-- DROP TABLE IF EXISTS users;

-- Создание основной таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    -- Основные поля
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    age INT,
    
    -- Временные метки тестирования
    test_start TIMESTAMP NULL,
    test_end TIMESTAMP NULL,
    
    -- JSON данные ответов
    answers_json JSON,
    
    -- Результаты тестов
    inq_scores_json JSON,
    epi_scores_json JSON,
    priorities_json JSON,
    temperament VARCHAR(50),
    
    -- Состояние тестирования
    current_task_type INT DEFAULT 1,
    current_question INT DEFAULT 0,
    current_step INT DEFAULT 0,
    test_completed BOOLEAN DEFAULT FALSE,
    
    -- Служебные поля
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Создание индексов для быстрого поиска
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_test_completed ON users(test_completed);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_current_task_type ON users(current_task_type);

-- Добавление комментариев к таблице и полям
ALTER TABLE users COMMENT = 'Основная таблица пользователей бота';
ALTER TABLE users MODIFY COLUMN id INT AUTO_INCREMENT COMMENT 'Внутренний ID записи';
ALTER TABLE users MODIFY COLUMN user_id BIGINT UNIQUE NOT NULL COMMENT 'ID пользователя в Telegram';
ALTER TABLE users MODIFY COLUMN username VARCHAR(255) COMMENT 'Имя пользователя в Telegram (@username)';
ALTER TABLE users MODIFY COLUMN first_name VARCHAR(255) COMMENT 'Имя пользователя';
ALTER TABLE users MODIFY COLUMN last_name VARCHAR(255) COMMENT 'Фамилия пользователя';
ALTER TABLE users MODIFY COLUMN age INT COMMENT 'Возраст пользователя';
ALTER TABLE users MODIFY COLUMN test_start TIMESTAMP NULL COMMENT 'Время начала тестирования';
ALTER TABLE users MODIFY COLUMN test_end TIMESTAMP NULL COMMENT 'Время завершения тестирования';
ALTER TABLE users MODIFY COLUMN answers_json JSON COMMENT 'JSON с ответами на все тесты';
ALTER TABLE users MODIFY COLUMN inq_scores_json JSON COMMENT 'JSON с результатами INQ теста';
ALTER TABLE users MODIFY COLUMN epi_scores_json JSON COMMENT 'JSON с результатами EPI теста';
ALTER TABLE users MODIFY COLUMN priorities_json JSON COMMENT 'JSON с результатами теста приоритетов';
ALTER TABLE users MODIFY COLUMN temperament VARCHAR(50) COMMENT 'Определенный темперамент (Холерик, Сангвиник, Меланхолик, Флегматик)';
ALTER TABLE users MODIFY COLUMN current_task_type INT DEFAULT 1 COMMENT 'Текущий тип теста (1-приоритеты, 2-INQ, 3-EPI)';
ALTER TABLE users MODIFY COLUMN current_question INT DEFAULT 0 COMMENT 'Номер текущего вопроса';
ALTER TABLE users MODIFY COLUMN current_step INT DEFAULT 0 COMMENT 'Текущий шаг в вопросе';
ALTER TABLE users MODIFY COLUMN test_completed BOOLEAN DEFAULT FALSE COMMENT 'Флаг завершения всех тестов';

-- Проверка созданных объектов
SELECT 
    'Таблицы успешно созданы!' as message,
    COUNT(*) as tables_count
FROM information_schema.tables 
WHERE table_schema = DATABASE() 
    AND table_name = 'users';

-- Показать структуру таблицы
DESCRIBE users;