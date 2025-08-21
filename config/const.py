from enum import Enum

from aiogram import Dispatcher
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

from src.core.task_models import PrioritiesTask, InqTask, EpiTask

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

MESSAGES = {}

PRIORITIES_SCORES_PER_QUESTION = [4, 3, 2, 1]
PRIORITIES_LENGTH_SCORES_PER_QUESTION = len(PRIORITIES_SCORES_PER_QUESTION)

INQ_SCORES_PER_QUESTION = [5, 4, 3, 2, 1]
INQ_LENGTH_SCORES_PER_QUESTION = len(INQ_SCORES_PER_QUESTION)

TOTAL_QUESTIONS = 18

AGE_MIN = 12
AGE_MAX = 99


class PersonalDataStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()
    waiting_for_age = State()


class AdminStates(StatesGroup):
    waiting_for_senler_link = State()


class TaskEntity(Enum):
    priorities = PrioritiesTask()
    inq = InqTask()
    epi = EpiTask()


class TaskType(Enum):
    priorities = 1
    inq = 2
    epi = 3


class AnswerOptions(Enum):
    priorities = [1, 2, 3, 4]
    inq = ["1", "2", "3", "4", "5"]
    epi = ["Да", "Нет"]


class TaskSection(Enum):
    priorities = "priorities"
    inq = "inq"
    epi = "epi"


class TaskAnswersLimit(Enum):
    priorities = 4
    inq = 18
    epi = 57
