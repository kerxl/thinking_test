-- ============================================
-- Скрипт для вставки тестовых данных
-- Используется для разработки и тестирования
-- ============================================

-- Подключение к базе данных
-- psql -U postgres -d mind_style

-- Очистка таблицы перед вставкой тестовых данных
TRUNCATE TABLE users RESTART IDENTITY;

-- Вставка тестовых пользователей
INSERT INTO users (
    user_id, username, first_name, last_name, age,
    test_start, test_end,
    answers_json,
    inq_scores_json, epi_scores_json, priorities_json,
    temperament,
    current_task_type, current_question, current_step, test_completed,
    created_at, updated_at
) VALUES 

-- Пользователь 1: Завершил все тесты
(
    12345678, 
    '@ivanov', 
    'Иван', 
    'Иванов', 
    29,
    '2025-08-15 14:00:00+00', 
    '2025-08-15 14:25:00+00',
    '{
        "priorities": {
            "personal_wellbeing": 3,
            "material_career": 2, 
            "relationships": 5,
            "self_realization": 4
        },
        "inq": {
            "question_1": {"1": 5, "2": 4, "3": 3, "4": 2, "5": 1},
            "question_2": {"1": 3, "2": 5, "3": 1, "4": 4, "5": 2},
            "question_3": {"1": 2, "2": 1, "3": 5, "4": 3, "5": 4}
        },
        "epi": {
            "1": "Да", "2": "Нет", "3": "Да", "4": "Да", "5": "Нет",
            "6": "Да", "7": "Нет", "8": "Да", "9": "Да", "10": "Нет"
        }
    }'::jsonb,
    '{"Синтетический": 80, "Идеалистический": 72, "Прагматический": 59, "Аналитический": 65, "Реалистический": 64}'::jsonb,
    '{"E": 21, "N": 6, "L": 7}'::jsonb,
    '{"personal_wellbeing": 3, "material_career": 2, "relationships": 5, "self_realization": 4}'::jsonb,
    'Сангвиник',
    4, 0, 0, TRUE,
    '2025-08-15 14:00:00+00',
    '2025-08-15 14:25:00+00'
),

-- Пользователь 2: В процессе прохождения INQ теста
(
    87654321,
    '@petrov',
    'Петр',
    'Петров', 
    25,
    '2025-08-15 15:00:00+00',
    NULL,
    '{
        "priorities": {
            "personal_wellbeing": 5,
            "material_career": 4,
            "relationships": 2,
            "self_realization": 3
        },
        "inq": {
            "question_1": {"1": 5, "2": 4, "3": 3},
            "question_2": {"1": 2, "2": 5}
        }
    }'::jsonb,
    NULL,
    NULL,
    '{"personal_wellbeing": 5, "material_career": 4, "relationships": 2, "self_realization": 3}'::jsonb,
    NULL,
    2, 1, 2, FALSE,
    '2025-08-15 15:00:00+00',
    '2025-08-15 15:15:00+00'
),

-- Пользователь 3: Только начал (собрал личные данные)
(
    11111111,
    '@newuser',
    'Анна',
    'Сидорова',
    22,
    '2025-08-15 16:00:00+00',
    NULL,
    '{}'::jsonb,
    NULL,
    NULL,
    NULL,
    NULL,
    1, 0, 0, FALSE,
    '2025-08-15 16:00:00+00',
    '2025-08-15 16:00:00+00'
),

-- Пользователь 4: Завершил с другим темпераментом
(
    22222222,
    '@choleric',
    'Михаил',
    'Громов',
    35,
    '2025-08-15 12:00:00+00',
    '2025-08-15 12:30:00+00',
    '{
        "priorities": {
            "personal_wellbeing": 2,
            "material_career": 5,
            "relationships": 3,
            "self_realization": 4
        },
        "inq": {
            "question_1": {"1": 3, "2": 2, "3": 5, "4": 4, "5": 1},
            "question_2": {"1": 5, "2": 3, "3": 4, "4": 1, "5": 2},
            "question_3": {"1": 4, "2": 5, "3": 2, "4": 3, "5": 1}
        },
        "epi": {
            "1": "Да", "2": "Да", "3": "Да", "4": "Да", "5": "Да",
            "6": "Да", "7": "Да", "8": "Да", "9": "Да", "10": "Да"
        }
    }'::jsonb,
    '{"Синтетический": 65, "Идеалистический": 60, "Прагматический": 85, "Аналитический": 70, "Реалистический": 55}'::jsonb,
    '{"E": 25, "N": 20, "L": 3}'::jsonb,
    '{"personal_wellbeing": 2, "material_career": 5, "relationships": 3, "self_realization": 4}'::jsonb,
    'Холерик',
    4, 0, 0, TRUE,
    '2025-08-15 12:00:00+00',
    '2025-08-15 12:30:00+00'
);

-- Проверка вставленных данных
SELECT 
    'Тестовые данные успешно добавлены!' as message,
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE test_completed = TRUE) as completed_tests,
    COUNT(*) FILTER (WHERE test_completed = FALSE) as in_progress_tests
FROM users;

-- Показать краткую информацию о пользователях
SELECT 
    id,
    user_id,
    username,
    first_name,
    last_name,
    age,
    current_task_type,
    current_question,
    current_step,
    test_completed,
    temperament,
    created_at
FROM users
ORDER BY id;