# Data access layer for CustomerActivity entity.

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import CustomerActivity
from app.repositories.base_repository import BaseRepository

class ActivityRepository(BaseRepository[CustomerActivity]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, CustomerActivity)
    
    async def get_by_customer(
        self,
        customer_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[CustomerActivity]:
        stmt = select(CustomerActivity).where(CustomerActivity.customer_id == customer_id)
        
        if start_date:
            stmt = stmt.where(CustomerActivity.login_date >= start_date)
        if end_date:
            stmt = stmt.where(CustomerActivity.login_date <= end_date)
        
        stmt = stmt.order_by(CustomerActivity.login_date.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_latest_activity(self, customer_id: UUID) -> Optional[CustomerActivity]:
        result = await self.db.execute(
            select(CustomerActivity)
            .where(CustomerActivity.customer_id == customer_id)
            .order_by(CustomerActivity.login_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_engagement_summary(self, customer_id: UUID, days: int = 30) -> dict:
        start_date = date.today() - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                func.count(CustomerActivity.id).label("total_sessions"),
                func.sum(CustomerActivity.session_duration).label("total_duration"),
                func.avg(CustomerActivity.engagement_score).label("avg_engagement"),
                func.sum(CustomerActivity.app_opens).label("total_app_opens"),
                func.max(CustomerActivity.login_date).label("last_activity_date"),
            )
            .where(
                and_(
                    CustomerActivity.customer_id == customer_id,
                    CustomerActivity.login_date >= start_date,
                )
            )
        )
        row = result.one_or_none()
        return {
            "total_sessions": row.total_sessions or 0,
            "total_duration": row.total_duration or 0,
            "avg_engagement": float(row.avg_engagement or 0),
            "total_app_opens": row.total_app_opens or 0,
            "last_activity_date": row.last_activity_date,
        } if row else {
            "total_sessions": 0,
            "total_duration": 0,
            "avg_engagement": 0.0,
            "total_app_opens": 0,
            "last_activity_date": None,
        }
    
    async def get_inactive_customers(self, days: int = 90) -> List[UUID]:
        cutoff_date = date.today() - timedelta(days=days)
        
        # Subquery: customers with recent activity
        recent_activity = (
            select(CustomerActivity.customer_id)
            .where(CustomerActivity.login_date >= cutoff_date)
            .distinct()
        )
        
        # Main query: customers without recent activity
        result = await self.db.execute(
            select(CustomerActivity.customer_id)
            .where(CustomerActivity.customer_id.not_in(recent_activity))
            .distinct()
        )
        return list(result.scalars().all())
    
    # TODO: Add real-time activity streaming integration
    # TODO: Add cohort retention analysis queries
    # TODO: Add engagement prediction features