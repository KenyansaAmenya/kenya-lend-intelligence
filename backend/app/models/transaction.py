# Transaction Models.
# M-Pesa and Bank transaction models for statement parsing and analysis.

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.user import Base

class MpesaTransaction(Base):
    
    __tablename__ = "mpesa_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    balance = Column(Float, nullable=True)
    reference = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    customer = relationship("Customer", back_populates="mpesa_transactions")
    
    def __repr__(self) -> str:
        return f"<MpesaTransaction(customer={self.customer_id}, amount={self.amount}, type={self.transaction_type})>"
class BankTransaction(Base):
    
    __tablename__ = "bank_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    balance = Column(Float, nullable=True)
    account_number_masked = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    customer = relationship("Customer", back_populates="bank_transactions")
    
    # Future Enhancements:
    # TODO: Add transaction categorization
    # TODO: Add standing order / recurring payment flags
    # TODO: Add loan obligation detection
    # TODO: Add real-time streaming integration
    # TODO: Add transaction categorization (salary, rent, utilities, etc.)
    # TODO: Add merchant identification and geolocation
    # TODO: Add anomaly detection flags
    # TODO: Add real-time streaming integration
    
    def __repr__(self) -> str:
        return f"<BankTransaction(customer={self.customer_id}, amount={self.amount}, type={self.transaction_type})>"