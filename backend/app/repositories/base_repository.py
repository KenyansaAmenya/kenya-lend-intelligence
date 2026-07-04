# Abstract base class defining the contract for all repositories.
# Provides common CRUD operations that can be overridden by specific repositories.

from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    async def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: UUID) -> bool:
        obj = await self.get_by_id(id)
        if obj:
            await self.db.delete(obj)
            await self.db.flush()
            return True
        return False
    
    async def count(self) -> int:
        from sqlalchemy import func
        result = await self.db.execute(select(func.count()).select_from(self.model))
        return result.scalar() or 0

# TODO: Add soft delete support (deleted_at column)
# TODO: Add query result caching with Redis
# TODO: Add audit logging for all write operations
# TODO: Add optimistic locking for concurrent updates        

