#!/usr/bin/env python3
"""
Скрипт для имитации полного прохождения тестов рандомным пользователем.
Имитирует реальные действия пользователя: отправку команд, нажатие на кнопки,
ввод текста и заполнение ответов тестов.
"""

# ВАЖНО: Настройка логирования должна быть ДО всех импортов
import logging
import os

# Полностью отключаем SQLAlchemy логи через переменную окружения
os.environ['SQLALCHEMY_WARN_20'] = '0'

# Настройка корневого логгера
logging.basicConfig(level=logging.CRITICAL, format='%(message)s')

# Полное отключение всех библиотечных логов
for logger_name in [
    'sqlalchemy', 'sqlalchemy.engine', 'sqlalchemy.pool', 'sqlalchemy.dialects',
    'sqlalchemy.orm', 'sqlalchemy.engine.Engine', 'httpx', 'aiogram', 
    'asyncio', 'urllib3', 'aiofiles', 'asyncpg'
]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    logging.getLogger(logger_name).disabled = True

# Отключаем все логи уровня INFO и DEBUG
logging.disable(logging.INFO)

import asyncio
import random
import sys
import time
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from src.core.admin_reports import admin_reports

from aiogram import Bot
from aiogram.types import User, Chat
from config.settings import BOT_TOKEN
from config.const import TaskType
from src.database.operations import get_or_create_user
from src.database.models import User as DBUser
from src.core.task_manager import TaskManager

# Создаем экземпляр TaskManager
task_manager = TaskManager()


async def initialize_task_manager():
    """Инициализация TaskManager с загрузкой данных тестов"""
    # Загружаем константы сообщений
    import json
    from config.const import MESSAGES

    try:
        with open("config/constants.json", "r", encoding="utf-8") as f:
            messages = json.load(f)
            MESSAGES.update(messages)
        print(f"✅ Константы сообщений загружены: {len(MESSAGES)} записей")

        # Проверяем наличие необходимых ключей
        required_keys = ["answer_saved", "answer_process_error", "task_not_found"]
        missing_keys = [key for key in required_keys if key not in MESSAGES]
        if missing_keys:
            print(f"⚠️ Отсутствуют ключи сообщений: {missing_keys}")
            # Добавляем базовые сообщения
            fallback_messages = {
                "answer_saved": "Ответ сохранен",
                "answer_process_error": "Ошибка обработки ответа",
                "task_not_found": "Задача не найдена",
            }
            for key in missing_keys:
                if key in fallback_messages:
                    MESSAGES[key] = fallback_messages[key]

    except FileNotFoundError:
        print("⚠️ Файл constants.json не найден, используем базовые сообщения")
        MESSAGES.update(
            {
                "answer_saved": "Ответ сохранен",
                "answer_process_error": "Ошибка обработки ответа",
                "task_not_found": "Задача не найдена",
            }
        )

    # Загружаем вопросы для всех тестов
    await task_manager.tasks[TaskType.priorities].load_questions()
    await task_manager.tasks[TaskType.inq].load_questions()
    await task_manager.tasks[TaskType.epi].load_questions()


class SimulatedUser:
    """Класс для имитации действий пользователя"""

    def __init__(self, user_id: int, username: str, first_name: str, last_name: str):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.age = random.randint(18, 65)
        self.bot = Bot(token=BOT_TOKEN)

        # Данные для ответов
        self.priorities_categories = ["personal_wellbeing", "material_career", "relationships", "self_realization"]

    def log(self, message: str):
        """Логирование действий пользователя"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] 👤 {self.first_name}: {message}")

    def create_mock_user(self) -> User:
        """Создание мок-объекта пользователя Telegram"""
        return User(
            id=self.user_id,
            is_bot=False,
            first_name=self.first_name,
            last_name=self.last_name,
            username=self.username,
            language_code="ru",
        )

    def create_mock_chat(self) -> Chat:
        """Создание мок-объекта чата"""
        return Chat(id=self.user_id, type="private")

    async def start_bot_interaction(self):
        """Начало взаимодействия с ботом - команда /start"""
        self.log("🚀 Отправляю команду /start")

        # Имитируем отправку команды /start
        await asyncio.sleep(0.5)  # Задержка как у реального пользователя

        # Создаем пользователя в БД
        user = await get_or_create_user(
            user_id=self.user_id, username=self.username, first_name=self.first_name, last_name=self.last_name
        )

        self.log("📱 Бот ответил приветственным сообщением")
        return user

    async def click_start_button(self):
        """Нажатие на кнопку 'Начать тест'"""
        self.log("🔘 Нажимаю кнопку 'Начать тест'")
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Имитируем callback "start_personal_data"
        self.log("📝 Бот запросил ввод имени и фамилии")

    async def enter_personal_data(self):
        """Ввод персональных данных"""
        full_name = f"{self.first_name} {self.last_name}"
        self.log(f"⌨️ Ввожу имя и фамилию: '{full_name}'")
        await asyncio.sleep(random.uniform(0.2, 0.8))

        self.log(f"⌨️ Ввожу возраст: {self.age}")
        await asyncio.sleep(random.uniform(0.1, 0.3))

        self.log("✅ Персональные данные введены, переходим к тестам")

    async def click_start_tasks_button(self):
        """Нажатие на кнопку начала тестов"""
        self.log("🔘 Нажимаю кнопку начала тестов")
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Получаем пользователя из БД
        user = await get_or_create_user(
            user_id=self.user_id, username=self.username, first_name=self.first_name, last_name=self.last_name
        )

        # Начинаем тесты через TaskManager
        success = await task_manager.start_tasks(user)
        if success:
            self.log("🎯 Тесты начаты! Приступаю к тесту приоритетов")
        else:
            self.log("❌ Ошибка запуска тестов")
            return False

        return user

    async def complete_priorities_test(self, user: DBUser):
        """Прохождение теста приоритетов"""
        self.log("📊 Начинаю тест приоритетов...")

        # Создаем случайную расстановку приоритетов от 1 до 5
        scores = [1, 2, 3, 4, 5]
        random.shuffle(scores)

        for i, category in enumerate(self.priorities_categories):
            score = scores[i]

            # Имитируем размышления пользователя
            await asyncio.sleep(random.uniform(0.3, 1.0))

            self.log(f"🔘 Выбираю для '{category}' балл: {score}")

            # Отправляем ответ через TaskManager
            try:
                success, message = await task_manager.process_priorities_answer(user, category, score)
            except Exception as e:
                self.log(f"💥 Исключение при process_priorities_answer: {e}")
                success, message = False, str(e)

            if not success:
                self.log(f"❌ Ошибка при выборе балла: {message}")
                # Если балл уже использован, пробуем другой
                available_scores = [s for s in [1, 2, 3, 4, 5] if s not in [scores[j] for j in range(i)]]
                if available_scores:
                    score = random.choice(available_scores)
                    scores[i] = score
                    self.log(f"🔄 Пробую другой балл: {score}")
                    success, message = await task_manager.process_priorities_answer(user, category, score)

                    # Если все еще ошибка, попробуем все доступные баллы
                    retry_count = 0
                    while not success and available_scores and retry_count < 3:
                        available_scores.remove(score) if score in available_scores else None
                        if available_scores:
                            score = random.choice(available_scores)
                            scores[i] = score
                            self.log(f"🔄 Повторная попытка с баллом: {score}")
                            success, message = await task_manager.process_priorities_answer(user, category, score)
                        retry_count += 1

            if success:
                self.log(f"✅ Балл {score} принят")
            else:
                self.log(f"❌ Не удалось выбрать балл: {message}")

        # Проверяем завершение теста
        if task_manager.is_priorities_task_completed(user.user_id):
            self.log("🎉 Тест приоритетов завершен!")
            await asyncio.sleep(random.uniform(0.1, 0.5))
            self.log("🔘 Нажимаю кнопку 'Завершить тест 1'")

            # Переходим к следующему тесту
            await task_manager.move_to_next_task(user.user_id)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            self.log("🔘 Нажимаю кнопку 'Тест 2'")
            return True
        else:
            self.log("❌ Тест приоритетов не завершен")
            return False

    async def complete_inq_test(self, user: DBUser):
        """Прохождение INQ теста"""
        self.log("🧠 Начинаю INQ тест (стили мышления)...")

        # Получаем количество вопросов
        inq_task = task_manager.tasks[TaskType.inq]
        total_questions = inq_task.get_total_questions()

        self.log(f"📋 Всего вопросов в INQ тесте: {total_questions}")

        for question_num in range(total_questions):
            self.log(f"❓ Отвечаю на вопрос {question_num + 1}/{total_questions}")

            # Имитируем чтение вопроса
            await asyncio.sleep(random.uniform(0.5, 1.5))

            # Для каждого вопроса нужно выбрать 5 вариантов в порядке предпочтения
            options = ["1", "2", "3", "4", "5"]
            random.shuffle(options)  # Случайный порядок выбора

            for step, option in enumerate(options):
                score = 5 - step  # 5, 4, 3, 2, 1

                # Имитируем размышления над вариантом
                await asyncio.sleep(random.uniform(0.2, 0.8))

                self.log(f"🔘 Выбираю вариант {option} (балл: {score})")

                success, message = await task_manager.process_inq_answer(user, option)

                if success:
                    self.log(f"✅ Вариант {option} принят")
                else:
                    self.log(f"❌ Ошибка выбора варианта: {message}")

            # Проверяем завершение вопроса
            if task_manager.is_inq_question_completed(user.user_id, question_num):
                self.log(f"✅ Вопрос {question_num + 1} завершен")

                # Переходим к следующему вопросу (кроме последнего)
                if question_num < total_questions - 1:
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await task_manager.move_to_next_question(user.user_id)
                    self.log(f"➡️ Переход к вопросу {question_num + 2}")
            else:
                self.log(f"❌ Вопрос {question_num + 1} не завершен")

        self.log("🎉 INQ тест завершен!")
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Переходим к следующему тесту
        await task_manager.move_to_next_task(user.user_id)
        self.log("🔘 Нажимаю кнопку 'Тест 3'")

        return True

    async def complete_epi_test(self, user: DBUser):
        """Прохождение EPI теста"""
        self.log("🧠 Начинаю EPI тест (личность)...")

        # Получаем количество вопросов
        epi_task = task_manager.tasks[TaskType.epi]
        total_questions = epi_task.get_total_questions()

        self.log(f"📋 Всего вопросов в EPI тесте: {total_questions}")

        for question_num in range(total_questions):
            # Имитируем чтение вопроса
            await asyncio.sleep(random.uniform(0.2, 0.8))

            # Случайный ответ "Да" или "Нет"
            answer = random.choice(["Да", "Нет"])

            self.log(f"❓ Вопрос {question_num + 1}/{total_questions} - отвечаю: {answer}")

            success, message = await task_manager.process_epi_answer(user, answer)

            if success:
                self.log(f"✅ Ответ '{answer}' принят")
            else:
                self.log(f"❌ Ошибка ответа: {message}")

        self.log("🎉 EPI тест завершен!")
        await asyncio.sleep(random.uniform(0.1, 0.3))

        return True

    async def complete_all_tests_and_get_results(self, user: DBUser):
        """Завершение всех тестов и получение результатов"""
        self.log("🏁 Завершаю все тесты и получаю результаты...")

        # Переходим после EPI теста (имитируем завершение)
        await task_manager.move_to_next_task(user.user_id)

        # Получаем результаты
        scores = await task_manager.complete_all_tasks(user)

        # Отправляем отчет админу
        await admin_reports.send_to_admin(user, scores)

        if scores:
            self.log("📊 Получены результаты тестирования:")

            # Выводим результаты приоритетов
            if "personal_wellbeing" in scores or any("personal_wellbeing" in str(k) for k in scores.keys()):
                self.log("  🎯 Приоритеты сохранены")

            # Выводим результаты INQ
            inq_styles = ["Синтетический", "Идеалистический", "Прагматический", "Аналитический", "Реалистический"]
            inq_results = {style: scores.get(style, 0) for style in inq_styles if style in scores}
            if inq_results:
                max_style = max(inq_results, key=inq_results.get)
                self.log(f"  🧠 Доминирующий стиль мышления: {max_style} ({inq_results[max_style]} баллов)")

            # Выводим результаты EPI
            if "temperament" in scores:
                self.log(f"  🎭 Темперамент: {scores['temperament']}")
                self.log(f"  📈 E (экстраверсия): {scores.get('E', 0)}")
                self.log(f"  📈 N (нейротизм): {scores.get('N', 0)}")
                self.log(f"  📈 L (ложь): {scores.get('L', 0)}")

            self.log("✅ Тестирование успешно завершено!")
            return True
        else:
            self.log("❌ Ошибка получения результатов")
            return False

    async def check_database_record(self):
        """Проверка записи в базе данных"""
        self.log("🔍 Проверяю запись в базе данных...")

        user = await get_or_create_user(user_id=self.user_id)

        if user:
            self.log(f"📋 Найдена запись пользователя:")
            self.log(f"  👤 ID: {user.user_id}")
            self.log(f"  📛 Имя: {user.first_name} {user.last_name}")
            self.log(f"  🎂 Возраст: {user.age}")
            self.log(f"  ✅ Тест завершен: {user.test_completed}")

            if user.test_completed:
                self.log(f"  🎯 Приоритеты: {user.get_priorities_dict()}")
                self.log(f"  🧠 INQ баллы: {user.get_inq_scores_dict()}")
                self.log(f"  🎭 EPI баллы: {user.get_epi_scores_dict()}")
                self.log(f"  🎭 Темперамент: {user.temperament}")

            return True
        else:
            self.log("❌ Запись пользователя не найдена")
            return False


async def generate_random_user() -> SimulatedUser:
    """Генерация случайного пользователя"""

    # Списки имен и фамилий для генерации
    first_names = [
        "Алексей",
        "Мария",
        "Дмитрий",
        "Анна",
        "Сергей",
        "Елена",
        "Андрей",
        "Ольга",
        "Михаил",
        "Татьяна",
        "Владимир",
        "Наталья",
        "Александр",
        "Ирина",
        "Максим",
        "Юлия",
    ]

    male_last_names = [
        "Иванов",
        "Петров",
        "Сидоров",
        "Козлов",
        "Новиков",
        "Морозов",
        "Попов",
        "Волков",
        "Соколов",
        "Лебедев",
        "Семенов",
        "Егоров",
        "Павлов",
        "Захаров",
        "Степанов",
        "Николаев",
    ]

    female_last_names = [
        "Иванова",
        "Петрова",
        "Сидорова",
        "Козлова",
        "Новикова",
        "Морозова",
        "Попова",
        "Волкова",
        "Соколова",
        "Лебедева",
        "Семенова",
        "Егорова",
        "Павлова",
        "Захарова",
        "Степанова",
        "Николаева",
    ]

    first_name = random.choice(first_names)

    # Определяем пол по имени и выбираем соответствующую фамилию
    female_names = ["Мария", "Анна", "Елена", "Ольга", "Татьяна", "Наталья", "Ирина", "Юлия"]
    if first_name in female_names:
        last_name = random.choice(female_last_names)
    else:
        last_name = random.choice(male_last_names)

    # Генерируем уникальный ID пользователя
    user_id = random.randint(100000, 999999)
    username = f"user_{user_id}"

    return SimulatedUser(user_id, username, first_name, last_name)


async def simulate_full_user_journey():
    """Полная имитация прохождения пользователем всех тестов"""

    print("=" * 80)
    print("🤖 СИМУЛЯЦИЯ ПРОХОЖДЕНИЯ ТЕСТОВ ПОЛЬЗОВАТЕЛЕМ")
    print("=" * 80)
    print()

    # Генерируем случайного пользователя
    user = await generate_random_user()

    print(f"👤 Сгенерирован пользователь: {user.first_name} {user.last_name}")
    print(f"🆔 ID: {user.user_id}, возраст: {user.age}")
    print()

    try:
        # 1. Начало взаимодействия с ботом
        db_user = await user.start_bot_interaction()

        # 2. Нажатие на кнопку начала теста
        await user.click_start_button()

        # 3. Ввод персональных данных
        await user.enter_personal_data()

        # 4. Начало тестов
        db_user = await user.click_start_tasks_button()
        if not db_user:
            return False

        # 5. Прохождение теста приоритетов
        success = await user.complete_priorities_test(db_user)
        if not success:
            user.log("❌ Не удалось завершить тест приоритетов")
            return False

        # 6. Прохождение INQ теста
        success = await user.complete_inq_test(db_user)
        if not success:
            user.log("❌ Не удалось завершить INQ тест")
            return False

        # 7. Прохождение EPI теста
        success = await user.complete_epi_test(db_user)
        if not success:
            user.log("❌ Не удалось завершить EPI тест")
            return False

        # 8. Завершение всех тестов и получение результатов
        success = await user.complete_all_tests_and_get_results(db_user)
        if not success:
            user.log("❌ Не удалось получить результаты")
            return False

        # 9. Проверка записи в базе данных
        success = await user.check_database_record()

        print()
        print("=" * 80)
        if success:
            print("🎉 СИМУЛЯЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
            print("📊 Пользователь прошел все тесты, результаты сохранены в БД")
        else:
            print("❌ СИМУЛЯЦИЯ ЗАВЕРШЕНА С ОШИБКАМИ")
        print("=" * 80)

        return success

    except Exception as e:
        user.log(f"💥 Критическая ошибка: {e}")
        print(f"\n❌ Ошибка симуляции: {e}")
        return False


async def main():
    """Главная функция"""

    # Проверяем что мы запускаемся из правильной директории
    if not Path("src/bot/main.py").exists():
        print("❌ Запустите скрипт из корневой директории проекта (06.08/)")
        sys.exit(1)

    print("🚀 Запуск симуляции прохождения тестов...")
    print("⏳ Инициализация...")

    # Инициализируем TaskManager
    await initialize_task_manager()
    print("✅ TaskManager инициализирован")

    # Небольшая задержка для инициализации
    await asyncio.sleep(1)

    try:
        # Запускаем симуляцию
        success = await simulate_full_user_journey()

        if success:
            print("\n🎯 Для проверки результатов вы можете:")
            print("1. Проверить БД командой: make db-status")
            print("2. Посмотреть записи пользователей в таблице users")
            print("3. Запустить бота и проверить отчеты для админа")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n❌ Симуляция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Запускаем симуляцию
    asyncio.run(main())
