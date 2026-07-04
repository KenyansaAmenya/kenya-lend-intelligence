# Customer Schemas.
# Request and response models for customer management,
# including demographic, financial, and behavioral data.

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

class CustomerBase(BaseModel):
    # Base customer schema.
    model_config = ConfigDict(from_attributes=True)
    
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name")
    phone: str = Field(..., description="M-Pesa linked phone number")
    national_id: str = Field(..., min_length=5, max_length=20, description="Kenyan National ID")
    location: Optional[str] = Field(default=None, description="County/Region in Kenya")
    occupation: Optional[str] = Field(default=None, max_length=255, description="Job or business type")
    employment_status: Optional[str] = Field(default="INFORMAL", description="Employment status")
    income: Optional[float] = Field(default=None, ge=0, description="Monthly income in KES")
    
    @field_validator("phone")
    @classmethod
    def validate_kenyan_phone(cls, v: str) -> str:
        # Validate phone number format.
        # Remove spaces and dashes
        cleaned = v.replace(" ", "").replace("-", "")
        # Check for valid Kenyan formats: +2547..., 07..., 01...
        if not (cleaned.startswith("+254") or cleaned.startswith("07") or cleaned.startswith("01")):
            raise ValueError("Invalid Kenyan phone number format")
        return cleaned
    
    @field_validator("national_id")
    @classmethod
    def validate_national_id(cls, v: str) -> str:
        # Kenyan IDs are typically 8 digits
        cleaned = v.strip()
        if not cleaned.isdigit() or len(cleaned) < 5:
            raise ValueError("Invalid National ID format")
        return cleaned


class CustomerCreate(CustomerBase):
    pass
class CustomerUpdate(BaseModel):
    
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    phone: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    occupation: Optional[str] = Field(default=None)
    employment_status: Optional[str] = Field(default=None)
    income: Optional[float] = Field(default=None, ge=0)

class CustomerResponse(CustomerBase):
    id: UUID
    customer_since: date
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    total_loans: Optional[int] = Field(default=None, description="Total number of loans")
    active_loans: Optional[int] = Field(default=None, description="Number of active loans")
    total_borrowed: Optional[float] = Field(default=None, description="Total amount borrowed")
    health_score: Optional[float] = Field(default=None, ge=0, le=100, description="Customer health score")

class CustomerListResponse(BaseModel):
    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    pages: int

class CustomerDetailResponse(CustomerResponse):
    
    loans: Optional[List["LoanResponse"]] = None
    recent_activity: Optional[List["ActivityResponse"]] = None
    credit_score: Optional[int] = None
    churn_probability: Optional[float] = None
    segment: Optional[str] = None

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    login_date: date
    session_duration: int
    app_opens: int
    engagement_score: float
    device_type: Optional[str] = None

class CustomerHealthScore(BaseModel):
    customer_id: UUID
    health_score: float = Field(..., ge=0, le=100)
    score_components: dict
    assessment_date: datetime


# TODO: Add KYC document schemas
# TODO: Add customer consent schemas
# TODO: Add customer note/comment schemas

