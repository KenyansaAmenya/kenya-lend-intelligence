# Customer Segmentation Model.
# This will Store customer segmentation results from clustering algorithms

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.user import Base


class CustomerSegment(Base):
    
    __tablename__ = "customer_segments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    segment = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    customer = relationship("Customer", back_populates="segments")
    
    # TODO: Add segment confidence score
    # TODO: Add segment migration history
    # TODO: Add segment-specific offer tracking
    # TODO: Add multi-tenancy: tenant_id field
    
    def __repr__(self) -> str:
        return f"<CustomerSegment(customer={self.customer_id}, segment={self.segment})>"