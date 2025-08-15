import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.operations import get_or_create_user, update_user, init_db
from src.database.models import User


class TestDatabaseOperations:
    """Тесты для операций с базой данных"""

    @pytest.fixture
    async def mock_session(self):
        """Мок сессии базы данных"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.mark.asyncio
    async def test_init_db(self):
        """Тест инициализации базы данных"""
        with patch('src.database.operations.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            
            await init_db()
            
            mock_engine.begin.assert_called_once()
            mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio 
    async def test_get_or_create_user_existing(self):
        """Тест получения существующего пользователя"""
        # Создаем мок существующего пользователя
        existing_user = User(
            user_id=12345,
            username="existing_user",
            first_name="John",
            last_name="Doe"
        )
        
        with patch('src.database.operations.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_session
            
            # Мокаем результат запроса - пользователь найден
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = existing_user
            mock_session.execute.return_value = mock_result
            
            user = await get_or_create_user(
                user_id=12345,
                username="existing_user",
                first_name="John",
                last_name="Doe"
            )
            
            assert user == existing_user
            # Проверяем, что новый пользователь не создавался
            mock_session.add.assert_not_called()
            mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_user_new(self):
        """Тест создания нового пользователя"""
        with patch('src.database.operations.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_session
            
            # Мокаем результат запроса - пользователь не найден
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result
            
            user = await get_or_create_user(
                user_id=67890,
                username="new_user",
                first_name="Jane",
                last_name="Smith"
            )
            
            # Проверяем, что пользователь был создан
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_existing(self):
        """Тест обновления существующего пользователя"""
        existing_user = User(
            user_id=12345,
            username="test_user",
            first_name="John",
            last_name="Doe"
        )
        
        with patch('src.database.operations.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_session
            
            # Мокаем результат запроса - пользователь найден
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = existing_user
            mock_session.execute.return_value = mock_result
            
            updated_user = await update_user(
                user_id=12345,
                first_name="John Updated",
                age=30,
                current_task_type=2
            )
            
            assert updated_user == existing_user
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        """Тест обновления несуществующего пользователя"""
        with patch('src.database.operations.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_session
            
            # Мокаем результат запроса - пользователь не найден
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result
            
            result = await update_user(
                user_id=99999,
                first_name="Nonexistent User"
            )
            
            assert result is None
            mock_session.commit.assert_not_called()

    def test_user_model_methods(self):
        """Тест методов модели User"""
        user = User(
            user_id=12345,
            username="test_user",
            answers_json={
                "priorities": {"personal_wellbeing": 5},
                "inq": {"question_1": {"A": 5, "B": 4}},
                "epi": {"1": "Да", "2": "Нет"}
            },
            inq_scores_json={"Синтетический": 50, "Аналитический": 40},
            epi_scores_json={"E": 15, "N": 8, "L": 3},
            priorities_json={"personal_wellbeing": 5, "material_career": 4}
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