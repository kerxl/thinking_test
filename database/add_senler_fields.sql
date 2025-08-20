-- Миграция для добавления полей Senler интеграции в таблицу users
-- Выполнить эту миграцию для поддержки Senler интеграции

-- Добавляем новые поля для Senler интеграции
ALTER TABLE users ADD COLUMN IF NOT EXISTS senler_token VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS senler_user_id VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS from_senler BOOLEAN DEFAULT FALSE;

-- Создаем индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_users_senler_token ON users(senler_token);
CREATE INDEX IF NOT EXISTS idx_users_from_senler ON users(from_senler);

-- Добавляем комментарии к новым полям
COMMENT ON COLUMN users.senler_token IS 'Token для возврата пользователя в Senler';
COMMENT ON COLUMN users.senler_user_id IS 'ID пользователя в системе Senler';
COMMENT ON COLUMN users.from_senler IS 'Флаг указывающий что пользователь пришел из Senler';