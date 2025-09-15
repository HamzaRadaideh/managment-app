# app/api/repositories/auths_repositories.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.database import get_async_session
from app.schemas.models.users_models import User

class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_username_or_email(self, username: str, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where((User.username == username) | (User.email == email))
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: dict) -> User:
        new_user = User(**user_data)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def get_user_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

# Dependency for easy injection
def get_auth_repository(
    db: AsyncSession = Depends(get_async_session)
) -> AuthRepository:
    return AuthRepository(db)

