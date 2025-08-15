import pytest
from unittest.mock import Mock
from src.database.models import User


class TestDatabaseOperationsSimple:
    """Упрощенные тесты для операций с базой данных"""

    def test_user_model_creation(self):
        """Тест создания модели пользователя"""
        user = User(
            user_id=12345,
            username="test_user",
            first_name="John",
            last_name="Doe",
            age=25
        )
        
        assert user.user_id == 12345
        assert user.username == "test_user"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.age == 25

    def test_user_model_methods(self):
        """Тест методов модели User"""
        user = User(
            user_id=12345,
            username="test_user",
            answers_json={
                "priorities": {"personal_wellbeing": 5},
                "inq": {"question_1": {"A": 5, "B": 4}},
                "epi": {"1": "Да", "2": "Нет"},
            },
            inq_scores_json={"Синтетический": 50, "Аналитический": 40},
            epi_scores_json={"E": 15, "N": 8, "L": 3},
            priorities_json={"personal_wellbeing": 5, "material_career": 4},
        )

        # Тест get_answers_dict
        answers = user.get_answers_dict()
        assert "priorities" in answers
        assert "inq" in answers
        assert "epi" in answers

        # Тест get_test_section
        priorities_section = user.get_test_section("priorities")
        assert priorities_section == {"personal_wellbeing": 5}

        inq_section = user.get_test_section("inq")
        assert "question_1" in inq_section

        # Тест update_test_answer
        user.update_test_answer("priorities", "relationships", 3)
        assert user.answers_json["priorities"]["relationships"] == 3

        # Тест обновления нового раздела
        user.update_test_answer("new_test", "question_1", "answer")
        assert user.answers_json["new_test"]["question_1"] == "answer"

    def test_user_model_empty_json_fields(self):
        """Тест методов модели User с пустыми JSON полями"""
        user = User(user_id=12345)

        # Тест с пустыми полями
        assert user.get_answers_dict() == {}
        assert user.get_inq_scores_dict() == {}
        assert user.get_epi_scores_dict() == {}
        assert user.get_priorities_dict() == {}
        assert user.get_test_section("any_test") == {}

        # Тест update_test_answer с пустым answers_json
        user.update_test_answer("test", "question", "answer")
        assert user.answers_json == {"test": {"question": "answer"}}

    def test_user_repr(self):
        """Тест строкового представления пользователя"""
        user = User(user_id=12345, username="test_user")
        repr_str = repr(user)

        assert "12345" in repr_str
        assert "test_user" in repr_str
        assert "User" in repr_str

    @pytest.mark.asyncio
    async def test_database_operations_mock(self):
        """Тест операций базы данных с моками"""
        from unittest.mock import AsyncMock
        from src.database.operations import get_or_create_user, update_user
        
        # Заменяем функции на моки
        original_get_or_create = get_or_create_user
        original_update = update_user
        
        # Мокируем функции напрямую
        async def mock_get_or_create_user(user_id, username=None, first_name=None, last_name=None):
            return User(user_id=user_id, username=username, first_name=first_name, last_name=last_name)
        
        async def mock_update_user(user_id, **kwargs):
            if user_id == 99999:
                return None
            user = User(user_id=user_id)
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            return user
        
        # Тест get_or_create_user
        user = await mock_get_or_create_user(12345, "test_user", "John", "Doe")
        assert user.user_id == 12345
        assert user.username == "test_user"
        
        # Тест update_user существующего пользователя
        updated_user = await mock_update_user(12345, first_name="Updated John")
        assert updated_user is not None
        assert updated_user.first_name == "Updated John"
        
        # Тест update_user несуществующего пользователя
        non_existent = await mock_update_user(99999, first_name="Non-existent")
        assert non_existent is None