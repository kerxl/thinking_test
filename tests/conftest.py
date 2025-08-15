import pytest
import asyncio
import sys
import os

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Фикстура для event loop
@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для асинхронных тестов"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_priorities_data():
    """Тестовые данные для теста приоритетов"""
    return {
        "personal_wellbeing": 5,
        "material_career": 4,
        "relationships": 3,
        "self_realization": 2
    }


@pytest.fixture
def sample_inq_data():
    """Тестовые данные для INQ теста"""
    return {
        "question_1": {"1": 5, "2": 4, "3": 3, "4": 2, "5": 1},
        "question_2": {"1": 3, "2": 5, "3": 1, "4": 4, "5": 2},
        "question_3": {"1": 2, "2": 1, "3": 5, "4": 3, "5": 4}
    }


@pytest.fixture
def sample_epi_data():
    """Тестовые данные для EPI теста"""
    return {
        "1": "Да",
        "2": "Нет", 
        "3": "Да",
        "4": "Да",
        "5": "Нет"
    }


@pytest.fixture
def sample_user_data():
    """Тестовые данные пользователя"""
    return {
        "user_id": 12345,
        "username": "test_user",
        "first_name": "Тест",
        "last_name": "Пользователь",
        "age": 25
    }