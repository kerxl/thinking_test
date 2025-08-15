import json
import aiofiles
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod


class BaseTest(ABC):
    def __init__(self):
        self.loaded = False

    @abstractmethod
    async def load_questions(self):
        pass

    @abstractmethod
    def get_total_questions(self) -> int:
        pass

    @abstractmethod
    def calculate_scores(self, answers: Dict) -> Dict:
        pass


class PrioritiesTask(BaseTest):
    def __init__(self):
        super().__init__()
        self.question_data = None

    async def load_questions(self):
        try:
            async with aiofiles.open("questions/first_task.json", "r", encoding="utf-8") as f:
                content = await f.read()
                self.question_data = json.loads(content)
                self.loaded = True
                print("Загружен тест приоритетов")
        except Exception as e:
            print(f"Ошибка загрузки первого теста: {e}")
            self.question_data = self._get_default_priorities_question()
            self.loaded = True

    def _get_default_priorities_question(self):
        return {
            "question": {
                "text": "Расставь приоритеты от 5 (максимально важно для тебя сейчас) до 2 (минимально важно). Оцени каждый блок, даже если все кажутся важными. Каждое число можно использовать только один раз.\n\n📝 1 / 1",
                "categories": [
                    {
                        "id": "personal_wellbeing",
                        "title": "Личное благополучие",
                        "description": "• Внутреннее спокойствие и уравновешенность\n• Чувствовать себя счастливым каждый день\n• Быть здоровым и полным энергии",
                    },
                    {
                        "id": "material_career",
                        "title": "Материальное и карьерное развитие",
                        "description": "• Финансовая обеспеченность\n• Успешная карьера / своё дело\n• Жить в комфорте и безопасности",
                    },
                    {
                        "id": "relationships",
                        "title": "Отношения и окружение",
                        "description": "• Крепкая семья / гармоничные отношения\n• Окружение людей, которые ценят\n• Доверять и быть понятым",
                    },
                    {
                        "id": "self_realization",
                        "title": "Самореализация и влияние",
                        "description": "• Делать то, что люблю, и получать доход\n• Развиваться и учиться новому\n• Оставить значимый след в мире",
                    },
                ],
            }
        }

    def get_total_questions(self) -> int:
        return 1

    def get_question(self):
        if not self.loaded or not self.question_data:
            return None
        return self.question_data["question"]

    def calculate_scores(self, answers: Dict) -> Dict:
        priorities = answers.get("priorities", {})
        return priorities


class InqTask(BaseTest):
    def __init__(self):
        super().__init__()
        self.questions = []

    async def load_questions(self):
        try:
            async with aiofiles.open("questions/second_task.json", "r", encoding="utf-8") as f:
                content = await f.read()
                self.questions = json.loads(content)
                self.loaded = True
                print(f"Загружено {len(self.questions)} INQ вопросов")
        except Exception as e:
            print(f"Ошибка загрузки второго теста: {e}")
            self.questions = self._get_default_inq_questions()
            self.loaded = True

    def _get_default_inq_questions(self):
        return [
            {
                "text": "Когда между людьми имеет место конфликт на почве идей, я отдаю предпочтение той стороне, которая:\n1️⃣ Устанавливает, определяет конфликт и пытается выразить его открыто.\n2️⃣ Лучше всех выражает затрагиваемые ценности и идеалы.\n3️⃣ Лучше всех отражает мои личные взгляды и опыт.\n4️⃣ Подходит к ситуации наиболее логично и последовательно.\n5️⃣ Излагает аргументы наиболее кратко и убедительно.\n\n📝 1 / 3",
                "mapping": {
                    "1": "Синтетический",
                    "2": "Идеалистический",
                    "3": "Прагматический",
                    "4": "Аналитический",
                    "5": "Реалистический",
                },
            },
            {
                "text": "Когда я начинаю работать над проектом в составе группы, самое важное для меня:\n1️⃣ Понять цели и значение этого проекта.\n2️⃣ Раскрыть цели и ценности участников рабочей группы.\n3️⃣ Определить, как мы собираемся разрабатывать данный проект.\n4️⃣ Понять, какую выгоду этот проект может принести для нашей группы.\n5️⃣ Чтобы работа над проектом была организована и сдвинулась с места.\n\n📝 2 / 3",
                "mapping": {
                    "1": "Идеалистический",
                    "2": "Синтетический",
                    "3": "Аналитический",
                    "4": "Прагматический",
                    "5": "Реалистический",
                },
            },
            {
                "text": "Вообще говоря, я усваиваю новые идеи лучше всего, когда могу:\n1️⃣ Связать их с текущими или будущими занятиями.\n2️⃣ Применить их к конкретным ситуациям.\n3️⃣ Сосредоточиться на них и тщательно их проанализировать.\n4️⃣ Понять, насколько они сходны с привычными идеями.\n5️⃣ Противопоставить их другим идеям.\n\n📝 3 / 3",
                "mapping": {
                    "1": "Прагматический",
                    "2": "Реалистический",
                    "3": "Аналитический",
                    "4": "Синтетический",
                    "5": "Идеалистический",
                },
            },
        ]

    def get_total_questions(self) -> int:
        return len(self.questions)

    def get_question(self, question_num: int):
        if not self.loaded or question_num >= len(self.questions):
            return None
        return self.questions[question_num]

    def calculate_scores(self, answers: Dict) -> Dict:
        scores = {
            "Синтетический": 0,
            "Идеалистический": 0,
            "Прагматический": 0,
            "Аналитический": 0,
            "Реалистический": 0,
        }

        inq_answers = answers.get("inq", {})

        for question_num in range(len(self.questions)):
            question_data = self.questions[question_num]
            question_key = f"question_{question_num + 1}"

            if question_key in inq_answers:
                question_answers = inq_answers[question_key]
                mapping = question_data["mapping"]

                for option, score in question_answers.items():
                    style = mapping.get(option)
                    if style and style in scores:
                        scores[style] += score

        return scores


class EpiTask(BaseTest):
    def __init__(self):
        super().__init__()
        self.questions = []

    async def load_questions(self):
        try:
            async with aiofiles.open("questions/third_task.json", "r", encoding="utf-8") as f:
                content = await f.read()
                self.questions = json.loads(content)
                self.loaded = True
                print(f"Загружено {len(self.questions)} EPI вопросов")
        except Exception as e:
            print(f"Ошибка загрузки третьего теста: {e}")
            self.questions = self._get_default_epi_questions()
            self.loaded = True

    def _get_default_epi_questions(self):
        return [
            {
                "number": 1,
                "text": "Часто ли вы испытываете тягу к новым впечатлениям, к тому, чтобы встряхнуться, испытать возбуждение?",
                "scale": "E",
                "answer_for_point": "да",
            },
            {
                "number": 2,
                "text": "Часто ли нуждаетесь в друзьях, которые вас понимают, могут ободрить, утешить?",
                "scale": "N",
                "answer_for_point": "да",
            },
            {
                "number": 3,
                "text": "Вы верите в удачу, считая себя везучим человеком?",
                "scale": "E",
                "answer_for_point": "да",
            },
            {
                "number": 4,
                "text": "Находите ли вы, что вам трудно ответить «нет»?",
                "scale": "L",
                "answer_for_point": "да",
            },
            {
                "number": 5,
                "text": "Задумываетесь ли вы перед тем, как что-нибудь предпринять?",
                "scale": "L",
                "answer_for_point": "да",
            },
        ]

    def get_total_questions(self) -> int:
        return len(self.questions)

    def get_question(self, question_num: int):
        if not self.loaded or question_num >= len(self.questions):
            return None
        return self.questions[question_num]

    def calculate_scores(self, answers: Dict) -> Dict:
        scores = {"E": 0, "N": 0, "L": 0}

        epi_answers = answers.get("epi", {})

        for question in self.questions:
            question_num = question["number"]
            user_answer = epi_answers.get(str(question_num))

            if user_answer and str(user_answer).lower() == question["answer_for_point"].lower():
                scale = question["scale"]
                if scale in scores:
                    scores[scale] += 1

        temperament = self._determine_temperament(scores["E"], scores["N"])

        return {"E": scores["E"], "N": scores["N"], "L": scores["L"], "temperament": temperament}

    def _determine_temperament(self, e_score: int, n_score: int) -> str:
        if e_score >= 2 and n_score >= 2:
            return "Холерик"
        elif e_score >= 2 and n_score < 2:
            return "Сангвиник"
        elif e_score < 2 and n_score >= 2:
            return "Меланхолик"
        else:
            return "Флегматик"
