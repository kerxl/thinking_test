-- ============================================
-- Полезные SQL запросы для анализа данных
-- ============================================

-- Подключение к базе данных
-- psql -U postgres -d mind_style

-- ============================================
-- ОСНОВНАЯ СТАТИСТИКА
-- ============================================

-- Общая статистика пользователей
SELECT 
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE test_completed = TRUE) as completed_tests,
    COUNT(*) FILTER (WHERE test_completed = FALSE) as in_progress_tests,
    COUNT(*) FILTER (WHERE current_task_type = 1) as on_priorities_test,
    COUNT(*) FILTER (WHERE current_task_type = 2) as on_inq_test,
    COUNT(*) FILTER (WHERE current_task_type = 3) as on_epi_test,
    ROUND(AVG(age), 2) as average_age,
    MIN(age) as min_age,
    MAX(age) as max_age
FROM users;

-- Статистика по темпераментам
SELECT 
    temperament,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM users WHERE temperament IS NOT NULL), 2) as percentage
FROM users 
WHERE temperament IS NOT NULL
GROUP BY temperament
ORDER BY count DESC;

-- Статистика по возрастным группам
SELECT 
    CASE 
        WHEN age BETWEEN 12 AND 18 THEN '12-18'
        WHEN age BETWEEN 19 AND 25 THEN '19-25'
        WHEN age BETWEEN 26 AND 35 THEN '26-35'
        WHEN age BETWEEN 36 AND 50 THEN '36-50'
        WHEN age > 50 THEN '50+'
        ELSE 'Не указан'
    END as age_group,
    COUNT(*) as count
FROM users
GROUP BY age_group
ORDER BY age_group;

-- ============================================
-- АНАЛИЗ ПРОХОЖДЕНИЯ ТЕСТОВ
-- ============================================

-- Время прохождения тестов
SELECT 
    user_id,
    username,
    first_name,
    test_start,
    test_end,
    CASE 
        WHEN test_end IS NOT NULL AND test_start IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (test_end - test_start)) / 60.0
        ELSE NULL 
    END as duration_minutes
FROM users 
WHERE test_completed = TRUE
ORDER BY duration_minutes;

-- Средняя продолжительность тестирования
SELECT 
    ROUND(AVG(EXTRACT(EPOCH FROM (test_end - test_start)) / 60.0), 2) as avg_duration_minutes,
    ROUND(MIN(EXTRACT(EPOCH FROM (test_end - test_start)) / 60.0), 2) as min_duration_minutes,
    ROUND(MAX(EXTRACT(EPOCH FROM (test_end - test_start)) / 60.0), 2) as max_duration_minutes
FROM users 
WHERE test_completed = TRUE 
  AND test_end IS NOT NULL 
  AND test_start IS NOT NULL;

-- Пользователи, застрявшие в тестах (более 24 часов)
SELECT 
    user_id,
    username,
    first_name,
    current_task_type,
    current_question,
    current_step,
    created_at,
    ROUND(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at)) / 3600.0, 2) as hours_stuck
FROM users 
WHERE test_completed = FALSE 
  AND created_at < CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY hours_stuck DESC;

-- ============================================
-- АНАЛИЗ РЕЗУЛЬТАТОВ INQ ТЕСТА
-- ============================================

-- Средние значения стилей мышления
SELECT 
    ROUND(AVG(CAST(inq_scores_json->>'Синтетический' AS INTEGER)), 2) as avg_synthetic,
    ROUND(AVG(CAST(inq_scores_json->>'Идеалистический' AS INTEGER)), 2) as avg_idealistic,
    ROUND(AVG(CAST(inq_scores_json->>'Прагматический' AS INTEGER)), 2) as avg_pragmatic,
    ROUND(AVG(CAST(inq_scores_json->>'Аналитический' AS INTEGER)), 2) as avg_analytic,
    ROUND(AVG(CAST(inq_scores_json->>'Реалистический' AS INTEGER)), 2) as avg_realistic
FROM users 
WHERE inq_scores_json IS NOT NULL;

-- Топ-10 пользователей по аналитическому стилю
SELECT 
    user_id,
    username,
    first_name,
    CAST(inq_scores_json->>'Аналитический' AS INTEGER) as analytic_score
FROM users 
WHERE inq_scores_json IS NOT NULL
ORDER BY CAST(inq_scores_json->>'Аналитический' AS INTEGER) DESC
LIMIT 10;

-- ============================================
-- АНАЛИЗ РЕЗУЛЬТАТОВ EPI ТЕСТА
-- ============================================

-- Распределение по экстраверсии и нейротизму
SELECT 
    ROUND(AVG(CAST(epi_scores_json->>'E' AS INTEGER)), 2) as avg_extraversion,
    ROUND(AVG(CAST(epi_scores_json->>'N' AS INTEGER)), 2) as avg_neuroticism,
    ROUND(AVG(CAST(epi_scores_json->>'L' AS INTEGER)), 2) as avg_lie_scale,
    COUNT(*) as total_completed
FROM users 
WHERE epi_scores_json IS NOT NULL;

-- Корреляция темперамента с возрастом
SELECT 
    temperament,
    ROUND(AVG(age), 2) as avg_age,
    COUNT(*) as count
FROM users 
WHERE temperament IS NOT NULL AND age IS NOT NULL
GROUP BY temperament
ORDER BY avg_age;

-- ============================================
-- АНАЛИЗ ПРИОРИТЕТОВ
-- ============================================

-- Средние приоритеты по категориям
SELECT 
    ROUND(AVG(CAST(priorities_json->>'personal_wellbeing' AS INTEGER)), 2) as avg_personal_wellbeing,
    ROUND(AVG(CAST(priorities_json->>'material_career' AS INTEGER)), 2) as avg_material_career,
    ROUND(AVG(CAST(priorities_json->>'relationships' AS INTEGER)), 2) as avg_relationships,
    ROUND(AVG(CAST(priorities_json->>'self_realization' AS INTEGER)), 2) as avg_self_realization
FROM users 
WHERE priorities_json IS NOT NULL;

-- Самая популярная приоритетная категория (получающая оценку 5)
SELECT 
    priority_category,
    COUNT(*) as times_rated_5
FROM (
    SELECT 
        user_id,
        CASE 
            WHEN CAST(priorities_json->>'personal_wellbeing' AS INTEGER) = 5 THEN 'Личное благополучие'
            WHEN CAST(priorities_json->>'material_career' AS INTEGER) = 5 THEN 'Материальное развитие'
            WHEN CAST(priorities_json->>'relationships' AS INTEGER) = 5 THEN 'Отношения'
            WHEN CAST(priorities_json->>'self_realization' AS INTEGER) = 5 THEN 'Самореализация'
        END as priority_category
    FROM users 
    WHERE priorities_json IS NOT NULL
) subq
WHERE priority_category IS NOT NULL
GROUP BY priority_category
ORDER BY times_rated_5 DESC;

-- ============================================
-- АНАЛИЗ АКТИВНОСТИ ПО ВРЕМЕНИ
-- ============================================

-- Активность по часам (когда пользователи чаще начинают тесты)
SELECT 
    EXTRACT(HOUR FROM created_at) as hour,
    COUNT(*) as users_started
FROM users
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour;

-- Активность по дням недели
SELECT 
    TO_CHAR(created_at, 'Day') as day_of_week,
    COUNT(*) as users_started
FROM users
GROUP BY TO_CHAR(created_at, 'Day'), EXTRACT(DOW FROM created_at)
ORDER BY EXTRACT(DOW FROM created_at);

-- ============================================
-- ПОИСК И ФИЛЬТРАЦИЯ
-- ============================================

-- Поиск пользователя по username или имени
-- SELECT * FROM users WHERE username ILIKE '%имя%' OR first_name ILIKE '%имя%';

-- Пользователи с высокими показателями нейротизма
SELECT 
    user_id,
    username,
    first_name,
    temperament,
    CAST(epi_scores_json->>'N' AS INTEGER) as neuroticism_score
FROM users 
WHERE epi_scores_json IS NOT NULL
  AND CAST(epi_scores_json->>'N' AS INTEGER) >= 15
ORDER BY CAST(epi_scores_json->>'N' AS INTEGER) DESC;

-- Последние 10 зарегистрированных пользователей
SELECT 
    user_id,
    username,
    first_name,
    last_name,
    created_at,
    test_completed
FROM users 
ORDER BY created_at DESC 
LIMIT 10;