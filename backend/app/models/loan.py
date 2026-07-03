# Loan Model.
# Tracks repayment status and performance metrics.

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.user import Base


class LoanStatus(str, PyEnum):
    
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISBURSED = "DISBURSED"
    ACTIVE = "ACTIVE"
    REPAID = "REPAID"
    DEFAULTED = "DEFAULTED"
    WRITTEN_OFF = "WRITTEN_OFF"

class Loan(Base):
    
    __tablename__ = "loans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Requested amount
    interest_rate = Column(Float, nullable=False)  # Annual rate as decimal
    outstanding_balance = Column(Float, default=0.0)
    days_past_due = Column(Integer, default=0)
    status = Column(String(50), default=LoanStatus.PENDING.value, nullable=False, index=True)
    
    # Decisioning fields
    approved_amount = Column(Float, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    disbursed_at = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    # ML predictions at time of application
    predicted_default_probability = Column(Float, nullable=True)
    credit_score_at_application = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    customer = relationship("Customer", back_populates="loans")
    
    # TODO: Add loan product type (personal, business, emergency)
    # TODO: Add repayment schedule (installment details)
    # TODO: Add collateral information
    # TODO: Add collection agency tracking
    # TODO: Add restructuring history
    # TODO: Add multi-tenancy: tenant_id field

    # Future Enhancements:
    # - Add loan product types and configurations
    # - Add collateral information
    # - Add disbursement and repayment schedules
    # - Add collection tracking
    
    def __repr__(self) -> str:
        return f"<Loan(id={self.id}, amount={self.amount}, status={self.status})>"