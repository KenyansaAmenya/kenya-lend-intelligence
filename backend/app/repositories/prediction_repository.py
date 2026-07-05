# Data access layer for ChurnPrediction and related prediction entities.
# Handles prediction history and model performance tracking.

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import ChurnPrediction
from app.repositories.base_repository import BaseRepository


class PredictionRepository(BaseRepository[ChurnPrediction]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ChurnPrediction)
    
    async def get_by_customer(self, customer_id: UUID, limit: int = 10) -> List[ChurnPrediction]:
        result = await self.db.execute(
            select(ChurnPrediction)
            .where(ChurnPrediction.customer_id == customer_id)
            .order_by(desc(ChurnPrediction.prediction_date))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_latest_by_customer(self, customer_id: UUID) -> Optional[ChurnPrediction]:
        result = await self.db.execute(
            select(ChurnPrediction)
            .where(ChurnPrediction.customer_id == customer_id)
            .order_by(desc(ChurnPrediction.prediction_date))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_high_risk_predictions(
        self,
        threshold: float = 0.7,
        days: int = 7,
    ) -> List[ChurnPrediction]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.db.execute(
            select(ChurnPrediction)
            .where(
                and_(
                    ChurnPrediction.probability_of_churn >= threshold,
                    ChurnPrediction.prediction_date >= cutoff,
                )
            )
            .order_by(desc(ChurnPrediction.probability_of_churn))
        )
        return list(result.scalars().all())
    
    async def get_prediction_accuracy_stats(self, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                func.count(ChurnPrediction.id).label("total_predictions"),
                func.avg(ChurnPrediction.probability_of_churn).label("avg_probability"),
                func.count(
                    func.case((ChurnPrediction.probability_of_churn >= 0.7, 1))
                ).label("high_risk_count"),
                func.count(
                    func.case(
                        (
                            and_(
                                ChurnPrediction.probability_of_churn >= 0.4,
                                ChurnPrediction.probability_of_churn < 0.7,
                            ),
                            1,
                        )
                    )
                ).label("medium_risk_count"),
            )
            .where(ChurnPrediction.prediction_date >= cutoff)
        )
        row = result.one_or_none()
        return {
            "total_predictions": row.total_predictions or 0,
            "avg_probability": float(row.avg_probability or 0),
            "high_risk_count": row.high_risk_count or 0,
            "medium_risk_count": row.medium_risk_count or 0,
        } if row else {
            "total_predictions": 0,
            "avg_probability": 0.0,
            "high_risk_count": 0,
            "medium_risk_count": 0,
        }
    
    # Future Enhancements:
    # TODO: Add prediction feedback loop (actual vs predicted)
    # TODO: Add model performance degradation alerts
    # TODO: Add feature drift detection