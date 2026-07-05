# Data access layer for Customer entity.
# Handles customer-specific queries including search and filtering.

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.base_repository import BaseRepository

class CustomerRepository(BaseRepository[Customer]):

    def __init__(self, db: AsyncSession):
        super().__init__(db, Customer)
    
    async def get_by_phone(self, phone: str) -> Optional[Customer]:
        result = await self.db.execute(
            select(Customer).where(Customer.phone == phone)
        )
        return result.scalar_one_or_none()
    
    async def get_by_national_id(self, national_id: str) -> Optional[Customer]:
        result = await self.db.execute(
            select(Customer).where(Customer.national_id == national_id)
        )
        return result.scalar_one_or_none()
    
    async def search_customers(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        employment_status: Optional[str] = None,
        min_income: Optional[float] = None,
        max_income: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Customer]:
        stmt = select(Customer)
        
        if query:
            search_filter = or_(
                Customer.full_name.ilike(f"%{query}%"),
                Customer.phone.ilike(f"%{query}%"),
                Customer.national_id.ilike(f"%{query}%"),
            )
            stmt = stmt.where(search_filter)
        
        if location:
            stmt = stmt.where(Customer.location.ilike(f"%{location}%"))
        
        if employment_status:
            stmt = stmt.where(Customer.employment_status == employment_status)
        
        if min_income is not None:
            stmt = stmt.where(Customer.income >= min_income)
        
        if max_income is not None:
            stmt = stmt.where(Customer.income <= max_income)
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_customers_by_location(self, location: str) -> List[Customer]:
        result = await self.db.execute(
            select(Customer).where(Customer.location.ilike(f"%{location}%"))
        )
        return list(result.scalars().all())
    
    async def get_customer_count_by_location(self) -> List[dict]:
        result = await self.db.execute(
            select(Customer.location, func.count(Customer.id))
            .group_by(Customer.location)
        )
        return [{"location": loc, "count": count} for loc, count in result.all() if loc]
    
    # Future enhancements:
    # TODO: Add full-text search integration (PostgreSQL tsvector)
    # TODO: Add geospatial queries for location-based analytics
    # TODO: Add customer lifetime value calculations