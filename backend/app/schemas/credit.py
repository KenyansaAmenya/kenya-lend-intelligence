# Credit Scoring Schemas.
# Request and response models for credit scoring,
# risk assessment, and loan pricing.

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class CreditScoreRequest(BaseModel):
    customer_id: UUID = Field(..., description="Customer ID")
    use_statement_data: bool = Field(default=True, description="Include statement analysis")
    statement_type: Optional[str] = Field(default="mpesa", description="mpesa, bank, or combined")

class CreditScoreResponse(BaseModel):
    customer_id: UUID
    credit_score: int = Field(..., ge=300, le=850, description="Credit score (300-850)")
    risk_level: str = Field(..., description="VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH")
    recommended_limit: float = Field(..., description="Recommended loan limit in KES")
    recommended_interest_rate: float = Field(..., description="Recommended annual interest rate")
    score_date: datetime
    model_version: str
    score_factors: List[dict] = Field(default_factory=list, description="Factors affecting score")
    shap_explanation: Optional[dict] = Field(default=None, description="SHAP explainability")

class RiskAssessmentRequest(BaseModel):
    customer_id: UUID
    requested_amount: float = Field(..., gt=0, description="Requested loan amount")

class RiskAssessmentResponse(BaseModel):
    customer_id: UUID
    probability_of_default: float = Field(..., ge=0, le=1)
    risk_level: str
    recommended_amount: float
    recommended_rate: float
    max_affordable_payment: float
    debt_to_income_ratio: float
    assessment_date: datetime

class CreditScoreTrend(BaseModel):
    month: str
    average_score: float
    median_score: float
    score_distribution: dict

class CreditScoreDistribution(BaseModel):
    score_range: str
    count: int
    percentage: float
    average_default_rate: Optional[float] = None


# TODO: Add credit bureau report schemas
# TODO: Add alternative data scoring schemas
# TODO: Add dynamic pricing optimization schemas
# TODO: Add portfolio risk monitoring schemas
# TODO: Add scorecard Defination (Model Management) schemas