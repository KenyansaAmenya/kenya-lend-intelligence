# Customer Segmentation Service.
# Segments customers into actionable groups for targeted
# marketing and retention strategies.

from typing import Dict, List, Optional
from uuid import UUID

from app.config import settings
from app.core.logging_config import get_logger
from app.repositories.customer_repository import CustomerRepository

logger = get_logger(__name__)

class SegmentationService:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repo = customer_repository
    
    def segment_customer(
        self,
        churn_probability: float,
        customer_value: float,
        engagement_score: float,
        days_since_last_loan: int,
    ) -> str:

        # High churn risk
        if churn_probability >= 0.7:
            if customer_value >= 0.7:
                return "AT_RISK"  # High value but likely to churn
            return "LIKELY_CHURNER"
        
        # Dormant customers
        if days_since_last_loan > 90 and engagement_score < 30:
            return "DORMANT"
        
        # High value loyal customers
        if customer_value >= 0.7 and churn_probability < 0.3:
            return "HIGH_VALUE"
        
        # Loyal customers
        if churn_probability < 0.3 and engagement_score >= 60:
            return "LOYAL"
        
        # New or low-engagement customers
        if engagement_score < 40:
            return "LOW_ENGAGEMENT"
        
        # Default
        return "STANDARD"
    
    async def segment_all_customers(
        self,
        churn_predictions: List[Dict],
    ) -> List[Dict]:

        segments = []
        
        for pred in churn_predictions:
            segment = self.segment_customer(
                churn_probability=pred.get("probability_of_churn", 0),
                customer_value=pred.get("customer_value_score", 0.5),
                engagement_score=pred.get("engagement_score", 50),
                days_since_last_loan=pred.get("days_since_last_loan", 30),
            )
            
            segments.append({
                "customer_id": pred["customer_id"],
                "segment": segment,
                "churn_probability": pred.get("probability_of_churn"),
                "customer_value": pred.get("customer_value_score"),
            })
        
        return segments
    
    async def get_segment_distribution(self) -> List[Dict]:
        
        return [
            {"segment": "LOYAL", "count": 450, "percentage": 45.0, "avg_churn_prob": 0.15},
            {"segment": "AT_RISK", "count": 120, "percentage": 12.0, "avg_churn_prob": 0.75},
            {"segment": "LIKELY_CHURNER", "count": 80, "percentage": 8.0, "avg_churn_prob": 0.85},
            {"segment": "DORMANT", "count": 150, "percentage": 15.0, "avg_churn_prob": 0.60},
            {"segment": "HIGH_VALUE", "count": 100, "percentage": 10.0, "avg_churn_prob": 0.20},
            {"segment": "LOW_ENGAGEMENT", "count": 60, "percentage": 6.0, "avg_churn_prob": 0.45},
            {"segment": "STANDARD", "count": 40, "percentage": 4.0, "avg_churn_prob": 0.35},
        ]
    
    # TODO: Add ML-based clustering algorithms
    # TODO: Add segment migration tracking
    # TODO: Add segment-based offer optimization