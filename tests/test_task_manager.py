import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.core.task_manager import TaskManager
from src.database.models import User
from config.const import TaskType, TaskSection


class TestTaskManager:
    """Тесты для TaskManager - основного компонента управления тестами"""

    @pytest.fixture
    def task_manager(self):
        return TaskManager()

    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.user_id = 12345
        user.username = "test_user"
        user.first_name = "Test"
        user.last_name = "User"
        user.age = 25
        return user

    @pytest.mark.asyncio
    async def test_start_tests(self, task_manager, mock_user):
        """Тест начала тестирования"""
        # Mock update_user function
        import src.core.task_manager

        src.core.task_manager.update_user = AsyncMock()

        result = await task_manager.start_tasks(mock_user)

        assert result is True
        assert mock_user.user_id in task_manager.active_tasks
        task_state = task_manager.active_tasks[mock_user.user_id]
        assert task_state["current_task_type"] == TaskType.priorities.value
        assert task_state["current_question"] == 0
        assert task_state["current_step"] == 0
        assert task_state["answers"] == {}

    def test_get_task_state(self, task_manager, mock_user):
        """Тест получения состояния задачи"""
        # Инициализируем состояние
        task_manager.active_tasks[mock_user.user_id] = {
            "current_task_type": TaskType.inq.value,
            "current_question": 5,
            "current_step": 2,
        }

        state = task_manager.get_task_state(mock_user.user_id)
        assert state["current_task_type"] == TaskType.inq.value
        assert state["current_question"] == 5
        assert state["current_step"] == 2

    def test_clear_task_state(self, task_manager, mock_user):
        """Тест очистки состояния задачи"""
        task_manager.active_tasks[mock_user.user_id] = {"test": "data"}

        task_manager.clear_task_state(mock_user.user_id)

        assert mock_user.user_id not in task_manager.active_tasks

    def test_is_priorities_task_completed(self, task_manager, mock_user):
        """Тест проверки завершения теста приоритетов"""
        # Неполный тест
        task_manager.active_tasks[mock_user.user_id] = {
            "answers": {TaskSection.priorities.value: {"personal_wellbeing": 5, "material_career": 4}}
        }

        assert not task_manager.is_priorities_task_completed(mock_user.user_id)

        # Полный тест
        task_manager.active_tasks[mock_user.user_id]["answers"][TaskSection.priorities.value].update(
            {"relationships": 3, "self_realization": 2}
        )

        assert task_manager.is_priorities_task_completed(mock_user.user_id)

    @pytest.mark.asyncio
    async def test_process_priorities_answer(self, task_manager, mock_user):
        """Тест обработки ответа теста приоритетов"""
        # Mock update_user function
        import src.core.task_manager

        src.core.task_manager.update_user = AsyncMock()

        # Инициализируем состояние
        task_manager.active_tasks[mock_user.user_id] = {
            "current_task_type": TaskType.priorities.value,
            "current_step": 0,
            "answers": {},
        }

        success, message = await task_manager.process_priorities_answer(mock_user, "personal_wellbeing", 5)

        assert success is True
        answers = task_manager.active_tasks[mock_user.user_id]["answers"]
        assert answers[TaskSection.priorities.value]["personal_wellbeing"] == 5
        assert task_manager.active_tasks[mock_user.user_id]["current_step"] == 1

    @pytest.mark.asyncio
    async def test_process_priorities_answer_duplicate_score(self, task_manager, mock_user):
        """Тест обработки дублирующегося балла в тесте приоритетов"""
        # Инициализируем состояние с уже существующим баллом
        task_manager.active_tasks[mock_user.user_id] = {
            "current_task_type": TaskType.priorities.value,
            "current_step": 1,
            "answers": {TaskSection.priorities.value: {"personal_wellbeing": 5}},
        }

        success, message = await task_manager.process_priorities_answer(
            mock_user, "material_career", 5  # Повторный балл 5
        )

        assert success is False
        assert "уже использован" in message

    def test_get_inq_available_options(self, task_manager, mock_user):
        """Тест получения доступных опций для INQ теста"""
        # Пустое состояние - все опции доступны
        task_manager.active_tasks[mock_user.user_id] = {"answers": {}}

        options = task_manager.get_inq_available_options(mock_user.user_id, 0)
        assert "1" in options
        assert "2" in options
        assert "3" in options
        assert "4" in options
        assert "5" in options

        # Некоторые опции уже использованы
        task_manager.active_tasks[mock_user.user_id]["answers"]["inq"] = {"question_1": {"1": 5, "3": 4}}

        options = task_manager.get_inq_available_options(mock_user.user_id, 0)
        assert "1" not in options
        assert "2" in options
        assert "3" not in options
        assert "4" in options
        assert "5" in options

    @pytest.mark.asyncio
    async def test_process_epi_answer(self, task_manager, mock_user):
        """Тест обработки ответа EPI теста"""
        import src.core.task_manager

        src.core.task_manager.update_user = AsyncMock()

        task_manager.active_tasks[mock_user.user_id] = {
            "current_task_type": TaskType.epi.value,
            "current_question": 0,
            "answers": {},
        }

        success, message = await task_manager.process_epi_answer(mock_user, "Да")

        assert success is True
        answers = task_manager.active_tasks[mock_user.user_id]["answers"]
        assert answers[TaskSection.epi.value]["1"] == "Да"
        assert task_manager.active_tasks[mock_user.user_id]["current_question"] == 1
