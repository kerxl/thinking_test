import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.core.task_manager import TaskManager
from src.core.task_models import PrioritiesTask, InqTask, EpiTask
from src.database.models import User
from config.const import TaskType, TaskSection


class TestIntegration:
    """Интеграционные тесты полного цикла тестирования"""

    @pytest.fixture
    def task_manager(self):
        """Настроенный TaskManager"""
        manager = TaskManager()

        # Инициализируем тестовые модели с минимальными данными
        manager.tasks[TaskType.priorities].loaded = True
        manager.tasks[TaskType.priorities].question_data = {
            "question": {
                "text": "Test priorities question",
                "categories": [
                    {"id": "personal_wellbeing", "title": "Личное благополучие"},
                    {"id": "material_career", "title": "Материальное развитие"},
                    {"id": "relationships", "title": "Отношения"},
                    {"id": "self_realization", "title": "Самореализация"},
                ],
            }
        }

        manager.tasks[TaskType.inq].loaded = True
        manager.tasks[TaskType.inq].questions = [
            {
                "text": "Test INQ question 1",
                "mapping": {
                    "1": "Синтетический",
                    "2": "Идеалистический",
                    "3": "Прагматический",
                    "4": "Аналитический",
                    "5": "Реалистический",
                },
            },
            {
                "text": "Test INQ question 2",
                "mapping": {
                    "1": "Реалистический",
                    "2": "Синтетический",
                    "3": "Идеалистический",
                    "4": "Прагматический",
                    "5": "Аналитический",
                },
            },
        ]

        manager.tasks[TaskType.epi].loaded = True
        manager.tasks[TaskType.epi].questions = [
            {"number": 1, "text": "EPI Question 1", "scale": "E", "answer_for_point": "да"},
            {"number": 2, "text": "EPI Question 2", "scale": "N", "answer_for_point": "да"},
            {"number": 3, "text": "EPI Question 3", "scale": "L", "answer_for_point": "нет"},
        ]

        return manager

    @pytest.fixture
    def mock_user(self, sample_user_data):
        """Мок пользователя"""
        user = Mock(spec=User)
        user.user_id = sample_user_data["user_id"]
        user.username = sample_user_data["username"]
        user.first_name = sample_user_data["first_name"]
        user.last_name = sample_user_data["last_name"]
        user.age = sample_user_data["age"]
        return user

    @pytest.mark.asyncio
    async def test_full_testing_cycle(self, task_manager, mock_user):
        """Тест полного цикла прохождения всех тестов"""

        # Мокаем update_user
        with patch("src.core.task_manager.update_user", new_callable=AsyncMock):

            # 1. Начинаем тестирование
            success = await task_manager.start_tasks(mock_user)
            assert success is True
            assert task_manager.get_current_task_type(mock_user.user_id) == TaskType.priorities.value

            # 2. Проходим тест приоритетов
            priorities_answers = [
                ("personal_wellbeing", 5),
                ("material_career", 4),
                ("relationships", 3),
                ("self_realization", 2),
            ]

            for category, score in priorities_answers:
                success, _ = await task_manager.process_priorities_answer(mock_user, category, score)
                assert success is True

            # Проверяем завершение теста приоритетов
            assert task_manager.is_priorities_task_completed(mock_user.user_id)

            # Переходим к следующему тесту
            await task_manager.move_to_next_task(mock_user.user_id)
            assert task_manager.get_current_task_type(mock_user.user_id) == TaskType.inq.value

            # 3. Проходим INQ тест (2 вопроса)
            for question_num in range(2):
                # Имитируем выбор вариантов в порядке 5-4-3-2-1
                for step, option in enumerate(["1", "2", "3", "4", "5"]):
                    success, _ = await task_manager.process_inq_answer(mock_user, option)
                    assert success is True

                # Проверяем завершение вопроса
                assert task_manager.is_inq_question_completed(mock_user.user_id, question_num)

                # Переходим к следующему вопросу (кроме последнего)
                if question_num < 1:
                    await task_manager.move_to_next_question(mock_user.user_id)

            # Переходим к EPI тесту
            await task_manager.move_to_next_task(mock_user.user_id)
            assert task_manager.get_current_task_type(mock_user.user_id) == TaskType.epi.value

            # 4. Проходим EPI тест (3 вопроса)
            epi_answers = ["Да", "Да", "Нет"]
            for answer in epi_answers:
                success, _ = await task_manager.process_epi_answer(mock_user, answer)
                assert success is True

            # 5. Переходим после EPI теста (имитируем завершение) - нужно значение > 3
            await task_manager.move_to_next_task(mock_user.user_id)  # Теперь current_task_type = 4
            
            # Проверяем что состояние правильно обновилось
            state = task_manager.get_task_state(mock_user.user_id)
            assert state["current_task_type"] == 4  # После move_to_next_task из EPI (3) стало 4
            
            # Проверяем что все тесты завершены (current_task_type > TaskType.epi.value (3))
            assert task_manager.is_all_tasks_completed(mock_user.user_id)
            
            # Завершаем все тесты и получаем результаты
            scores = await task_manager.complete_all_tasks(mock_user)

            # Проверяем наличие результатов
            assert isinstance(scores, dict)
            assert len(scores) > 0

    @pytest.mark.asyncio
    async def test_inq_back_functionality(self, task_manager, mock_user):
        """Тест функции возврата в INQ тесте"""

        with patch("src.core.task_manager.update_user", new_callable=AsyncMock):

            # Начинаем тестирование и переходим к INQ
            await task_manager.start_tasks(mock_user)
            await task_manager.move_to_next_task(mock_user.user_id)

            # Делаем несколько ответов
            await task_manager.process_inq_answer(mock_user, "1")  # 5 баллов
            await task_manager.process_inq_answer(mock_user, "2")  # 4 балла

            # Проверяем что в истории есть записи
            state = task_manager.get_task_state(mock_user.user_id)
            assert len(state["history"]) == 2

            # Делаем откат
            success, message, updated_state = await task_manager.go_back_question(mock_user)
            assert success is True

            # Проверяем что состояние изменилось
            state_after = task_manager.get_task_state(mock_user.user_id)
            assert len(state_after["history"]) == 1
            assert state_after["current_step"] == 1

    @pytest.mark.asyncio
    async def test_error_handling_invalid_answers(self, task_manager, mock_user):
        """Тест обработки ошибок при неверных ответах"""

        with patch("src.core.task_manager.update_user", new_callable=AsyncMock):

            await task_manager.start_tasks(mock_user)

            # Тест дублирующихся баллов в приоритетах
            await task_manager.process_priorities_answer(mock_user, "personal_wellbeing", 5)
            success, message = await task_manager.process_priorities_answer(mock_user, "material_career", 5)
            assert success is False
            assert "уже использован" in message

            # Переход к INQ тесту
            await task_manager.move_to_next_task(mock_user.user_id)

            # Тест дублирующихся опций в INQ
            await task_manager.process_inq_answer(mock_user, "1")
            success, message = await task_manager.process_inq_answer(mock_user, "1")
            assert success is False

            # Завершаем все INQ вопросы и переходим к EPI тесту
            await task_manager.move_to_next_task(mock_user.user_id)

            # Тест неверных ответов в EPI
            success, message = await task_manager.process_epi_answer(mock_user, "Может быть")
            assert success is False

    @pytest.mark.asyncio
    async def test_scoring_calculations(self, task_manager, mock_user):
        """Тест правильности подсчета баллов"""

        with patch("src.core.task_manager.update_user", new_callable=AsyncMock):

            await task_manager.start_tasks(mock_user)

            # Заполняем тестовые данные
            state = task_manager.get_task_state(mock_user.user_id)
            state["answers"] = {
                "priorities": {
                    "personal_wellbeing": 5,
                    "material_career": 4,
                    "relationships": 3,
                    "self_realization": 2,
                },
                "inq": {
                    "question_1": {"1": 5, "2": 4, "3": 3, "4": 2, "5": 1},
                    "question_2": {"1": 3, "2": 5, "3": 1, "4": 4, "5": 2},
                },
                "epi": {"1": "Да", "2": "Да", "3": "Нет"},  # E: попадание  # N: попадание  # L: попадание
            }

            # Получаем результаты
            scores = await task_manager.complete_all_tasks(mock_user)

            # Проверяем INQ баллы
            assert "Синтетический" in scores
            assert "Идеалистический" in scores
            # Проверяем INQ баллы с учетом правильной логики подсчета
            # question_1: {"1": 5, "2": 4, "3": 3, "4": 2, "5": 1} с mapping {"1": "Синтетический", "2": "Идеалистический", "3": "Прагматический", "4": "Аналитический", "5": "Реалистический"}
            # question_2: {"1": 3, "2": 5, "3": 1, "4": 4, "5": 2} с mapping {"1": "Реалистический", "2": "Синтетический", "3": "Идеалистический", "4": "Прагматический", "5": "Аналитический"}
            # Итого: Синтетический: 5+5=10, Идеалистический: 4+1=5, Прагматический: 3+4=7, Аналитический: 2+2=4, Реалистический: 1+3=4
            expected_synthetic = 10  # 5 (из q1 опция "1") + 5 (из q2 опция "2")
            expected_idealistic = 5   # 4 (из q1 опция "2") + 1 (из q2 опция "3")
            assert scores["Синтетический"] == expected_synthetic
            assert scores["Идеалистический"] == expected_idealistic

            # Проверяем EPI баллы
            assert scores["E"] == 1
            assert scores["N"] == 1
            assert scores["L"] == 1
            assert "temperament" in scores

    def test_task_state_management(self, task_manager, mock_user):
        """Тест управления состоянием задач"""

        # Проверяем пустое состояние
        assert task_manager.get_task_state(mock_user.user_id) is None

        # Создаем состояние
        task_manager.active_tasks[mock_user.user_id] = {
            "current_task_type": TaskType.inq.value,
            "current_question": 5,
            "current_step": 2,
            "answers": {},
            "history": [],
        }

        # Проверяем получение состояния
        state = task_manager.get_task_state(mock_user.user_id)
        assert state is not None
        assert state["current_task_type"] == TaskType.inq.value
        assert state["current_question"] == 5
        assert state["current_step"] == 2

        # Проверяем очистку состояния
        task_manager.clear_task_state(mock_user.user_id)
        assert task_manager.get_task_state(mock_user.user_id) is None
