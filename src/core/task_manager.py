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
)
from src.database.operations import update_user

if TYPE_CHECKING:
    from src.database.models import User

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self):
        self.active_tasks = {}
        self.tasks = {
            TaskType.priorities: TaskEntity.priorities.value,
            TaskType.inq: TaskEntity.inq.value,
            TaskType.epi: TaskEntity.epi.value,
        }

    async def start_tests(self, user: "User") -> bool:
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
                "current_task_type": TaskType.priorities,
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
            logger.info(f"Состояние тестов очищено для пользователя {user_id}")

    def get_current_task_type(self, user_id: int) -> int:
        state = self.get_task_state(user_id)
        return state["current_task_type"] if state else TaskType.priorities

    def is_all_tasks_completed(self, user_id: int) -> bool:
        state = self.get_task_state(user_id)
        if not state:
            return False
        return state["current_task_type"] > TaskType.epi

    async def process_priorities_answer(self, user: "User", category_id: str, score: int) -> Tuple[bool, str]:
        try:
            task_state = self.get_task_state(user.user_id)
            if not task_state:
                return False, MESSAGES["task_not_found"]

            if task_state["current_task_type"] != TaskType.priorities:
                return False, MESSAGES["task_incorrect"]

            if TaskSection.priorities.value not in task_state["answers"]:
                task_state["answers"][TaskSection.priorities.value] = {}

            used_scores = set(task_state["answers"][TaskSection.priorities.value].values())
            if score in used_scores:
                return False, f"Балл {score} уже использован"

            task_state["answers"][TaskSection.priorities.value][category_id] = score
            task_state["current_step"] += 1

            await update_user(
                user_id=user.user_id, current_step=task_state["current_step"], answers_json=task_state["answers"]
            )

            logger.info(
                f"Ответ в тесте приоритетов: пользователь {user.user_id}, категория {category_id}, балл {score}"
            )
            return True, MESSAGES["answer_saved"]

        except Exception as e:
            logger.error(f"Ошибка при обработке ответа теста приоритетов: {e}")
            return False, MESSAGES["answer_process_error"]

    async def process_inq_answer(self, user: "User", option: str) -> Tuple[bool, str]:
        try:
            task_state = self.get_task_state(user.user_id)
            if not task_state:
                return False, MESSAGES["task_not_found"]

            if task_state["current_task_type"] != TaskType.inq:
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
                {"task": TaskType.inq, "question": question_num, "step": step, "option": option, "score": score}
            )

            task_state["current_step"] = step + 1

            await update_user(
                user_id=user.user_id,
                current_question=question_num,
                current_step=step + 1,
                answers_json=task_state["answers"],
            )

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

            if task_state["current_task_type"] != TaskType.epi:
                return False, MESSAGES["task_incorrect"]

            question_num = task_state["current_question"]

            if answer not in AnswerOptions.epi.value:
                return False, MESSAGES["answer_option_incorrect"]

            question_key = str(question_num + 1)

            if TaskSection.epi.value not in task_state["answers"]:
                task_state["answers"][TaskSection.epi.value] = {}

            task_state["answers"][TaskSection.epi.value][question_key] = answer
            task_state["current_question"] += 1

            await update_user(
                user_id=user.user_id,
                current_question=task_state["current_question"],
                answers_json=task_state["answers"],
            )

            logger.info(f"Ответ в EPI тесте: пользователь {user.user_id}, вопрос {question_num + 1}, ответ {answer}")
            return True, MESSAGES["answer_saved"]

        except Exception as e:
            logger.error(f"Ошибка при обработке ответа EPI: {e}")
            return False, MESSAGES["answer_process_error"]

    def is_priorities_task_completed(self, user_id: int) -> bool:
        state = self.get_task_state(user_id)
        if not state or TaskSection.priorities.value not in state["answers"]:
            return False
        return len(state["answers"][TaskSection.priorities.value]) == TaskAnswersLimit.priorities

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

    async def move_to_next_task(self, user_id: int):
        state = self.get_task_state(user_id)
        if state:
            state["current_task_type"] += 1
            state["current_question"] = 0
            state["current_step"] = 0

            await update_user(
                user_id=user_id, current_task_type=state["current_task_type"], current_question=0, current_step=0
            )

    async def move_to_next_question(self, user_id: int):
        state = self.get_task_state(user_id)
        if state:
            state["current_question"] += 1
            state["current_step"] = 0

            await update_user(user_id=user_id, current_question=state["current_question"], current_step=0)

    async def complete_all_tasks(self, user: "User") -> Dict[str, Any]:
        try:
            test_state = self.get_task_state(user.user_id)
            if not test_state:
                return {}

            all_scores = {}

            priorities_scores = TaskEntity.priorities.value.calculate_scores(test_state["answers"])
            inq_scores = TaskEntity.inq.value.calculate_scores(test_state["answers"])
            epi_scores = TaskEntity.epi.value.calculate_scores(test_state["answers"])

            await update_user(
                user_id=user.user_id,
                test_completed=True,
                priorities_json=priorities_scores,
                inq_scores_json=inq_scores,
                epi_scores_json=epi_scores,
                temperament=epi_scores.get("temperament"),
            )

            if user.user_id in self.active_tasks:
                del self.active_tasks[user.user_id]

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

            if last_action["task"] == TaskType.inq.value:
                question_num = last_action["question"]
                option = last_action["option"]

                question_key = f"question_{question_num + 1}"

                if (
                    TaskSection.inq.value in task_state["answers"]
                    and question_key in task_state["answers"][TaskSection.inq.value]
                    and option in task_state["answers"][TaskSection.inq.value][question_key]
                ):

                    del task_state["answers"][TaskSection.inq.value][question_key][option]

                    if not task_state["answers"][TaskSection.inq.value][question_key]:
                        del task_state["answers"][TaskSection.inq.value][question_key]

                new_step = len(task_state["answers"][TaskSection.inq.value].get(question_key, {}))
                task_state["current_step"] = new_step
                task_state["current_question"] = question_num

                await update_user(
                    user_id=user.user_id,
                    current_question=question_num,
                    current_step=new_step,
                    answers_json=task_state["answers"],
                )

            logger.info(f"Откат выполнен для пользователя {user.user_id}")
            return True, MESSAGES["go_back_completed"], task_state

        except Exception as e:
            logger.error(f"Ошибка при откате: {e}")
            return False, MESSAGES["go_back_error"], None
