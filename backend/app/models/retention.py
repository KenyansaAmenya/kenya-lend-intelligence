# Retention Action Model.
# will use this to Track retention interventions and their outcomes.

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.user import Base


class RetentionAction(Base):
    
    __tablename__ = "retention_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    description = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    customer = relationship("Customer", back_populates="retention_actions")
    
    # TODO: Add campaign_id for grouping related actions
    # TODO: Add cost tracking for ROI analysis
    # TODO: Add customer response tracking
    # TODO: Add automated follow-up scheduling
    # TODO: Add multi-tenancy: tenant_id field
    
    def __repr__(self) -> str:
        return f"<RetentionAction(customer={self.customer_id}, type={self.action_type}, status={self.status})>"