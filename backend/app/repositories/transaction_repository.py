# Data access layer for MpesaTransaction and BankTransaction entities.
# Handles transaction data queries for income verification and spending analysis.

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import BankTransaction, MpesaTransaction
from app.repositories.base_repository import BaseRepository

class TransactionRepository:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.mpesa_repo = BaseRepository(db, MpesaTransaction)
        self.bank_repo = BaseRepository(db, BankTransaction)
    
    # M-Pesa Operations
    async def get_mpesa_by_customer(
        self,
        customer_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[MpesaTransaction]:
        stmt = select(MpesaTransaction).where(MpesaTransaction.customer_id == customer_id)
        
        if start_date:
            stmt = stmt.where(MpesaTransaction.transaction_date >= start_date)
        if end_date:
            stmt = stmt.where(MpesaTransaction.transaction_date <= end_date)
        
        stmt = stmt.order_by(MpesaTransaction.transaction_date.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_mpesa_summary(self, customer_id: UUID, days: int = 90) -> dict:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                func.count(MpesaTransaction.id).label("transaction_count"),
                func.sum(MpesaTransaction.amount).label("total_amount"),
                func.avg(MpesaTransaction.amount).label("avg_amount"),
                func.max(MpesaTransaction.transaction_date).label("last_transaction"),
            )
            .where(
                and_(
                    MpesaTransaction.customer_id == customer_id,
                    MpesaTransaction.transaction_date >= start_date,
                )
            )
        )
        row = result.one_or_none()
        return {
            "transaction_count": row.transaction_count or 0,
            "total_amount": float(row.total_amount or 0),
            "avg_amount": float(row.avg_amount or 0),
            "last_transaction": row.last_transaction,
        } if row else {
            "transaction_count": 0,
            "total_amount": 0.0,
            "avg_amount": 0.0,
            "last_transaction": None,
        }
    
    # Bank Operations
    async def get_bank_by_customer(
        self,
        customer_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[BankTransaction]:
        stmt = select(BankTransaction).where(BankTransaction.customer_id == customer_id)
        
        if start_date:
            stmt = stmt.where(BankTransaction.transaction_date >= start_date)
        if end_date:
            stmt = stmt.where(BankTransaction.transaction_date <= end_date)
        
        stmt = stmt.order_by(BankTransaction.transaction_date.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_bank_summary(self, customer_id: UUID, days: int = 90) -> dict:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                func.count(BankTransaction.id).label("transaction_count"),
                func.sum(BankTransaction.amount).label("total_amount"),
                func.avg(BankTransaction.amount).label("avg_amount"),
                func.max(BankTransaction.transaction_date).label("last_transaction"),
            )
            .where(
                and_(
                    BankTransaction.customer_id == customer_id,
                    BankTransaction.transaction_date >= start_date,
                )
            )
        )
        row = result.one_or_none()
        return {
            "transaction_count": row.transaction_count or 0,
            "total_amount": float(row.total_amount or 0),
            "avg_amount": float(row.avg_amount or 0),
            "last_transaction": row.last_transaction,
        } if row else {
            "transaction_count": 0,
            "total_amount": 0.0,
            "avg_amount": 0.0,
            "last_transaction": None,
        }

    # Combined Analysis
    async def get_combined_income_estimate(self, customer_id: UUID, days: int = 90) -> dict:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # M-Pesa credits
        mpesa_result = await self.db.execute(
            select(
                func.sum(MpesaTransaction.amount).label("total_credits"),
                func.count(MpesaTransaction.id).label("credit_count"),
            )
            .where(
                and_(
                    MpesaTransaction.customer_id == customer_id,
                    MpesaTransaction.transaction_date >= start_date,
                    MpesaTransaction.amount > 0,
                )
            )
        )
        mpesa_row = mpesa_result.one_or_none()
        
        # Bank credits
        bank_result = await self.db.execute(
            select(
                func.sum(BankTransaction.amount).label("total_credits"),
                func.count(BankTransaction.id).label("credit_count"),
            )
            .where(
                and_(
                    BankTransaction.customer_id == customer_id,
                    BankTransaction.transaction_date >= start_date,
                    BankTransaction.amount > 0,
                )
            )
        )
        bank_row = bank_result.one_or_none()
        
        mpesa_credits = float(mpesa_row.total_credits or 0) if mpesa_row else 0
        bank_credits = float(bank_row.total_credits or 0) if bank_row else 0
        
        return {
            "mpesa_credits": mpesa_credits,
            "bank_credits": bank_credits,
            "total_credits": mpesa_credits + bank_credits,
            "estimated_monthly_income": (mpesa_credits + bank_credits) / (days / 30),
            "primary_source": "mpesa" if mpesa_credits > bank_credits else "bank",
        }
    
    # Future Enhancements: 
    # TODO: Add transaction categorization queries
    # TODO: Add recurring payment detection
    # TODO: Add spending pattern analysis