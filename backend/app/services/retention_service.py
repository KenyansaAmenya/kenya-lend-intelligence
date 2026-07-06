# Retention Service.
# Generates personalized retention recommendations based on
# churn predictions and customer segments.

from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

from app.config import settings
from app.core.audit import AuditEventType, AuditLogger
from app.core.logging_config import get_logger
from app.schemas.churn import RetentionRecommendation, RetentionRecommendationBatch
from app.services.churn_service import ChurnService
from app.services.segmentation_service import SegmentationService

logger = get_logger(__name__)

class RetentionService:
    
    def __init__(
        self,
        churn_service: ChurnService,
        segmentation_service: SegmentationService,
    ):
        self.churn_service = churn_service
        self.segmentation_service = segmentation_service
        self.audit = AuditLogger()
    
    def generate_recommendation(
        self,
        customer_id: UUID,
        full_name: str,
        churn_probability: float,
        segment: str,
        churn_drivers: List[Dict],
        customer_value: float,
    ) -> RetentionRecommendation:
        # Generate personalized retention recommendation.
    
        # Determine priority
        if churn_probability >= 0.8:
            priority = "URGENT"
        elif churn_probability >= 0.6:
            priority = "HIGH"
        elif churn_probability >= 0.4:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        # Generate recommendation based on segment and drivers
        recommendation = self._get_recommendation_for_segment(
            segment, churn_drivers, customer_value, churn_probability
        )
        
        return RetentionRecommendation(
            customer_id=customer_id,
            full_name=full_name,
            probability_of_churn=churn_probability,
            segment=segment,
            recommended_action=recommendation["action"],
            action_priority=priority,
            expected_impact=recommendation["impact"],
            suggested_offer=recommendation.get("offer"),
        )
    
    def _get_recommendation_for_segment(
        self,
        segment: str,
        churn_drivers: List[Dict],
        customer_value: float,
        churn_probability: float,
    ) -> Dict:
        
        # Analyze top churn drivers
        driver_names = [d["factor"] for d in churn_drivers[:3]]
        
        if segment == "AT_RISK" and customer_value >= 0.7:
            return {
                "action": "Offer personalized rate reduction and exclusive product access",
                "impact": "High - valuable customer with clear retention opportunity",
                "offer": f"Reduce interest rate by 3% on next loan (current value: {customer_value:.2f})",
            }
        
        if segment == "LIKELY_CHURNER":
            if "Low Engagement Score" in driver_names:
                return {
                    "action": "Launch targeted re-engagement campaign with gamified app features",
                    "impact": "Medium - engagement-driven churn can be reversed with incentives",
                    "offer": "KES 500 airtime bonus for app login and profile update",
                }
            if "Missed Payments" in driver_names:
                return {
                    "action": "Offer loan restructuring and financial counseling",
                    "impact": "Medium - financial stress requires supportive intervention",
                    "offer": "Restructure existing loan with 30-day payment holiday",
                }
            return {
                "action": "Initiate personal outreach from relationship manager",
                "impact": "Medium - personal touch for high-risk customers",
                "offer": "Exclusive access to financial wellness program",
            }
        
        if segment == "DORMANT":
            return {
                "action": "Send promotional incentive campaign via SMS and push notification",
                "impact": "Medium - dormant customers respond to limited-time offers",
                "offer": "Zero-interest first week on next loan up to KES 10,000",
            }
        
        if segment == "LOW_ENGAGEMENT":
            return {
                "action": "Implement engagement boosting program with push notifications",
                "impact": "Low-Medium - gradual engagement improvement expected",
                "offer": "Loyalty points for daily app check-ins",
            }
        
        if "Days Since Last Loan" in driver_names:
            return {
                "action": "Send personalized loan offer with pre-approved limit",
                "impact": "Medium - address loan inactivity with relevant offer",
                "offer": "Pre-approved loan offer with 1-click application",
            }
        
        # Default recommendation
        return {
            "action": "Monitor and maintain regular communication",
            "impact": "Low - standard retention maintenance",
            "offer": None,
        }
    
    async def generate_batch_recommendations(
        self,
        at_risk_customers: List[Dict],
    ) -> RetentionRecommendationBatch:

        recommendations = []
        
        for customer in at_risk_customers:
            # Get churn prediction details
            try:
                churn_pred = await self.churn_service.predict_churn(
                    type('obj', (object,), {
                        'customer_id': customer["customer_id"],
                        'lookback_days': 90,
                    })()
                )
                
                # Determine segment
                segment = self.segmentation_service.segment_customer(
                    churn_probability=customer["probability_of_churn"],
                    customer_value=customer.get("customer_value_score", 0.5),
                    engagement_score=customer.get("engagement_score", 50),
                    days_since_last_loan=customer.get("days_since_last_loan", 30),
                )
                
                rec = self.generate_recommendation(
                    customer_id=customer["customer_id"],
                    full_name=customer["full_name"],
                    churn_probability=customer["probability_of_churn"],
                    segment=segment,
                    churn_drivers=churn_pred.churn_drivers,
                    customer_value=customer.get("customer_value_score", 0.5),
                )
                
                recommendations.append(rec)
            except Exception as e:
                logger.error(
                    "recommendation_generation_error",
                    customer_id=str(customer["customer_id"]),
                    error=str(e),
                )
                continue
        
        # Sort by priority
        priority_order = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.action_priority, 4))
        
        urgent_count = sum(1 for r in recommendations if r.action_priority == "URGENT")
        high_count = sum(1 for r in recommendations if r.action_priority == "HIGH")
        
        return RetentionRecommendationBatch(
            recommendations=recommendations,
            total=len(recommendations),
            urgent_count=urgent_count,
            high_priority_count=high_count,
        )
    
    # TODO: Add automated campaign execution via SMS/API
    # TODO: Add retention A/B testing framework
    # TODO: Add retention ROI calculation
    # TODO: Add multi-channel orchestration (SMS, push, email, call)