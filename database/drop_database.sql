-- ============================================
-- Скрипт для полного удаления базы данных
-- ВНИМАНИЕ: Полностью удаляет базу данных и пользователя!
-- ============================================

-- Подключение к PostgreSQL под суперпользователем
-- psql -U postgres

-- Завершение всех активных подключений к базе данных
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'mind_style'
  AND pid <> pg_backend_pid();

-- Удаление базы данных
DROP DATABASE IF EXISTS mind_style;

-- Удаление пользователя (осторожно! проверьте что пользователь не используется в других БД)

-- Проверка что база данных удалена
SELECT 
    CASE 
        WHEN EXISTS(SELECT 1 FROM pg_database WHERE datname = 'mind_style')
        THEN 'База данных НЕ удалена!'
        ELSE 'База данных успешно удалена!'
    END as message;

-- Список оставшихся баз данных
\l