# Customer Activity Model.
# will Use this for churn prediction and customer health scoring.

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.user import Base

class CustomerActivity(Base):

    __tablename__ = "customer_activity"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    login_date = Column(Date, default=lambda: datetime.now(timezone.utc).date(), index=True)
    session_duration = Column(Integer, default=0) 
    app_opens = Column(Integer, default=0)
    feature_usage = Column(JSONB, default=dict)  
    device_type = Column(String(50), nullable=True)  
    notification_opens = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)  
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    customer = relationship("Customer", back_populates="activities")
    
    # TODO: Add real-time streaming to Kafka for live analytics
    # TODO: Add session replay reference IDs
    # TODO: Add A/B test variant tracking
    # TODO: Add customer journey stage tracking

    # Future Enhancements:
    # - Add push notification interaction tracking
    # - Add in-app feature usage analytics
    # - Add customer journey mapping
    # - Add real-time activity streaming (Kafka)
    
    def __repr__(self) -> str:
        return f"<CustomerActivity(customer={self.customer_id}, date={self.login_date})>"