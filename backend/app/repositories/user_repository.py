# Data access layer for User entity.
# Handles user-specific queries and operations.

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_by_role(self, role: str, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.role == role).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db.execute(
            select(User).where(User.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    # TODO: Add user session management methods
    # TODO: Add user password history tracking
    # TODO: Add user preference storage methods