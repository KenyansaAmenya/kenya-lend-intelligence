# Request and response models for loan applications,
# decisions, and management.

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

class LoanBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    amount: float = Field(..., gt=0, description="Loan amount in KES")
    interest_rate: float = Field(..., ge=0, le=1, description="Annual interest rate (decimal)")

class LoanCreate(LoanBase):
    customer_id: UUID = Field(..., description="Customer ID")
    term_months: Optional[int] = Field(default=1, ge=1, le=24, description="Loan term in months")
    
    @field_validator("amount")
    @classmethod
    def validate_loan_amount(cls, v: float) -> float:
        if v < 500:
            raise ValueError("Minimum loan amount is KES 500")
        if v > 500000:
            raise ValueError("Maximum loan amount is KES 500,000")
        return v

class LoanUpdate(BaseModel):
    status: Optional[str] = Field(default=None, description="New loan status")
    approved_amount: Optional[float] = Field(default=None, ge=0)
    outstanding_balance: Optional[float] = Field(default=None, ge=0)
    days_past_due: Optional[int] = Field(default=None, ge=0)

class LoanResponse(LoanBase):
    
    id: UUID
    customer_id: UUID
    outstanding_balance: float
    days_past_due: int
    status: str
    approved_amount: Optional[float] = None
    approved_at: Optional[datetime] = None
    disbursed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    predicted_default_probability: Optional[float] = None
    credit_score_at_application: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class LoanListResponse(BaseModel):
    
    items: List[LoanResponse]
    total: int
    page: int
    page_size: int
    pages: int

class LoanDecisionRequest(BaseModel):
    
    customer_id: UUID = Field(..., description="Customer ID")
    amount: float = Field(..., gt=0, description="Requested loan amount")
    term_months: int = Field(default=1, ge=1, le=24, description="Loan term")
    statement_type: str = Field(default="mpesa", description="Statement type: mpesa, bank, or combined")

class LoanDecisionResponse(BaseModel):
    
    customer_id: UUID
    decision: str = Field(..., description="APPROVED, REJECTED, or MANUAL_REVIEW")
    approved_amount: Optional[float] = Field(default=None, description="Approved loan amount")
    interest_rate: Optional[float] = Field(default=None, description="Recommended interest rate")
    probability_of_default: float = Field(..., ge=0, le=1, description="Predicted default probability")
    credit_score: int = Field(..., ge=300, le=850, description="Customer credit score")
    risk_level: str = Field(..., description="Risk classification")
    affordability_assessment: dict = Field(default_factory=dict, description="Affordability details")
    explanation: dict = Field(default_factory=dict, description="Decision explanation (SHAP)")
    decision_date: datetime = Field(default_factory=datetime.utcnow)

class LoanApprovalTrend(BaseModel):
    
    month: str
    total_applications: int
    approved: int
    rejected: int
    manual_review: int
    average_amount: float

# TODO: Add loan product type schemas
# TODO: Add repayment installment schemas
# TODO: Add loan restructuring schemas
