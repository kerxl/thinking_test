import pytest
import asyncio
import sys
import os
import json

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Загружаем MESSAGES для тестов
@pytest.fixture(scope="session", autouse=True)
def setup_messages():
    """Загрузка сообщений для тестов"""
    from config.const import MESSAGES
    try:
        with open("config/constants.json", "r", encoding="utf-8") as f:
            messages = json.load(f)
            MESSAGES.update(messages)
    except FileNotFoundError:
        # Добавляем минимальные сообщения для тестов
        MESSAGES.update({
            "answer_saved": "Ответ сохранен",
            "answer_process_error": "Ошибка обработки ответа",
            "task_not_found": "Задача не найдена",
            "task_incorrect": "Неверная задача",
            "answer_option_incorrect": "Неверная опция",
            "answer_option_already_exist": "Опция уже выбрана",
            "go_back_completed": "Возврат выполнен",
            "go_back_unavailable": "Возврат недоступен",
            "go_back_error": "Ошибка возврата"
        })


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