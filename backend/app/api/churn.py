# Churn API Router.
# This will Handle churn predictions, at-risk customer queries, and customer segmentation.

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.exceptions import ResourceNotFoundError, handle_app_exception
from app.dependencies import get_churn_service, get_current_active_user, get_segmentation_service
from app.models.user import User
from app.schemas.churn import (
    AtRiskListResponse,
    ChurnPredictionBatchResponse,
    ChurnPredictionRequest,
    ChurnPredictionResponse,
    ChurnTrend,
    CustomerSegment,
    SegmentDistribution,
)
from app.services.churn_service import ChurnService
from app.services.segmentation_service import SegmentationService

router = APIRouter(prefix="/churn", tags=["Churn Prediction"])


@router.post("/predict", response_model=ChurnPredictionResponse)
async def predict_churn(
    request: ChurnPredictionRequest,
    churn_service: ChurnService = Depends(get_churn_service),
    current_user: User = Depends(get_current_active_user),
):

    try:
        if not request.customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="customer_id is required for single prediction",
            )
        return await churn_service.predict_churn(request)
    except ResourceNotFoundError as e:
        raise handle_app_exception(e)


@router.post("/predict/batch", response_model=ChurnPredictionBatchResponse)
async def predict_churn_batch(
    customer_ids: Optional[List[UUID]] = None,
    churn_service: ChurnService = Depends(get_churn_service),
    current_user: User = Depends(get_current_active_user),
):

    predictions = await churn_service.predict_churn_batch(customer_ids)
    
    high_risk = sum(1 for p in predictions if p.probability_of_churn >= 0.7)
    medium_risk = sum(1 for p in predictions if 0.4 <= p.probability_of_churn < 0.7)
    low_risk = len(predictions) - high_risk - medium_risk
    
    return ChurnPredictionBatchResponse(
        predictions=predictions[:100],  # Limit response size
        total_processed=len(predictions),
        high_risk_count=high_risk,
        medium_risk_count=medium_risk,
        low_risk_count=low_risk,
    )


@router.get("/{customer_id}", response_model=ChurnPredictionResponse)
async def get_customer_churn(
    customer_id: UUID,
    churn_service: ChurnService = Depends(get_churn_service),
    current_user: User = Depends(get_current_active_user),
):

    try:
        return await churn_service.predict_churn(
            ChurnPredictionRequest(customer_id=customer_id)
        )
    except ResourceNotFoundError as e:
        raise handle_app_exception(e)


@router.get("/customers/at-risk", response_model=AtRiskListResponse)
async def get_at_risk_customers(
    threshold: float = Query(0.6, ge=0, le=1, description="Minimum churn probability"),
    limit: int = Query(100, ge=1, le=1000),
    churn_service: ChurnService = Depends(get_churn_service),
    current_user: User = Depends(get_current_active_user),
):

    at_risk = await churn_service.get_at_risk_customers(threshold=threshold, limit=limit)
    
    return AtRiskListResponse(
        items=at_risk,
        total=len(at_risk),
        page=1,
        page_size=limit,
    )


@router.get("/customers/segments", response_model=List[SegmentDistribution])
async def get_customer_segments(
    segmentation_service: SegmentationService = Depends(get_segmentation_service),
    current_user: User = Depends(get_current_active_user),
):

    segments = await segmentation_service.get_segment_distribution()
    return [SegmentDistribution(**s) for s in segments]


@router.get("/trends", response_model=List[ChurnTrend])
async def get_churn_trends(
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_active_user),
):
    # Placeholder trend data
    from datetime import datetime, timedelta
    
    trends = []
    for i in range(months):
        month_date = datetime.utcnow() - timedelta(days=30 * i)
        trends.append(ChurnTrend(
            month=month_date.strftime("%Y-%m"),
            churn_rate=0.15 + (i * 0.01),
            total_customers=1000 - (i * 50),
            churned_customers=150 - (i * 10),
            new_customers=100 - (i * 5),
        ))
    
    return trends


# TODO: Add real-time churn webhook endpoint
# TODO: Add churn intervention trigger endpoint
# TODO: Add churn cohort analysis endpoint