# Data access layer for Loan management.

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import Loan, LoanStatus
from app.repositories.base_repository import BaseRepository


class LoanRepository(BaseRepository[Loan]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Loan)
    
    async def get_by_customer(self, customer_id: UUID, skip: int = 0, limit: int = 100) -> List[Loan]:
        result = await self.db.execute(
            select(Loan)
            .where(Loan.customer_id == customer_id)
            .order_by(Loan.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_active_loans(self, skip: int = 0, limit: int = 100) -> List[Loan]:
        result = await self.db.execute(
            select(Loan)
            .where(Loan.status.in_([LoanStatus.ACTIVE.value, LoanStatus.DISBURSED.value, LoanStatus.APPROVED.value]))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_overdue_loans(self, days: int = 30) -> List[Loan]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(Loan)
            .where(
                and_(
                    Loan.days_past_due >= days,
                    Loan.status.in_([LoanStatus.ACTIVE.value, LoanStatus.DISBURSED.value]),
                )
            )
        )
        return list(result.scalars().all())
    
    async def get_loan_summary_by_customer(self, customer_id: UUID) -> dict:
        result = await self.db.execute(
            select(
                func.count(Loan.id).label("total_loans"),
                func.sum(Loan.amount).label("total_borrowed"),
                func.sum(Loan.outstanding_balance).label("total_outstanding"),
                func.avg(Loan.interest_rate).label("avg_interest_rate"),
            ).where(Loan.customer_id == customer_id)
        )
        row = result.one_or_none()
        return {
            "total_loans": row.total_loans or 0,
            "total_borrowed": float(row.total_borrowed or 0),
            "total_outstanding": float(row.total_outstanding or 0),
            "avg_interest_rate": float(row.avg_interest_rate or 0),
        } if row else {
            "total_loans": 0,
            "total_borrowed": 0.0,
            "total_outstanding": 0.0,
            "avg_interest_rate": 0.0,
        }
    
    async def get_portfolio_metrics(self) -> dict:
        result = await self.db.execute(
            select(
                func.count(Loan.id).label("total_loans"),
                func.sum(Loan.amount).label("total_disbursed"),
                func.sum(Loan.outstanding_balance).label("total_outstanding"),
                func.avg(Loan.days_past_due).label("avg_dpd"),
                func.sum(
                    func.case((Loan.status == LoanStatus.DEFAULTED.value, 1), else_=0)
                ).label("defaulted_count"),
            )
        )
        row = result.one_or_none()
        return {
            "total_loans": row.total_loans or 0,
            "total_disbursed": float(row.total_disbursed or 0),
            "total_outstanding": float(row.total_outstanding or 0),
            "avg_dpd": float(row.avg_dpd or 0),
            "defaulted_count": row.defaulted_count or 0,
            "default_rate": (row.defaulted_count / row.total_loans * 100) if row.total_loans else 0,
        } if row else {
            "total_loans": 0,
            "total_disbursed": 0.0,
            "total_outstanding": 0.0,
            "avg_dpd": 0.0,
            "defaulted_count": 0,
            "default_rate": 0.0,
        }
    
    # Future enhancements:
    # TODO: Add loan performance trend queries
    # TODO: Add collection priority queue queries
    # TODO: Add loan restructuring history queries