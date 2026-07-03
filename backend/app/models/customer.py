# Customer Model.

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.user import Base


class EmploymentStatus(str, PyEnum):

    EMPLOYED = "EMPLOYED"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    UNEMPLOYED = "UNEMPLOYED"
    STUDENT = "STUDENT"
    RETIRED = "RETIRED"
    INFORMAL = "INFORMAL"

class Customer(Base):

    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    national_id = Column(String(20), unique=True, nullable=False, index=True)
    location = Column(String(100), nullable=True)  # County in Kenya
    occupation = Column(String(255), nullable=True)
    employment_status = Column(String(50), default=EmploymentStatus.INFORMAL.value)
    income = Column(Float, nullable=True)  # Monthly income in KES
    customer_since = Column(Date, default=lambda: datetime.now(timezone.utc).date())
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Relationships
    loans = relationship("Loan", back_populates="customer", cascade="all, delete-orphan")
    activities = relationship("CustomerActivity", back_populates="customer", cascade="all, delete-orphan")
    mpesa_transactions = relationship("MpesaTransaction", back_populates="customer", cascade="all, delete-orphan")
    bank_transactions = relationship("BankTransaction", back_populates="customer", cascade="all, delete-orphan")
    churn_predictions = relationship("ChurnPrediction", back_populates="customer", cascade="all, delete-orphan")
    segments = relationship("CustomerSegment", back_populates="customer", cascade="all, delete-orphan")
    retention_actions = relationship("RetentionAction", back_populates="customer", cascade="all, delete-orphan")
    
    # TODO: Add KYC verification fields (verified_at, verification_method)
    # TODO: Add credit bureau reference numbers
    # TODO: Add customer consent flags for data usage
    # TODO: Add customer risk rating cache
    # TODO: Add multi-tenancy: tenant_id field
    
    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name={self.full_name}, phone={self.phone})>"

# Future Enhancements:
    # - Add KYC verification status and documents
    # - Add alternative ID support (passport, alien card)
    # - Add biometric data references
    # - Add customer consent management        