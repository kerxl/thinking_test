from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, BigInteger
from sqlalchemy.sql import func

from config.settings import DATABASE_URL

Base = declarative_base()

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)

    test_start = Column(DateTime, nullable=True)
    test_end = Column(DateTime, nullable=True)

    answers_json = Column(JSON, nullable=True)

    inq_scores_json = Column(JSON, nullable=True)
    epi_scores_json = Column(JSON, nullable=True)
    priorities_json = Column(JSON, nullable=True)
    temperament = Column(String, nullable=True)

    current_task_type = Column(Integer, default=1)
    current_question = Column(Integer, default=0)
    current_step = Column(Integer, default=0)
    test_completed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(user_id={self.user_id}, username={self.username})>"

    def get_answers_dict(self):
        return self.answers_json if self.answers_json else {}

    def get_inq_scores_dict(self):
        return self.inq_scores_json if self.inq_scores_json else {}

    def get_epi_scores_dict(self):
        return self.epi_scores_json if self.epi_scores_json else {}

    def get_priorities_dict(self):
        return self.priorities_json if self.priorities_json else {}

    def get_test_section(self, test_name: str):
        answers = self.get_answers_dict()
        return answers.get(test_name, {})

    def update_test_answer(self, test_name: str, question_key: str, data):
        if not self.answers_json:
            self.answers_json = {}

        if test_name not in self.answers_json:
            self.answers_json[test_name] = {}

        self.answers_json[test_name][question_key] = data
