import logging
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING

from config.const import (
    MESSAGES,
    TaskSection,
    AnswerOptions,
    TaskType,
    TaskEntity,
    TaskAnswersLimit,
    INQ_LENGTH_SCORES_PER_QUESTION,
    INQ_SCORES_PER_QUESTION,
    PRIORITIES_LENGTH_SCORES_PER_QUESTION,
    PRIORITIES_SCORES_PER_QUESTION,
)
from src.database.operations import update_user

if TYPE_CHECKING:
    from src.database.models import User

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self):
        self.active_tasks = {}
        self.pending_saves = {}  # Пользователи с несохраненными изменениями в памяти
        self.cached_users = {}  # Кэш пользователей для избежания повторных запросов к БД
        self.tasks = {
            TaskType.priorities: TaskEntity.priorities.value,
            TaskType.inq: TaskEntity.inq.value,
            TaskType.epi: TaskEntity.epi.value,
        }

    async def start_tasks(self, user: "User") -> bool:
        try:
            await update_user(
                user_id=user.user_id,
                current_task_type=1,
                current_question=0,
                current_step=0,
                test_completed=False,
                answers_json={},
            )

            self.active_tasks[user.user_id] = {
                "current_task_type": TaskType.priorities.value,
                "current_question": 0,
                "current_step": 0,
                "answers": {},
                "history": [],
            }

            logger.info(f"Тесты начаты для пользователя {user.user_id}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при начале тестов: {e}")
            return False

    def get_task_state(self, user_id: int) -> Optional[Dict]:
        return self.active_tasks.get(user_id)

    def clear_task_state(self, user_id: int):
        if user_id in self.active_tasks:
            del self.active_tasks[user_id]
        if user_id in self.pending_saves:
            del self.pending_saves[user_id]
        if user_id in self.cached_users:
            del self.cached_users[user_id]
    
    async def get_cached_user(self, user_id: int, username: str = None) -> "User":
        """Получает пользователя из кэша или базы данных"""
        if user_id in self.cached_users:
            return self.cached_users[user_id]
        
        from src.database.operations import get_or_create_user
        user = await get_or_create_user(user_id, username)
        self.cached_users[user_id] = user
        return user
    
    def mark_for_save(self, user_id: int):
        """Отмечает пользователя как имеющего несохраненные изменения"""
        self.pending_saves[user_id] = True
    
    async def save_pending_changes(self, user_id: int, force: bool = False):
        """Сохраняет все несохраненные изменения пользователя в БД"""
        if user_id not in self.pending_saves and not force:
            return
        
        task_state = self.get_task_state(user_id)
        if task_state:
            await update_user(
                user_id=user_id,
                current_task_type=task_state["current_task_type"],
                current_question=task_state["current_question"],
                current_step=task_state["current_step"],
                answers_json=task_state["answers"],
            )
            if user_id in self.pending_saves:
                del self.pending_saves[user_id]
            logger.info(f"Сохранены отложенные изменения для пользователя {user_id}")

    def get_current_task_type(self, user_id: int) -> int:
        state = self.get_task_state(user_id)
        return state["current_task_type"] if state else TaskType.priorities.value

    def is_all_tasks_completed(self, user_id: int) -> bool:
        state = self.get_task_state(user_id)
        if not state:
            return False
        return state["current_task_type"] > TaskType.epi.value

    async def process_priorities_answer(
        self, user: "User", category_id: str, score: int
    ) -> Tuple[bool, str]:
        try:
            task_state = self.get_task_state(user.user_id)
            if not task_state:
                return False, MESSAGES["task_not_found"]

            if task_state["current_task_type"] != TaskType.priorities.value:
                return False, MESSAGES["task_incorrect"]

            if TaskSection.priorities.value not in task_state["answers"]:
                task_state["answers"][TaskSection.priorities.value] = {}

            used_scores = set(
                task_state["answers"][TaskSection.priorities.value].values()
            )
            if score in used_scores:
                return False, f"Балл {score} уже использован"

            task_state["answers"][TaskSection.priorities.value][category_id] = score
            task_state["current_step"] += 1

            task_state["history"].append(
                {
                    "task": TaskType.priorities.value,
                    "category_id": category_id,
                    "score": score,
                }
            )

            # Отмечаем для отложенного сохранения
            self.mark_for_save(user.user_id)

            logger.info(
                f"Ответ в тесте приоритетов: пользователь {user.user_id}, категория {category_id}, балл {score}"
            )
            return True, MESSAGES["answer_saved"]

        except Exception as e:
            logger.error(f"Ошибка при обработке ответа теста приоритетов: {e}")
            return False, MESSAGES["answer_process_error"]

    async def process_priorities_step_answer(
        self, user: "User", category_num: str
    ) -> Tuple[bool, str]:
        try:
            task_state = self.get_task_state(user.user_id)
            if not task_state:
                return False, MESSAGES["task_not_found"]

            if task_state["current_task_type"] != TaskType.priorities.value:
                return False, MESSAGES["task_incorrect"]

            step = task_state["current_step"]
            if step >= PRIORITIES_LENGTH_SCORES_PER_QUESTION:
                return False, MESSAGES["answer_option_limit"]

            if TaskSection.priorities.value not in task_state["answers"]:
                task_state["answers"][TaskSection.priorities.value] = {}

            # Получаем данные категории для сохранения названия
            question = TaskEntity.priorities.value.get_question()
            if not question or "categories" not in question:
                return False, "Ошибка загрузки вопроса"

            category_num_int = int(category_num)
            if not (1 <= category_num_int <= len(question["categories"])):
                return False, f"Неверный номер категории: {category_num}"

            category_data = question["categories"][category_num_int - 1]
            category_title = category_data["title"]

            # Проверяем что эта категория еще не выбрана
            if category_title in task_state["answers"][TaskSection.priorities.value]:
                return False, f"Категория '{category_title}' уже выбрана"

            score = PRIORITIES_SCORES_PER_QUESTION[step]
            # Сохраняем по названию категории, а не по техническому ключу
            task_state["answers"][TaskSection.priorities.value][category_title] = score

            task_state["history"].append(
                {
                    "task": TaskType.priorities.value,
                    "category_num": category_num,
                    "score": score,
                }
            )

            task_state["current_step"] = step + 1

            # Отмечаем для отложенного сохранения
            self.mark_for_save(user.user_id)

            logger.info(
                f"Ответ в тесте приоритетов (новая логика): пользователь {user.user_id}, категория {category_num}, балл {score}"
            )
            return True, MESSAGES["answer_saved"]

        except Exception as e:
            logger.error(
                f"Ошибка при обработке ответа теста приоритетов (новая логика): {e}"
            )
            return False, MESSAGES["answer_process_error"]

    async def process_inq_answer(self, user: "User", option: str) -> Tuple[bool, str]:
        try:
            task_state = self.get_task_state(user.user_id)
            if not task_state:
                return False, MESSAGES["task_not_found"]

            if task_state["current_task_type"] != TaskType.inq.value:
                return False, MESSAGES["task_incorrect"]

            question_num = task_state["current_question"]
            step = task_state["current_step"]

            if option not in AnswerOptions.inq.value:
                return False, MESSAGES["answer_option_incorrect"]

            if step >= INQ_LENGTH_SCORES_PER_QUESTION:
                return False, MESSAGES["answer_option_limit"]

            question_key = f"question_{question_num + 1}"

            if TaskSection.inq.value not in task_state["answers"]:
                task_state["answers"][TaskSection.inq.value] = {}

            if question_key not in task_state["answers"][TaskSection.inq.value]:
                task_state["answers"][TaskSection.inq.value][question_key] = {}

            if option in task_state["answers"][TaskSection.inq.value][question_key]:
                return False, MESSAGES["answer_option_already_exist"]

            score = INQ_SCORES_PER_QUESTION[step]

            task_state["answers"][TaskSection.inq.value][question_key][option] = score

            task_state["history"].append(
                {
                    "task": TaskType.inq.value,
                    "question": question_num,
                    "step": step,
                    "option": option,
                    "score": score,
                }
            )

            task_state["current_step"] = step + 1
            
            # Отмечаем для отложенного сохранения
            self.mark_for_save(user.user_id)
            
            # Сохраняем только при завершении каждого INQ вопроса для надежности
            if step == INQ_LENGTH_SCORES_PER_QUESTION - 1:
                await self.save_pending_changes(user.user_id)

            logger.info(
                f"Ответ в INQ тесте: пользователь {user.user_id}, вопрос {question_num}, вариант {option}, балл {score}"
            )
            return True, MESSAGES["answer_saved"]

        except Exception as e:
            logger.error(f"Ошибка при обработке ответа INQ: {e}")
            return False, MESSAGES["answer_process_error"]

    async def process_epi_answer(self, user: "User", answer: str) -> Tuple[bool, str]:
        try:
            task_state = self.get_task_state(user.user_id)
            if not task_state:
                return False, MESSAGES["task_not_found"]

            if task_state["current_task_type"] != TaskType.epi.value:
                return False, MESSAGES["task_incorrect"]

            question_num = task_state["current_question"]

            if answer not in AnswerOptions.epi.value:
                return False, MESSAGES["answer_option_incorrect"]

            question_key = str(question_num + 1)

            if TaskSection.epi.value not in task_state["answers"]:
                task_state["answers"][TaskSection.epi.value] = {}

            task_state["answers"][TaskSection.epi.value][question_key] = answer
            task_state["current_question"] += 1

            # Отмечаем для отложенного сохранения
            self.mark_for_save(user.user_id)

            logger.info(
                f"Ответ в EPI тесте: пользователь {user.user_id}, вопрос {question_num + 1}, ответ {answer}"
            )
            return True, MESSAGES["answer_saved"]

        except Exception as e:
            logger.error(f"Ошибка при обработке ответа EPI: {e}")
            return False, MESSAGES["answer_process_error"]

    def is_priorities_task_completed(self, user_id: int) -> bool:
        state = self.get_task_state(user_id)
        if not state or TaskSection.priorities.value not in state["answers"]:
            return False
        return (
            len(state["answers"][TaskSection.priorities.value])
            == TaskAnswersLimit.priorities.value
        )

    def is_inq_question_completed(self, user_id: int, question_num: int) -> bool:
        state = self.get_task_state(user_id)
        if not state:
            return False

        task_section = state["answers"].get(TaskSection.inq.value, {})
        question_key = f"question_{question_num + 1}"
        question_answers = task_section.get(question_key, {})

        return len(question_answers) == INQ_LENGTH_SCORES_PER_QUESTION

    def get_inq_available_options(self, user_id: int, question_num: int) -> List[str]:
        state = self.get_task_state(user_id)
        if not state:
            return AnswerOptions.inq.value

        test_section = state["answers"].get("inq", {})
        question_key = f"question_{question_num + 1}"
        used_options = list(test_section.get(question_key, {}).keys())

        return [opt for opt in AnswerOptions.inq.value if opt not in used_options]

    def get_priorities_available_categories(self, user_id: int) -> List[str]:
        state = self.get_task_state(user_id)
        if not state:
            return ["1", "2", "3", "4"]

        test_section = state["answers"].get("priorities", {})
        used_category_titles = set(test_section.keys())

        # Получаем вопрос для сопоставления названий с номерами
        question = TaskEntity.priorities.value.get_question()
        if not question or "categories" not in question:
            return ["1", "2", "3", "4"]

        # Возвращаем номера категорий, названия которых еще не использованы
        available = []
        for i, category in enumerate(question["categories"], 1):
            if category["title"] not in used_category_titles:
                available.append(str(i))

        return available

    def get_priorities_remaining_categories_data(self, user_id: int) -> List[dict]:
        """Возвращает данные оставшихся категорий с новой нумерацией"""
        state = self.get_task_state(user_id)
        question = TaskEntity.priorities.value.get_question()
        if not state or not question:
            return []

        test_section = state["answers"].get("priorities", {})
        used_category_titles = set(test_section.keys())

        remaining = []
        for i, category in enumerate(question["categories"], 1):
            if category["title"] not in used_category_titles:
                remaining.append({"original_index": i, "category_data": category})

        return remaining

    def get_inq_remaining_options_data(self, user_id: int, question_num: int) -> dict:
        """Возвращает данные оставшихся вариантов INQ с новой нумерацией"""
        state = self.get_task_state(user_id)
        question = TaskEntity.inq.value.get_question(question_num)
        if not state or not question:
            return {"options": [], "base_text": ""}

        test_section = state["answers"].get("inq", {})
        question_key = f"question_{question_num + 1}"
        used_options = set(test_section.get(question_key, {}).keys())

        full_text = question["text"]
        lines = full_text.split("\n")

        base_text_lines = []
        options_data = []
        in_options = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣")):
                in_options = True
                option_num = stripped[0]
                option_text = stripped.split("️⃣", 1)[1].strip()
                if option_num not in used_options:
                    options_data.append(
                        {"original_option": option_num, "text": option_text}
                    )
            elif not in_options:
                base_text_lines.append(line)

        base_text = "\n".join(base_text_lines).strip()

        return {"base_text": base_text, "options": options_data}

    async def move_to_next_task(self, user_id: int):
        state = self.get_task_state(user_id)
        if state:
            state["current_task_type"] += 1
            state["current_question"] = 0
            state["current_step"] = 0

            # Сохраняем все изменения одним запросом
            await update_user(
                user_id=user_id,
                current_task_type=state["current_task_type"],
                current_question=0,
                current_step=0,
                answers_json=state["answers"],
            )
            
            # Очищаем pending saves так как уже сохранили
            if user_id in self.pending_saves:
                del self.pending_saves[user_id]

    async def move_to_next_question(self, user_id: int):
        state = self.get_task_state(user_id)
        if state:
            state["current_question"] += 1
            state["current_step"] = 0

            # Сохраняем все изменения одним запросом
            await update_user(
                user_id=user_id,
                current_question=state["current_question"],
                current_step=0,
                answers_json=state["answers"],
            )
            
            # Очищаем pending saves так как уже сохранили
            if user_id in self.pending_saves:
                del self.pending_saves[user_id]

    async def complete_all_tasks(self, user: "User") -> Dict[str, Any]:
        try:
            task_state = self.get_task_state(user.user_id)
            if not task_state:
                return {}

            all_scores = {}

            priorities_scores = TaskEntity.priorities.value.calculate_scores(
                task_state["answers"]
            )
            inq_scores = TaskEntity.inq.value.calculate_scores(task_state["answers"])
            epi_scores = TaskEntity.epi.value.calculate_scores(task_state["answers"])

            # Устанавливаем время отправки персональной ссылки через случайное время для пользователей не из Senler
            admin_link_send_time = None
            if not user.from_senler:
                from datetime import datetime, timedelta
                from config.settings import DEBUG
                import random

                # В режиме отладки - отправка через 5 секунд, иначе через случайное время от 15 до 24 часов
                if DEBUG:
                    admin_link_send_time = datetime.now() + timedelta(seconds=5)
                else:
                    # Случайное время от 15 до 24 часов
                    random_hours = random.randint(15, 24)
                    admin_link_send_time = datetime.now() + timedelta(hours=random_hours)

            # Сохраняем все финальные данные одним запросом
            await update_user(
                user_id=user.user_id,
                test_completed=True,
                answers_json=task_state["answers"],
                priorities_json=priorities_scores,
                inq_scores_json=inq_scores,
                epi_scores_json=epi_scores,
                temperament=epi_scores.get("temperament"),
                admin_link_send_time=admin_link_send_time,
            )

            if user.user_id in self.active_tasks:
                del self.active_tasks[user.user_id]
            if user.user_id in self.cached_users:
                del self.cached_users[user.user_id]
            if user.user_id in self.pending_saves:
                del self.pending_saves[user.user_id]

            all_scores.update(inq_scores)
            all_scores.update(epi_scores)

            logger.info(f"Все тесты завершены для пользователя {user.user_id}")
            return all_scores

        except Exception as e:
            logger.error(f"Ошибка при завершении тестов: {e}")
            return {}

    async def go_back_question(self, user: "User") -> Tuple[bool, str, Optional[Dict]]:
        try:
            task_state = self.get_task_state(user.user_id)
            if not task_state:
                return False, MESSAGES["task_not_found"], None

            if not task_state["history"]:
                return False, MESSAGES["go_back_unavailable"], None

            last_action = task_state["history"].pop()

            if last_action["task"] == TaskType.priorities.value:
                # Обработка отката для теста приоритетов
                if "category_num" in last_action:
                    category_num = last_action["category_num"]

                    # Получаем название категории по номеру
                    question = TaskEntity.priorities.value.get_question()
                    if question and "categories" in question:
                        try:
                            category_num_int = int(category_num)
                            if 1 <= category_num_int <= len(question["categories"]):
                                category_title = question["categories"][
                                    category_num_int - 1
                                ]["title"]

                                # Удаляем ответ по названию категории
                                if (
                                    TaskSection.priorities.value
                                    in task_state["answers"]
                                    and category_title
                                    in task_state["answers"][
                                        TaskSection.priorities.value
                                    ]
                                ):
                                    del task_state["answers"][
                                        TaskSection.priorities.value
                                    ][category_title]
                        except (ValueError, IndexError):
                            pass

                    current_answers = task_state["answers"].get(
                        TaskSection.priorities.value, {}
                    )
                    task_state["current_step"] = len(current_answers)
                else:
                    # Старая логика отката для совместимости
                    category_id = last_action["category_id"]

                    if (
                        TaskSection.priorities.value in task_state["answers"]
                        and category_id
                        in task_state["answers"][TaskSection.priorities.value]
                    ):
                        del task_state["answers"][TaskSection.priorities.value][
                            category_id
                        ]

                    current_answers = task_state["answers"].get(
                        TaskSection.priorities.value, {}
                    )
                    task_state["current_step"] = len(current_answers)

                # Отмечаем для отложенного сохранения
                self.mark_for_save(user.user_id)

            elif last_action["task"] == TaskType.inq.value:
                question_num = last_action["question"]
                option = last_action["option"]

                question_key = f"question_{question_num + 1}"

                if (
                    TaskSection.inq.value in task_state["answers"]
                    and question_key in task_state["answers"][TaskSection.inq.value]
                    and option
                    in task_state["answers"][TaskSection.inq.value][question_key]
                ):

                    del task_state["answers"][TaskSection.inq.value][question_key][
                        option
                    ]

                    if not task_state["answers"][TaskSection.inq.value][question_key]:
                        del task_state["answers"][TaskSection.inq.value][question_key]

                new_step = len(
                    task_state["answers"][TaskSection.inq.value].get(question_key, {})
                )
                task_state["current_step"] = new_step
                task_state["current_question"] = question_num

                # Отмечаем для отложенного сохранения
                self.mark_for_save(user.user_id)

            logger.info(f"Откат выполнен для пользователя {user.user_id}")
            return True, MESSAGES["go_back_completed"], task_state

        except Exception as e:
            logger.error(f"Ошибка при откате: {e}")
            return False, MESSAGES["go_back_error"], None
