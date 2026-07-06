# Credit Scoring Service.
# Handles credit score generation, risk assessment, and loan pricing.

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

import numpy as np

from app.config import settings
from app.core.audit import AuditEventType, AuditLogger
from app.core.exceptions import MLModelError, ResourceNotFoundError
from app.core.logging_config import get_logger
from app.repositories.customer_repository import CustomerRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.credit import CreditScoreRequest, CreditScoreResponse, RiskAssessmentRequest, RiskAssessmentResponse

logger = get_logger(__name__)

class CreditService:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        loan_repository: LoanRepository,
        transaction_repository: TransactionRepository,
    ):
        self.customer_repo = customer_repository
        self.loan_repo = loan_repository
        self.transaction_repo = transaction_repository
        self.audit = AuditLogger()
        
        # Load models (lazy loading)
        self._credit_model = None
        self._default_model = None
        self._preprocessor = None
        self._feature_columns = None
    
    def _load_model(self, model_path: str):
        try:
            with open(model_path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            logger.warning("model_not_found", path=model_path)
            return None
        except Exception as e:
            logger.error("model_load_error", error=str(e))
            return None
    
    @property
    def credit_model(self):
        if self._credit_model is None:
            self._credit_model = self._load_model(settings.credit_model_path)
        return self._credit_model
    
    @property
    def default_model(self):
        if self._default_model is None:
            self._default_model = self._load_model(settings.default_model_path)
        return self._default_model
    
    @property
    def preprocessor(self):
        if self._preprocessor is None:
            self._preprocessor = self._load_model(settings.preprocessor_path)
        return self._preprocessor
    
    def _load_feature_columns(self) -> List[str]:
        try:
            path = Path(settings.model_path) / "feature_columns.json"
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Default feature list
            return [
                "income", "employment_status_encoded", "location_encoded",
                "total_loans", "total_borrowed", "total_outstanding",
                "avg_dpd", "days_since_last_loan", "days_since_last_login",
                "engagement_score", "transaction_count", "avg_transaction_amount",
                "income_trend", "expense_trend", "savings_rate",
            ]
    
    def _extract_features(self, customer_id: UUID) -> Dict[str, float]:
        return {
            "income": 50000.0,
            "employment_status_encoded": 1,
            "location_encoded": 2,
            "total_loans": 3,
            "total_borrowed": 150000.0,
            "total_outstanding": 50000.0,
            "avg_dpd": 5.0,
            "days_since_last_loan": 30,
            "days_since_last_login": 2,
            "engagement_score": 75.0,
            "transaction_count": 50,
            "avg_transaction_amount": 2000.0,
            "income_trend": 1.05,
            "expense_trend": 0.98,
            "savings_rate": 0.15,
        }
    
    def _calculate_credit_score(self, features: Dict[str, float]) -> int:
        if self.credit_model is not None:
            try:
                X = np.array([list(features.values())]).reshape(1, -1)
                # Model might output probability or direct score
                raw_score = self.credit_model.predict(X)[0]
                # Scale to 300-850 range if needed
                if raw_score < 300:
                    score = int(300 + (raw_score * 550))
                else:
                    score = int(raw_score)
                return max(300, min(850, score))
            except Exception as e:
                logger.error("credit_model_error", error=str(e))
        
        # Fallback: rule-based scoring
        score = 550  # Base score
        
        # Income factor (max +100)
        income = features.get("income", 0)
        if income > 100000:
            score += 100
        elif income > 50000:
            score += 75
        elif income > 30000:
            score += 50
        elif income > 15000:
            score += 25
        
        # Repayment history (max +100)
        avg_dpd = features.get("avg_dpd", 0)
        if avg_dpd == 0:
            score += 100
        elif avg_dpd < 5:
            score += 75
        elif avg_dpd < 15:
            score += 50
        elif avg_dpd < 30:
            score += 25
        
        # Engagement (max +50)
        engagement = features.get("engagement_score", 0)
        score += int(engagement * 0.5)
        
        # Savings rate (max +50)
        savings_rate = features.get("savings_rate", 0)
        score += int(min(savings_rate * 200, 50))
        
        return max(300, min(850, score))
    
    def _calculate_default_probability(self, features: Dict[str, float]) -> float:
        if self.default_model is not None:
            try:
                X = np.array([list(features.values())]).reshape(1, -1)
                prob = self.default_model.predict_proba(X)[0][1]
                return float(prob)
            except Exception as e:
                logger.error("default_model_error", error=str(e))
        
        # Fallback: heuristic-based probability
        prob = 0.15  # Base probability
        
        # Income factor
        income = features.get("income", 0)
        if income < 20000:
            prob += 0.15
        elif income < 50000:
            prob += 0.05
        
        # DPD factor
        avg_dpd = features.get("avg_dpd", 0)
        if avg_dpd > 30:
            prob += 0.25
        elif avg_dpd > 15:
            prob += 0.15
        elif avg_dpd > 5:
            prob += 0.05
        
        # Engagement factor
        engagement = features.get("engagement_score", 0)
        if engagement < 30:
            prob += 0.1
        
        return min(0.95, max(0.01, prob))
    
    def _get_risk_level(self, credit_score: int, default_prob: float) -> str:
        if credit_score >= 750 and default_prob < 0.05:
            return "VERY_LOW"
        elif credit_score >= 650 and default_prob < 0.1:
            return "LOW"
        elif credit_score >= 550 and default_prob < 0.2:
            return "MEDIUM"
        elif credit_score >= 450 and default_prob < 0.35:
            return "HIGH"
        else:
            return "VERY_HIGH"
    
    def _calculate_recommended_limit(self, credit_score: int, income: float, default_prob: float) -> float:
        # Base limit on income
        base_limit = income * 0.5
        
        # Adjust by credit score
        if credit_score >= 750:
            multiplier = 1.5
        elif credit_score >= 650:
            multiplier = 1.2
        elif credit_score >= 550:
            multiplier = 1.0
        elif credit_score >= 450:
            multiplier = 0.7
        else:
            multiplier = 0.4
        
        # Adjust by default probability
        if default_prob > 0.3:
            multiplier *= 0.5
        elif default_prob > 0.2:
            multiplier *= 0.7
        
        limit = base_limit * multiplier
        return round(min(limit, 500000), 2)  # Max KES 500,000
    
    def _calculate_interest_rate(self, credit_score: int, default_prob: float) -> float:
        base_rate = settings.base_interest_rate  # 15%
        
        # Risk adjustment
        if credit_score >= 750:
            adjustment = -0.03
        elif credit_score >= 650:
            adjustment = -0.01
        elif credit_score >= 550:
            adjustment = 0.0
        elif credit_score >= 450:
            adjustment = 0.05
        else:
            adjustment = 0.1
        
        # Default probability adjustment
        if default_prob > 0.3:
            adjustment += 0.05
        elif default_prob > 0.2:
            adjustment += 0.03
        
        rate = base_rate + adjustment
        return round(min(rate, settings.max_interest_rate), 4)
    
    async def generate_credit_score(self, request: CreditScoreRequest) -> CreditScoreResponse:
        customer = await self.customer_repo.get_by_id(request.customer_id)
        if not customer:
            raise ResourceNotFoundError("Customer")
        
        # Extract features
        features = self._extract_features(request.customer_id)
        
        # Calculate metrics
        credit_score = self._calculate_credit_score(features)
        default_prob = self._calculate_default_probability(features)
        risk_level = self._get_risk_level(credit_score, default_prob)
        recommended_limit = self._calculate_recommended_limit(
            credit_score, features.get("income", 0), default_prob
        )
        interest_rate = self._calculate_interest_rate(credit_score, default_prob)
        
        # Build score factors
        score_factors = [
            {"factor": "Income Level", "impact": "positive" if features["income"] > 50000 else "neutral", "weight": 0.25},
            {"factor": "Repayment History", "impact": "positive" if features["avg_dpd"] < 5 else "negative", "weight": 0.30},
            {"factor": "Engagement Score", "impact": "positive" if features["engagement_score"] > 60 else "neutral", "weight": 0.20},
            {"factor": "Savings Rate", "impact": "positive" if features["savings_rate"] > 0.1 else "neutral", "weight": 0.15},
            {"factor": "Transaction Activity", "impact": "positive" if features["transaction_count"] > 30 else "neutral", "weight": 0.10},
        ]
        
        response = CreditScoreResponse(
            customer_id=request.customer_id,
            credit_score=credit_score,
            risk_level=risk_level,
            recommended_limit=recommended_limit,
            recommended_interest_rate=interest_rate,
            score_date=datetime.now(timezone.utc),
            model_version="v1.0.0-fallback",
            score_factors=score_factors,
            shap_explanation=None,  # TODO: Add SHAP explainability
        )
        
        logger.info(
            "credit_score_generated",
            customer_id=str(request.customer_id),
            score=credit_score,
            risk_level=risk_level,
        )
        
        await self.audit.log_event(
            event_type=AuditEventType.CREDIT_SCORE_GENERATED,
            resource_type="customer",
            resource_id=str(request.customer_id),
            details={
                "credit_score": credit_score,
                "risk_level": risk_level,
                "recommended_limit": recommended_limit,
            },
        )
        
        return response
    
    async def assess_risk(self, request: RiskAssessmentRequest) -> RiskAssessmentResponse:
        features = self._extract_features(request.customer_id)
        default_prob = self._calculate_default_probability(features)
        credit_score = self._calculate_credit_score(features)
        risk_level = self._get_risk_level(credit_score, default_prob)
        
        # Affordability calculation
        monthly_income = features.get("income", 0) / 12
        existing_obligations = features.get("total_outstanding", 0) * 0.1  # Assume 10% monthly
        max_affordable = monthly_income * 0.4 - existing_obligations  # 40% DTI rule
        
        dti_ratio = (existing_obligations / monthly_income) if monthly_income > 0 else 1.0
        
        recommended_amount = min(request.requested_amount, max_affordable)
        if default_prob > 0.3:
            recommended_amount *= 0.5
        
        return RiskAssessmentResponse(
            customer_id=request.customer_id,
            probability_of_default=default_prob,
            risk_level=risk_level,
            recommended_amount=round(max(0, recommended_amount), 2),
            recommended_rate=self._calculate_interest_rate(credit_score, default_prob),
            max_affordable_payment=round(max_affordable, 2),
            debt_to_income_ratio=round(dti_ratio, 4),
            assessment_date=datetime.now(timezone.utc),
        )
    
    # TODO: Add credit bureau integration
    # TODO: Add alternative data scoring
    # TODO: Add model A/B testing framework
    # TODO: Add real-time feature computation
