-- Миграция для добавления полей админских ссылок на Senler в таблицу users
-- Выполнить эту миграцию для поддержки отложенной отправки ссылок от администратора

-- Добавляем новые поля для админских ссылок Senler
ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_senler_link VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_link_send_time TIMESTAMP;

-- Создаем индекс для быстрого поиска пользователей с отложенными ссылками
CREATE INDEX IF NOT EXISTS idx_users_admin_link_send_time ON users(admin_link_send_time);

-- Добавляем комментарии к новым полям
COMMENT ON COLUMN users.admin_senler_link IS 'Ссылка на Senler добавленная администратором для отправки пользователю';
COMMENT ON COLUMN users.admin_link_send_time IS 'Время когда должна быть отправлена ссылка пользователю (через 24 часа)';