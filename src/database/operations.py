from sqlalchemy import select
from .models import AsyncSessionLocal, User, engine, Base


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_user_by_id(user_id: int) -> User:
    """Получить пользователя по ID"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()


async def get_or_create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> User:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(user_id=user_id, username=username, first_name=first_name, last_name=last_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user


async def update_user(user_id: int, **kwargs):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            await session.commit()
            await session.refresh(user)
            return user
        return None
