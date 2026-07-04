# Request and response models for M-Pesa and bank statement uploads,
# processing, and analysis.

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class StatementUploadRequest(BaseModel):
    customer_id: UUID = Field(..., description="Customer ID")
    statement_type: str = Field(..., description="mpesa or bank")
    statement_period_start: Optional[datetime] = None
    statement_period_end: Optional[datetime] = None

class StatementUploadResponse(BaseModel):
    upload_id: UUID
    customer_id: UUID
    statement_type: str
    file_name: str
    file_size: int
    status: str = Field(..., description="PENDING, PROCESSING, COMPLETED, FAILED")
    storage_path: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    transaction_count: Optional[int] = None
    error_message: Optional[str] = None

class StatementAnalysisRequest(BaseModel):
    customer_id: UUID
    statement_type: str = Field(default="mpesa", description="mpesa, bank, or combined")

class StatementAnalysisResponse(BaseModel):
    customer_id: UUID
    statement_type: str
    analysis_date: datetime
    period_covered: dict = Field(default_factory=dict)
    
    # Income analysis
    total_income: float
    average_monthly_income: float
    income_sources: List[dict] = Field(default_factory=list)
    income_stability_score: float = Field(..., ge=0, le=100)
    salary_detected: bool
    
    # Spending analysis
    total_expenses: float
    average_monthly_expenses: float
    expense_categories: List[dict] = Field(default_factory=list)
    spending_stability_score: float = Field(..., ge=0, le=100)
    
    # Savings analysis
    total_savings: float
    savings_rate: float
    savings_trend: str = Field(..., description="INCREASING, STABLE, DECREASING")
    
    # Cash flow
    net_cash_flow: float
    cash_flow_trend: str
    negative_balance_days: int
    
    # Risk indicators
    gambling_indicators: Optional[List[str]] = None
    frequent_overdrafts: bool
    irregular_income_pattern: bool
    
    # Financial health
    financial_health_score: float = Field(..., ge=0, le=100)

class ExternalDatasetUpload(BaseModel):
    dataset_name: str = Field(..., description="Dataset name")
    dataset_type: str = Field(..., description="Type: macroeconomic, demographic, etc.")
    description: Optional[str] = None
    source_url: Optional[str] = None

class ExternalDatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    dataset_name: str
    dataset_type: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    file_path: str
    record_count: Optional[int] = None
    uploaded_at: datetime
    status: str


# TODO: Add real-time statement streaming schemas
# TODO: Add statement fraud detection schemas
# TODO: Add multi-currency support schemas
# TODO: Add transaction categorization schemas
# TODO: Add income & employment verification schemas
# TODO: spending pattern analysis schemas