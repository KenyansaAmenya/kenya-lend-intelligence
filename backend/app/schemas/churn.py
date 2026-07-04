# Churn Prediction Schemas.
# Request and response models for churn prediction,
# customer segmentation, and retention management.

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ChurnPredictionRequest(BaseModel):
    customer_id: Optional[UUID] = Field(default=None, description="Specific customer ID or None for batch")
    lookback_days: Optional[int] = Field(default=90, ge=30, le=365, description="Lookback period")

class ChurnPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    customer_id: UUID
    probability_of_churn: float = Field(..., ge=0, le=1)
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    prediction_date: datetime
    model_version: str
    churn_drivers: List[dict] = Field(default_factory=list, description="Top churn drivers")
    shap_values: Optional[dict] = Field(default=None, description="SHAP explainability")
    features_used: Optional[dict] = Field(default=None, description="Feature values used")

class ChurnPredictionBatchResponse(BaseModel):
    predictions: List[ChurnPredictionResponse]
    total_processed: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int

class CustomerSegment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    customer_id: UUID
    segment: str = Field(..., description="Segment name")
    created_at: datetime
class SegmentDistribution(BaseModel):
    segment: str
    count: int
    percentage: float
    average_churn_probability: float
    average_credit_score: Optional[float] = None

class AtRiskCustomer(BaseModel):
    customer_id: UUID
    full_name: str
    phone: str
    probability_of_churn: float
    risk_level: str
    days_since_last_loan: Optional[int] = None
    days_since_last_login: Optional[int] = None
    total_loan_value: Optional[float] = None
    last_prediction_date: Optional[datetime] = None
class AtRiskListResponse(BaseModel):
    items: List[AtRiskCustomer]
    total: int
    page: int
    page_size: int

class ChurnTrend(BaseModel):
    month: str
    churn_rate: float
    total_customers: int
    churned_customers: int
    new_customers: int

class RetentionRecommendation(BaseModel):
    customer_id: UUID
    full_name: str
    probability_of_churn: float
    segment: str
    recommended_action: str
    action_priority: str = Field(..., description="LOW, MEDIUM, HIGH, URGENT")
    expected_impact: str
    suggested_offer: Optional[str] = None

class RetentionRecommendationBatch(BaseModel):
    recommendations: List[RetentionRecommendation]
    total: int
    urgent_count: int
    high_priority_count: int

class RetentionActionCreate(BaseModel):
    customer_id: UUID
    action_type: str = Field(..., description="Type of retention action")
    description: Optional[str] = None

class RetentionActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    customer_id: UUID
    action_type: str
    status: str
    description: Optional[str] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    created_at: datetime


# TODO: Add churn cohort analysis schemas
# TODO: Add retention campaign performance schemas
# TODO: Add customer lifetime value schemas