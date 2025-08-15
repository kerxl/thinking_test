-- ============================================
-- Скрипт для создания базы данных и пользователя
-- ============================================

-- Подключение к PostgreSQL под суперпользователем postgres
-- psql -U postgres

-- Создание базы данных
CREATE DATABASE mind_style
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    TABLESPACE = pg_default;

-- Предоставление всех прав на базу данных пользователю
GRANT ALL PRIVILEGES ON DATABASE mind_style TO postgres;

-- Подключение к созданной базе данных
\c mind_style

-- Предоставление прав на схему public
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Установка прав по умолчанию для будущих объектов
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres;

-- Создание расширения для генерации UUID (если понадобится)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Информация об успешном создании
SELECT 
    'База данных mind_style успешно создана!' as message,
    current_database() as database_name,
    current_user as current_user,
    version() as postgresql_version;