# Churn Prediction Service.
# Handles churn prediction, risk assessment, and customer health monitoring.

import json
import pickle
from datetime import datetime, timedelta, timezone
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
from app.schemas.churn import ChurnPredictionRequest, ChurnPredictionResponse

logger = get_logger(__name__)

class ChurnService:
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
        
        self._churn_model = None
        self._preprocessor = None
    
    def _load_model(self, model_path: str):
        try:
            with open(model_path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            logger.warning("churn_model_not_found", path=model_path)
            return None
        except Exception as e:
            logger.error("churn_model_load_error", error=str(e))
            return None
    
    @property
    def churn_model(self):
        if self._churn_model is None:
            self._churn_model = self._load_model(settings.churn_model_path)
        return self._churn_model
    
    def _extract_churn_features(self, customer_id: UUID) -> Dict[str, float]:
        
        return {
            "days_since_last_loan": 45,
            "days_since_last_login": 5,
            "days_since_last_transaction": 3,
            "loans_last_3_months": 1,
            "transactions_last_30_days": 15,
            "app_sessions_last_30_days": 20,
            "total_loan_value": 100000.0,
            "average_loan_size": 50000.0,
            "average_monthly_income": 45000.0,
            "average_balance": 15000.0,
            "session_duration": 300,
            "active_days": 20,
            "app_usage_frequency": 0.67,
            "notification_open_rate": 0.4,
            "engagement_score": 65.0,
            "income_trend": 1.02,
            "expense_trend": 1.05,
            "savings_trend": 0.98,
            "cash_flow_trend": 0.95,
            "financial_health_score": 70.0,
            "repayment_consistency": 0.85,
            "debt_to_income_ratio": 0.3,
            "missed_payment_count": 1,
            "existing_loan_obligations": 50000.0,
            "county_unemployment_rate": 0.08,
            "county_inflation_rate": 0.05,
            "financial_access_score": 0.7,
            "regional_poverty_index": 0.35,
        }
    
    def _calculate_churn_probability(self, features: Dict[str, float]) -> float:
        if self.churn_model is not None:
            try:
                X = np.array([list(features.values())]).reshape(1, -1)
                prob = self.churn_model.predict_proba(X)[0][1]
                return float(prob)
            except Exception as e:
                logger.error("churn_model_error", error=str(e))
        
        # Fallback: heuristic-based churn probability
        prob = 0.2  # Base probability
        
        # Recency factors 
        days_since_loan = features.get("days_since_last_loan", 0)
        if days_since_loan > 90:
            prob += 0.3
        elif days_since_loan > 60:
            prob += 0.2
        elif days_since_loan > 30:
            prob += 0.1
        
        days_since_login = features.get("days_since_last_login", 0)
        if days_since_login > 14:
            prob += 0.15
        elif days_since_login > 7:
            prob += 0.08
        
        # Engagement factors
        engagement = features.get("engagement_score", 0)
        if engagement < 40:
            prob += 0.15
        elif engagement < 60:
            prob += 0.08
        
        app_usage = features.get("app_usage_frequency", 0)
        if app_usage < 0.3:
            prob += 0.1
        
        # Financial factors
        dti = features.get("debt_to_income_ratio", 0)
        if dti > 0.5:
            prob += 0.1
        
        missed_payments = features.get("missed_payment_count", 0)
        if missed_payments > 2:
            prob += 0.1
        
        # External factors
        unemployment = features.get("county_unemployment_rate", 0)
        if unemployment > 0.1:
            prob += 0.05
        
        return min(0.99, max(0.01, prob))
    
    def _get_risk_level(self, probability: float) -> str:
        if probability >= 0.8:
            return "CRITICAL"
        elif probability >= 0.6:
            return "HIGH"
        elif probability >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _identify_churn_drivers(self, features: Dict[str, float]) -> List[Dict]:
        drivers = []
        
        # Recency drivers
        if features.get("days_since_last_loan", 0) > 60:
            drivers.append({
                "factor": "Days Since Last Loan",
                "value": features["days_since_last_loan"],
                "impact": "high",
                "description": "Customer has not taken a loan in over 60 days",
            })
        
        if features.get("days_since_last_login", 0) > 7:
            drivers.append({
                "factor": "Days Since Last Login",
                "value": features["days_since_last_login"],
                "impact": "medium",
                "description": "Reduced app engagement detected",
            })
        
        # Engagement drivers
        if features.get("engagement_score", 100) < 50:
            drivers.append({
                "factor": "Low Engagement Score",
                "value": features["engagement_score"],
                "impact": "high",
                "description": "Customer engagement has dropped significantly",
            })
        
        # Financial drivers
        if features.get("debt_to_income_ratio", 0) > 0.5:
            drivers.append({
                "factor": "High Debt-to-Income Ratio",
                "value": features["debt_to_income_ratio"],
                "impact": "medium",
                "description": "Customer may be over-leveraged",
            })
        
        if features.get("missed_payment_count", 0) > 1:
            drivers.append({
                "factor": "Missed Payments",
                "value": features["missed_payment_count"],
                "impact": "high",
                "description": "Recent missed payments indicate financial stress",
            })
        
        # Sort by impact
        impact_order = {"high": 0, "medium": 1, "low": 2}
        drivers.sort(key=lambda x: impact_order.get(x["impact"], 3))
        
        return drivers[:5]  # Top 5 drivers
    
    async def predict_churn(self, request: ChurnPredictionRequest) -> ChurnPredictionResponse:
        if request.customer_id:
            customer = await self.customer_repo.get_by_id(request.customer_id)
            if not customer:
                raise ResourceNotFoundError("Customer")
        
        features = self._extract_churn_features(request.customer_id)
        probability = self._calculate_churn_probability(features)
        risk_level = self._get_risk_level(probability)
        churn_drivers = self._identify_churn_drivers(features)
        
        response = ChurnPredictionResponse(
            customer_id=request.customer_id,
            probability_of_churn=probability,
            risk_level=risk_level,
            prediction_date=datetime.now(timezone.utc),
            model_version="v1.0.0-fallback",
            churn_drivers=churn_drivers,
            shap_values=None,  # TODO: Add SHAP explainability
            features_used=features,
        )
        
        logger.info(
            "churn_prediction_made",
            customer_id=str(request.customer_id),
            probability=probability,
            risk_level=risk_level,
        )
        
        await self.audit.log_event(
            event_type=AuditEventType.CHURN_PREDICTION_MADE,
            resource_type="customer",
            resource_id=str(request.customer_id),
            details={
                "probability": probability,
                "risk_level": risk_level,
            },
        )
        
        return response
    
    async def predict_churn_batch(self, customer_ids: Optional[List[UUID]] = None) -> List[ChurnPredictionResponse]:
        if customer_ids is None:
            # Get all customers
            customers = await self.customer_repo.get_all(limit=10000)
            customer_ids = [c.id for c in customers]
        
        predictions = []
        for cid in customer_ids:
            try:
                pred = await self.predict_churn(ChurnPredictionRequest(customer_id=cid))
                predictions.append(pred)
            except Exception as e:
                logger.error("batch_churn_error", customer_id=str(cid), error=str(e))
        
        return predictions
    
    async def get_at_risk_customers(self, threshold: float = 0.6, limit: int = 100) -> List[Dict]:
        
        customers = await self.customer_repo.get_all(limit=limit)
        at_risk = []
        
        for customer in customers:
            features = self._extract_churn_features(customer.id)
            prob = self._calculate_churn_probability(features)
            
            if prob >= threshold:
                at_risk.append({
                    "customer_id": customer.id,
                    "full_name": customer.full_name,
                    "phone": customer.phone,
                    "probability_of_churn": prob,
                    "risk_level": self._get_risk_level(prob),
                    "days_since_last_loan": features.get("days_since_last_loan"),
                    "days_since_last_login": features.get("days_since_last_login"),
                    "total_loan_value": features.get("total_loan_value"),
                    "last_prediction_date": datetime.now(timezone.utc),
                })
        
        # Sort by probability descending
        at_risk.sort(key=lambda x: x["probability_of_churn"], reverse=True)
        return at_risk[:limit]
    
    # TODO: Add real-time churn scoring from event streams
    # TODO: Add churn intervention automation
    # TODO: Add churn feedback loop tracking