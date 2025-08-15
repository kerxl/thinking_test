-- ============================================
-- Скрипт для создания таблиц
-- Выполняется после создания базы данных
-- ============================================

-- Подключение к базе данных
-- psql -U postgres -d mind_style

-- Удаление таблицы если существует (осторожно!)
-- DROP TABLE IF EXISTS users CASCADE;

-- Создание основной таблицы пользователей
CREATE TABLE IF NOT EXISTS users (
    -- Основные поля
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    age INTEGER,
    
    -- Временные метки тестирования
    test_start TIMESTAMP WITH TIME ZONE,
    test_end TIMESTAMP WITH TIME ZONE,
    
    -- JSON данные ответов
    answers_json JSONB,
    
    -- Результаты тестов
    inq_scores_json JSONB,
    epi_scores_json JSONB,
    priorities_json JSONB,
    temperament VARCHAR(50),
    
    -- Состояние тестирования
    current_task_type INTEGER DEFAULT 1,
    current_question INTEGER DEFAULT 0,
    current_step INTEGER DEFAULT 0,
    test_completed BOOLEAN DEFAULT FALSE,
    
    -- Служебные поля
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_test_completed ON users(test_completed);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_current_task_type ON users(current_task_type);

-- Индексы для JSON полей
CREATE INDEX IF NOT EXISTS idx_users_answers_json ON users USING GIN (answers_json);
CREATE INDEX IF NOT EXISTS idx_users_inq_scores_json ON users USING GIN (inq_scores_json);
CREATE INDEX IF NOT EXISTS idx_users_epi_scores_json ON users USING GIN (epi_scores_json);
CREATE INDEX IF NOT EXISTS idx_users_priorities_json ON users USING GIN (priorities_json);

-- Создание функции для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Создание триггера для автоматического обновления updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Добавление комментариев к таблице и полям
COMMENT ON TABLE users IS 'Основная таблица пользователей бота';
COMMENT ON COLUMN users.id IS 'Внутренний ID записи';
COMMENT ON COLUMN users.user_id IS 'ID пользователя в Telegram';
COMMENT ON COLUMN users.username IS 'Имя пользователя в Telegram (@username)';
COMMENT ON COLUMN users.first_name IS 'Имя пользователя';
COMMENT ON COLUMN users.last_name IS 'Фамилия пользователя';
COMMENT ON COLUMN users.age IS 'Возраст пользователя';
COMMENT ON COLUMN users.test_start IS 'Время начала тестирования';
COMMENT ON COLUMN users.test_end IS 'Время завершения тестирования';
COMMENT ON COLUMN users.answers_json IS 'JSON с ответами на все тесты';
COMMENT ON COLUMN users.inq_scores_json IS 'JSON с результатами INQ теста';
COMMENT ON COLUMN users.epi_scores_json IS 'JSON с результатами EPI теста';
COMMENT ON COLUMN users.priorities_json IS 'JSON с результатами теста приоритетов';
COMMENT ON COLUMN users.temperament IS 'Определенный темперамент (Холерик, Сангвиник, Меланхолик, Флегматик)';
COMMENT ON COLUMN users.current_task_type IS 'Текущий тип теста (1-приоритеты, 2-INQ, 3-EPI)';
COMMENT ON COLUMN users.current_question IS 'Номер текущего вопроса';
COMMENT ON COLUMN users.current_step IS 'Текущий шаг в вопросе';
COMMENT ON COLUMN users.test_completed IS 'Флаг завершения всех тестов';

-- Проверка созданных объектов
SELECT 
    'Таблицы успешно созданы!' as message,
    COUNT(*) as tables_count
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name = 'users';

-- Показать структуру таблицы
\d+ users;