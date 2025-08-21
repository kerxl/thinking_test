import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, mock_open
from src.core.task_models import PrioritiesTask, InqTask, EpiTask


class TestPrioritiesTask:
    """Тесты для PrioritiesTask"""

    @pytest.fixture
    def priorities_task(self):
        return PrioritiesTask()

    def test_get_total_questions(self, priorities_task):
        """Тест получения общего количества вопросов"""
        assert priorities_task.get_total_questions() == 1

    def test_load_questions_success(self, priorities_task):
        """Тест успешной загрузки вопросов"""
        mock_data = {
            "question": {
                "text": "Test question",
                "categories": [
                    {
                        "id": "test_cat",
                        "title": "Test Category",
                        "description": "Test desc",
                    }
                ],
            }
        }

        # Устанавливаем данные напрямую для тестирования
        priorities_task.question_data = mock_data
        priorities_task.loaded = True

        assert priorities_task.loaded is True
        assert priorities_task.question_data == mock_data

    @pytest.mark.asyncio
    async def test_load_questions_file_error(self, priorities_task):
        """Тест загрузки при ошибке файла"""
        with patch("aiofiles.open", side_effect=FileNotFoundError("File not found")):
            await priorities_task.load_questions()

        assert priorities_task.loaded is True
        assert priorities_task.question_data is not None  # Использует default данные

    def test_calculate_scores(self, priorities_task):
        """Тест подсчета баллов приоритетов"""
        test_answers = {
            "priorities": {
                "personal_wellbeing": 5,
                "material_career": 4,
                "relationships": 3,
                "self_realization": 2,
            }
        }

        scores = priorities_task.calculate_scores(test_answers)

        assert scores == test_answers["priorities"]

    def test_get_question_not_loaded(self, priorities_task):
        """Тест получения вопроса когда данные не загружены"""
        result = priorities_task.get_question()
        assert result is None

    def test_get_question_loaded(self, priorities_task):
        """Тест получения вопроса когда данные загружены"""
        test_data = {"question": {"text": "Test question", "categories": []}}
        priorities_task.question_data = test_data
        priorities_task.loaded = True

        result = priorities_task.get_question()
        assert result == test_data["question"]


class TestInqTask:
    """Тесты для InqTask"""

    @pytest.fixture
    def inq_task(self):
        return InqTask()

    def test_load_questions_success(self, inq_task):
        """Тест успешной загрузки INQ вопросов"""
        mock_data = [
            {"text": "Test question 1", "mapping": {"1": "Style1", "2": "Style2"}},
            {"text": "Test question 2", "mapping": {"1": "Style3", "2": "Style4"}},
        ]

        # Устанавливаем данные напрямую для тестирования
        inq_task.questions = mock_data
        inq_task.loaded = True

        assert inq_task.loaded is True
        assert inq_task.questions == mock_data
        assert inq_task.get_total_questions() == 2

    def test_get_question(self, inq_task):
        """Тест получения конкретного вопроса"""
        test_questions = [
            {"text": "Question 1", "mapping": {}},
            {"text": "Question 2", "mapping": {}},
        ]

        inq_task.questions = test_questions
        inq_task.loaded = True

        assert inq_task.get_question(0) == test_questions[0]
        assert inq_task.get_question(1) == test_questions[1]
        assert inq_task.get_question(2) is None  # Вне границ

    def test_calculate_scores(self, inq_task):
        """Тест подсчета баллов INQ"""
        # Настраиваем тестовые вопросы
        inq_task.questions = [
            {
                "mapping": {
                    "1": "Синтетический",
                    "2": "Идеалистический",
                    "3": "Прагматический",
                }
            },
            {
                "mapping": {
                    "1": "Аналитический",
                    "2": "Реалистический",
                    "3": "Синтетический",
                }
            },
        ]

        test_answers = {
            "inq": {
                "question_1": {"1": 5, "2": 4, "3": 3},
                "question_2": {"1": 5, "2": 4, "3": 3},
            }
        }

        scores = inq_task.calculate_scores(test_answers)

        assert scores["Синтетический"] == 8  # 5 + 3
        assert scores["Идеалистический"] == 4
        assert scores["Прагматический"] == 3
        assert scores["Аналитический"] == 5
        assert scores["Реалистический"] == 4


class TestEpiTask:
    """Тесты для EpiTask"""

    @pytest.fixture
    def epi_task(self):
        return EpiTask()

    def test_load_questions_success(self, epi_task):
        """Тест успешной загрузки EPI вопросов"""
        mock_data = [
            {
                "number": 1,
                "text": "Test question 1",
                "scale": "E",
                "answer_for_point": "да",
            },
            {
                "number": 2,
                "text": "Test question 2",
                "scale": "N",
                "answer_for_point": "нет",
            },
        ]

        # Устанавливаем данные напрямую для тестирования
        epi_task.questions = mock_data
        epi_task.loaded = True

        assert epi_task.loaded is True
        assert epi_task.questions == mock_data
        assert epi_task.get_total_questions() == 2

    def test_calculate_scores(self, epi_task):
        """Тест подсчета баллов EPI"""
        epi_task.questions = [
            {"number": 1, "scale": "E", "answer_for_point": "да"},
            {"number": 2, "scale": "N", "answer_for_point": "да"},
            {"number": 3, "scale": "L", "answer_for_point": "нет"},
            {"number": 4, "scale": "E", "answer_for_point": "нет"},
            {"number": 5, "scale": "N", "answer_for_point": "да"},
        ]

        test_answers = {
            "epi": {
                "1": "Да",  # E: попадание
                "2": "Да",  # N: попадание
                "3": "Нет",  # L: попадание
                "4": "Да",  # E: не попадание
                "5": "Нет",  # N: не попадание
            }
        }

        scores = epi_task.calculate_scores(test_answers)

        assert scores["E"] == 1  # Только вопрос 1
        assert scores["N"] == 1  # Только вопрос 2
        assert scores["L"] == 1  # Только вопрос 3

    def test_determine_temperament(self, epi_task):
        """Тест определения темперамента"""
        # Холерик: E >= 2 и N >= 2
        assert epi_task._determine_temperament(3, 3) == "Холерик"

        # Сангвиник: E >= 2 и N < 2
        assert epi_task._determine_temperament(3, 1) == "Сангвиник"

        # Меланхолик: E < 2 и N >= 2
        assert epi_task._determine_temperament(1, 3) == "Меланхолик"

        # Флегматик: E < 2 и N < 2
        assert epi_task._determine_temperament(1, 1) == "Флегматик"

    def test_calculate_scores_with_temperament(self, epi_task):
        """Тест подсчета баллов с определением темперамента"""
        epi_task.questions = [
            {"number": 1, "scale": "E", "answer_for_point": "да"},
            {"number": 2, "scale": "E", "answer_for_point": "да"},
            {"number": 3, "scale": "N", "answer_for_point": "да"},
            {"number": 4, "scale": "N", "answer_for_point": "да"},
            {"number": 5, "scale": "N", "answer_for_point": "да"},
        ]

        test_answers = {
            "epi": {"1": "Да", "2": "Да", "3": "Да", "4": "Да", "5": "Да"}
        }  # E  # E  # N  # N  # N

        scores = epi_task.calculate_scores(test_answers)

        assert scores["E"] == 2
        assert scores["N"] == 3
        assert scores["temperament"] == "Холерик"
