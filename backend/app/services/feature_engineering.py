# Feature Engineering Service.
# Generates ML features from raw customer, loan, and transaction data.

from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import UUID

import numpy as np
import pandas as pd

from app.config import settings
from app.core.logging_config import get_logger
from app.repositories.activity_repository import ActivityRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.transaction_repository import TransactionRepository

logger = get_logger(__name__)

class FeatureEngineeringService:
    
    def __init__(self):
        pass
    
    async def generate_customer_features(
        self,
        customer_id: UUID,
        customer_repo: CustomerRepository,
        loan_repo: LoanRepository,
        transaction_repo: TransactionRepository,
        activity_repo: Optional[ActivityRepository] = None,
    ) -> Dict[str, float]:

        features = {}
        
        # Get customer data
        customer = await customer_repo.get_by_id(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
    
        # 1. RECENCY FEATURES 
        features.update(await self._extract_recency_features(
            customer_id, loan_repo, activity_repo, transaction_repo
        ))
        
        # 2. FREQUENCY FEATURES 
        features.update(await self._extract_frequency_features(
            customer_id, loan_repo, activity_repo, transaction_repo
        ))
        
        # 3. MONETARY FEATURES 
        features.update(await self._extract_monetary_features(
            customer_id, customer, loan_repo, transaction_repo
        ))
        
        # 4. ENGAGEMENT FEATURES 
        features.update(await self._extract_engagement_features(
            customer_id, activity_repo
        ))
        
        # 5. FINANCIAL FEATURES
        features.update(await self._extract_financial_features(
            customer_id, transaction_repo
        ))
 
        # 6. CREDIT FEATURES 
        features.update(await self._extract_credit_features(
            customer_id, loan_repo
        ))

        # 7. DEMOGRAPHIC FEATURES 
        features.update(self._extract_demographic_features(customer))
        
        # 8. EXTERNAL FEATURES 
        features.update(self._extract_external_features(customer))
        
        # 9. DERIVED FEATURES 
        features.update(self._extract_derived_features(features))
        
        logger.info("features_generated", customer_id=str(customer_id), feature_count=len(features))
        
        return features
    
    async def _extract_recency_features(
        self,
        customer_id: UUID,
        loan_repo: LoanRepository,
        activity_repo: Optional[ActivityRepository],
        transaction_repo: TransactionRepository,
    ) -> Dict[str, float]:
        # Extract recency-based features.
        features = {}
        now = datetime.now(timezone.utc)
        
        # Days since last loan
        loans = await loan_repo.get_by_customer(customer_id, limit=1)
        if loans:
            last_loan_date = loans[0].created_at
            features["days_since_last_loan"] = (now - last_loan_date).days
        else:
            features["days_since_last_loan"] = 365  # No loans taken
        
        # Days since last login
        if activity_repo:
            latest_activity = await activity_repo.get_latest_activity(customer_id)
            if latest_activity:
                features["days_since_last_login"] = (date.today() - latest_activity.login_date).days
            else:
                features["days_since_last_login"] = 365
        else:
            features["days_since_last_login"] = 180  # Default
        
        # Days since last transaction
        # Use M-Pesa as primary source
        mpesa_summary = await transaction_repo.get_mpesa_summary(customer_id, days=365)
        if mpesa_summary["last_transaction"]:
            features["days_since_last_transaction"] = (now - mpesa_summary["last_transaction"]).days
        else:
            features["days_since_last_transaction"] = 365
        
        return features
    
    async def _extract_frequency_features(
        self,
        customer_id: UUID,
        loan_repo: LoanRepository,
        activity_repo: Optional[ActivityRepository],
        transaction_repo: TransactionRepository,
    ) -> Dict[str, float]:
        # Extract frequency-based features.
        features = {}
        
        # Loans in last 3 months
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        # TODO: Filter by date in query
        loans = await loan_repo.get_by_customer(customer_id)
        recent_loans = [l for l in loans if l.created_at >= three_months_ago]
        features["loans_last_3_months"] = len(recent_loans)
        
        # Transactions in last 30 days
        mpesa_summary = await transaction_repo.get_mpesa_summary(customer_id, days=30)
        features["transactions_last_30_days"] = mpesa_summary["transaction_count"]
        
        # App sessions in last 30 days
        if activity_repo:
            engagement = await activity_repo.get_engagement_summary(customer_id, days=30)
            features["app_sessions_last_30_days"] = engagement["total_sessions"]
        else:
            features["app_sessions_last_30_days"] = 0
        
        return features
    
    async def _extract_monetary_features(
        self,
        customer_id: UUID,
        customer,
        loan_repo: LoanRepository,
        transaction_repo: TransactionRepository,
    ) -> Dict[str, float]:
        # Extract monetary features.
        features = {}
        
        # Total loan value
        loan_summary = await loan_repo.get_loan_summary_by_customer(customer_id)
        features["total_loan_value"] = loan_summary["total_borrowed"]
        features["average_loan_size"] = (
            loan_summary["total_borrowed"] / max(loan_summary["total_loans"], 1)
        )
        
        # Average monthly income
        income = customer.income or 0
        features["average_monthly_income"] = income
        
        # Average balance from transactions
        mpesa_summary = await transaction_repo.get_mpesa_summary(customer_id, days=90)
        features["average_balance"] = mpesa_summary["avg_amount"]
        
        return features
    
    async def _extract_engagement_features(
        self,
        customer_id: UUID,
        activity_repo: Optional[ActivityRepository],
    ) -> Dict[str, float]:
        # Extract engagement features.
        features = {}
        
        if activity_repo:
            engagement = await activity_repo.get_engagement_summary(customer_id, days=30)
            features["session_duration"] = engagement["total_duration"] / max(engagement["total_sessions"], 1)
            features["active_days"] = engagement["total_sessions"]
            features["app_usage_frequency"] = engagement["total_sessions"] / 30.0
            features["notification_open_rate"] = 0.5  # TODO: Calculate from notification data
            features["engagement_score"] = engagement["avg_engagement"]
        else:
            features["session_duration"] = 0
            features["active_days"] = 0
            features["app_usage_frequency"] = 0
            features["notification_open_rate"] = 0
            features["engagement_score"] = 0
        
        return features
    
    async def _extract_financial_features(
        self,
        customer_id: UUID,
        transaction_repo: TransactionRepository,
    ) -> Dict[str, float]:
        """Extract financial health features."""
        features = {}
        
        # Income trend (3-month vs 6-month)
        income_3m = await transaction_repo.get_combined_income_estimate(customer_id, days=90)
        income_6m = await transaction_repo.get_combined_income_estimate(customer_id, days=180)
        
        if income_6m["estimated_monthly_income"] > 0:
            features["income_trend"] = (
                income_3m["estimated_monthly_income"] / income_6m["estimated_monthly_income"]
            )
        else:
            features["income_trend"] = 1.0
        
        # Expense trend 
        features["expense_trend"] = 1.0  # TODO: Calculate from categorized expenses
        
        # Savings trend 
        features["savings_trend"] = 1.0  # TODO: Calculate from balance changes
        
        # Cash flow trend
        features["cash_flow_trend"] = features["income_trend"] / max(features["expense_trend"], 0.1)
        
        # Financial health score (composite)
        features["financial_health_score"] = (
            min(features["income_trend"] * 30, 30) +
            min(features["savings_trend"] * 30, 30) +
            min(features["cash_flow_trend"] * 20, 20) +
            20  # Base score
        )
        
        return features
    
    async def _extract_credit_features(
        self,
        customer_id: UUID,
        loan_repo: LoanRepository,
    ) -> Dict[str, float]:
        """Extract credit behavior features."""
        features = {}
        
        loan_summary = await loan_repo.get_loan_summary_by_customer(customer_id)
        loans = await loan_repo.get_by_customer(customer_id)
        
        # Repayment consistency
        if loans:
            on_time_loans = sum(1 for l in loans if l.days_past_due <= 5)
            features["repayment_consistency"] = on_time_loans / len(loans)
        else:
            features["repayment_consistency"] = 1.0  # No history = perfect
        
        # Debt to income ratio
        monthly_income = 50000  # TODO: Get from customer data
        monthly_obligations = loan_summary["total_outstanding"] * 0.1  # Assume 10% monthly
        features["debt_to_income_ratio"] = monthly_obligations / max(monthly_income, 1)
        
        # Missed payment count
        features["missed_payment_count"] = sum(
            1 for l in loans if l.days_past_due > 5
        )
        
        # Existing loan obligations
        features["existing_loan_obligations"] = loan_summary["total_outstanding"]
        
        # Credit utilization
        # TODO: Calculate based on approved limits vs outstanding
        
        return features
    
    def _extract_demographic_features(self, customer) -> Dict[str, float]:
        # Extract demographic features.
        features = {}
        
        # Employment status encoding
        status_map = {
            "EMPLOYED": 1.0,
            "SELF_EMPLOYED": 0.8,
            "INFORMAL": 0.6,
            "UNEMPLOYED": 0.3,
            "STUDENT": 0.5,
            "RETIRED": 0.4,
        }
        features["employment_status_encoded"] = status_map.get(
            customer.employment_status, 0.5
        )
        
        # Location encoding
        # TODO: Use actual county risk data
        county_risk = {
            "NAIROBI": 0.7,
            "MOMBASA": 0.6,
            "KISUMU": 0.5,
            "NAKURU": 0.6,
        }
        features["location_risk_score"] = county_risk.get(
            (customer.location or "").upper(), 0.5
        )
        
        # Customer tenure (days)
        tenure_days = (date.today() - customer.customer_since).days
        features["customer_tenure_days"] = tenure_days
        
        # Income stability (based on employment)
        features["income_stability_score"] = features["employment_status_encoded"]
        
        # Age proxy (from tenure)
        features["platform_maturity"] = min(tenure_days / 365, 5.0)  # Cap at 5 years
        
        return features
    
    def _extract_external_features(self, customer) -> Dict[str, float]:
        """Extract external data features."""
        features = {}
        
        # County unemployment rate
        features["county_unemployment_rate"] = 0.08  # National average
        
        # County inflation rate
        features["county_inflation_rate"] = 0.05  # National average
        
        # Financial access score
        features["financial_access_score"] = 0.7  # Based on M-Pesa penetration
        
        # Regional poverty index
        features["regional_poverty_index"] = 0.35  # National average
        
        return features
    
    def _extract_derived_features(self, base_features: Dict[str, float]) -> Dict[str, float]:
        # Extract derived/composite features."""
        features = {}
        
        # Loan frequency ratio
        features["loan_frequency_ratio"] = base_features.get("loans_last_3_months", 0) / 3.0
        
        # Transaction intensity
        features["transaction_intensity"] = base_features.get("transactions_last_30_days", 0) / 30.0
        
        # Income to loan ratio
        features["income_to_loan_ratio"] = (
            base_features.get("average_monthly_income", 0) /
            max(base_features.get("total_loan_value", 1), 1)
        )
        
        # Engagement to churn risk (inverse)
        features["engagement_churn_index"] = 1.0 - min(
            base_features.get("engagement_score", 0) / 100, 1.0
        )
        
        # Financial stress indicator
        features["financial_stress_index"] = (
            base_features.get("debt_to_income_ratio", 0) * 0.4 +
            (1 - base_features.get("repayment_consistency", 1)) * 0.3 +
            max(0, 1 - base_features.get("income_trend", 1)) * 0.3
        )
        
        # Overall customer value score
        features["customer_value_score"] = (
            min(base_features.get("total_loan_value", 0) / 100000, 1.0) * 0.3 +
            base_features.get("repayment_consistency", 0) * 0.3 +
            min(base_features.get("engagement_score", 0) / 100, 1.0) * 0.2 +
            min(base_features.get("financial_health_score", 0) / 100, 1.0) * 0.2
        )
        
        return features
    
    async def generate_training_dataset(
        self,
        customer_repo: CustomerRepository,
        loan_repo: LoanRepository,
        transaction_repo: TransactionRepository,
        activity_repo: Optional[ActivityRepository] = None,
    ) -> pd.DataFrame:

        customers = await customer_repo.get_all(limit=10000)
        
        records = []
        for customer in customers:
            try:
                features = await self.generate_customer_features(
                    customer.id, customer_repo, loan_repo, transaction_repo, activity_repo
                )
                
                # Add target variables
                # For churn: 1 if churned, 0 if active
                # For default: 1 if defaulted, 0 if repaid
                # For credit score: actual score or bucket
                
                features["customer_id"] = str(customer.id)
                features["churned"] = 0  
                features["defaulted"] = 0 
                features["credit_score_bucket"] = "medium" 
                
                records.append(features)
            except Exception as e:
                logger.error("feature_generation_error", customer_id=str(customer.id), error=str(e))
                continue
        
        df = pd.DataFrame(records)
        logger.info("training_dataset_generated", records=len(df), features=len(df.columns))
        
        return df
    
    # TODO: Add Feature Store integration (Feast)
    # TODO: Add real-time feature computation
    # TODO: Add feature drift detection
    # TODO: Add automated feature selection