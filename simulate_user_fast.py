#!/usr/bin/env python3
"""
Быстрая версия скрипта симуляции для демонстрации.
Проходит только несколько вопросов из каждого теста для ускорения.
"""

import asyncio
import random
import sys
import time
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

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
    except FileNotFoundError:
        print("⚠️ Файл constants.json не найден, используем базовые сообщения")
        MESSAGES.update({
            "answer_saved": "Ответ сохранен",
            "answer_process_error": "Ошибка обработки ответа",
            "task_not_found": "Задача не найдена"
        })
    
    # Загружаем вопросы для всех тестов
    await task_manager.tasks[TaskType.priorities].load_questions()
    await task_manager.tasks[TaskType.inq].load_questions()
    await task_manager.tasks[TaskType.epi].load_questions()

class FastSimulatedUser:
    """Быстрая версия симуляции пользователя"""
    
    def __init__(self, user_id: int, username: str, first_name: str, last_name: str):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.age = random.randint(18, 65)
        
        self.priorities_categories = [
            "personal_wellbeing",
            "material_career", 
            "relationships",
            "self_realization"
        ]
        
    def log(self, message: str):
        """Логирование действий пользователя"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] 👤 {self.first_name}: {message}")
    
    async def run_simulation(self):
        """Быстрая симуляция прохождения тестов"""
        
        self.log("🚀 Начинаю быструю симуляцию тестирования")
        
        # 1. Создание пользователя
        user = await get_or_create_user(
            user_id=self.user_id,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name
        )
        self.log(f"👤 Создан пользователь в БД (ID: {user.user_id})")
        
        # 2. Начинаем тесты
        success = await task_manager.start_tasks(user)
        if not success:
            self.log("❌ Ошибка запуска тестов")
            return False
        
        self.log("🎯 Тесты начаты!")
        
        # 3. Проходим тест приоритетов
        self.log("📊 Прохожу тест приоритетов...")
        scores = [1, 2, 3, 4, 5]
        random.shuffle(scores)
        
        for i, category in enumerate(self.priorities_categories):
            score = scores[i]
            success, message = await task_manager.process_priorities_answer(user, category, score)
            if success:
                self.log(f"✅ {category}: {score} баллов")
            else:
                self.log(f"❌ Ошибка: {message}")
        
        if not task_manager.is_priorities_task_completed(user.user_id):
            self.log("❌ Тест приоритетов не завершен")
            return False
        
        await task_manager.move_to_next_task(user.user_id)
        self.log("🎉 Тест приоритетов завершен! Переход к INQ тесту")
        
        # 4. Проходим INQ тест (только первые 3 вопроса для скорости)
        self.log("🧠 Прохожу INQ тест (сокращенный)...")
        
        max_questions = min(3, task_manager.tasks[TaskType.inq].get_total_questions())
        
        for question_num in range(max_questions):
            self.log(f"❓ INQ вопрос {question_num + 1}/{max_questions}")
            
            # Выбираем варианты в случайном порядке
            options = ["1", "2", "3", "4", "5"]
            random.shuffle(options)
            
            for step, option in enumerate(options):
                success, message = await task_manager.process_inq_answer(user, option)
                if success:
                    self.log(f"✅ Вариант {option} принят")
                else:
                    self.log(f"❌ Ошибка: {message}")
            
            # Переходим к следующему вопросу
            if question_num < max_questions - 1:
                await task_manager.move_to_next_question(user.user_id)
        
        await task_manager.move_to_next_task(user.user_id)
        self.log("🎉 INQ тест завершен! Переход к EPI тесту")
        
        # 5. Проходим EPI тест (только первые 10 вопросов для скорости)
        self.log("🧠 Прохожу EPI тест (сокращенный)...")
        
        max_epi_questions = min(10, task_manager.tasks[TaskType.epi].get_total_questions())
        
        for question_num in range(max_epi_questions):
            answer = random.choice(["Да", "Нет"])
            success, message = await task_manager.process_epi_answer(user, answer)
            if success:
                self.log(f"✅ Вопрос {question_num + 1}: {answer}")
            else:
                self.log(f"❌ Ошибка: {message}")
        
        self.log("🎉 EPI тест завершен!")
        
        # 6. Завершаем и получаем результаты
        await task_manager.move_to_next_task(user.user_id)
        scores = await task_manager.complete_all_tasks(user)
        
        if scores:
            self.log("📊 Получены результаты:")
            
            # INQ результаты
            inq_styles = ["Синтетический", "Идеалистический", "Прагматический", "Аналитический", "Реалистический"]
            inq_results = {style: scores.get(style, 0) for style in inq_styles if style in scores}
            if inq_results:
                max_style = max(inq_results, key=inq_results.get)
                self.log(f"  🧠 Доминирующий стиль: {max_style} ({inq_results[max_style]} баллов)")
            
            # EPI результаты
            if "temperament" in scores:
                self.log(f"  🎭 Темперамент: {scores['temperament']}")
            
            self.log("✅ Симуляция завершена успешно!")
            return True
        else:
            self.log("❌ Ошибка получения результатов")
            return False

async def generate_random_user():
    """Генерация случайного пользователя"""
    first_names = ["Алексей", "Мария", "Дмитрий", "Анна", "Сергей", "Елена"]
    last_names = ["Иванов", "Петрова", "Сидоров", "Козлова", "Новиков", "Морозова"]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    user_id = random.randint(100000, 999999)
    username = f"user_{user_id}"
    
    return FastSimulatedUser(user_id, username, first_name, last_name)

async def main():
    """Главная функция быстрой симуляции"""
    
    print("🚀 БЫСТРАЯ СИМУЛЯЦИЯ ПРОХОЖДЕНИЯ ТЕСТОВ")
    print("=" * 50)
    
    # Инициализация
    await initialize_task_manager()
    print("✅ Система инициализирована\n")
    
    # Генерируем пользователя
    user = await generate_random_user()
    print(f"👤 Пользователь: {user.first_name} {user.last_name} (ID: {user.user_id})")
    print(f"🎂 Возраст: {user.age}\n")
    
    # Запускаем симуляцию
    try:
        success = await user.run_simulation()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 СИМУЛЯЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
            print("📊 Данные пользователя сохранены в БД")
            print("\n🔍 Для проверки используйте:")
            print("  - make db-status")
            print("  - Просмотр таблицы users в БД")
        else:
            print("❌ СИМУЛЯЦИЯ ЗАВЕРШЕНА С ОШИБКАМИ")
        print("=" * 50)
        
        return success
        
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    # Проверяем что мы запускаемся из правильной директории
    if not Path("src/bot/main.py").exists():
        print("❌ Запустите скрипт из корневой директории проекта (06.08/)")
        sys.exit(1)
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Симуляция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)