# Prediction Models.
# Stores ML model predictions for audit, explainability, and retraining.

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.user import Base

class ChurnPrediction(Base):

    __tablename__ = "churn_predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    probability_of_churn = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False, index=True)
    prediction_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    model_version = Column(String(50), nullable=False)
    features_snapshot = Column(JSONB, default=dict)
    shap_values = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    customer = relationship("Customer", back_populates="churn_predictions")
    
    # TODO: Add prediction feedback (actual churn outcome)
    # TODO: Add feature drift indicators
    # TODO: Add prediction latency metrics
    # TODO: Add multi-tenancy: tenant_id field
    
    def __repr__(self) -> str:
        return f"<ChurnPrediction(customer={self.customer_id}, prob={self.probability_of_churn:.2f})>"