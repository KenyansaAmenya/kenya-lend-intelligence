# Credit API Router.
# This will Handle credit scoring, risk assessment, and score trends.

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.exceptions import ResourceNotFoundError, handle_app_exception
from app.dependencies import get_credit_service, get_current_active_user
from app.models.user import User
from app.schemas.credit import (
    CreditScoreDistribution,
    CreditScoreRequest,
    CreditScoreResponse,
    CreditScoreTrend,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
)
from app.services.credit_service import CreditService

router = APIRouter(prefix="/credit", tags=["Credit Scoring"])


@router.post("/score", response_model=CreditScoreResponse)
async def generate_credit_score(
    request: CreditScoreRequest,
    credit_service: CreditService = Depends(get_credit_service),
    current_user: User = Depends(get_current_active_user),
):

    try:
        return await credit_service.generate_credit_score(request)
    except ResourceNotFoundError as e:
        raise handle_app_exception(e)


@router.post("/assess", response_model=RiskAssessmentResponse)
async def assess_risk(
    request: RiskAssessmentRequest,
    credit_service: CreditService = Depends(get_credit_service),
    current_user: User = Depends(get_current_active_user),
):

    try:
        return await credit_service.assess_risk(request)
    except ResourceNotFoundError as e:
        raise handle_app_exception(e)


@router.get("/score/{customer_id}", response_model=CreditScoreResponse)
async def get_customer_credit_score(
    customer_id: UUID,
    credit_service: CreditService = Depends(get_credit_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await credit_service.generate_credit_score(
            CreditScoreRequest(customer_id=customer_id)
        )
    except ResourceNotFoundError as e:
        raise handle_app_exception(e)


@router.get("/trends", response_model=List[CreditScoreTrend])
async def get_credit_score_trends(
    months: int = 6,
    credit_service: CreditService = Depends(get_credit_service),
    current_user: User = Depends(get_current_active_user),
):

    # TODO: Implement from historical prediction data
    from datetime import datetime, timedelta
    
    trends = []
    for i in range(months):
        month_date = datetime.utcnow() - timedelta(days=30 * i)
        trends.append(CreditScoreTrend(
            month=month_date.strftime("%Y-%m"),
            average_score=620 + (i * 5),
            median_score=610 + (i * 3),
            score_distribution={
                "300-450": 10 - i,
                "450-550": 20 - i,
                "550-650": 35,
                "650-750": 25 + i,
                "750-850": 10 + i,
            },
        ))
    
    return trends


@router.get("/distribution", response_model=List[CreditScoreDistribution])
async def get_score_distribution(
    credit_service: CreditService = Depends(get_credit_service),
    current_user: User = Depends(get_current_active_user),
):

    # TODO: Calculate from actual data
    return [
        CreditScoreDistribution(score_range="300-450", count=50, percentage=5.0, average_default_rate=0.35),
        CreditScoreDistribution(score_range="450-550", count=150, percentage=15.0, average_default_rate=0.25),
        CreditScoreDistribution(score_range="550-650", count=300, percentage=30.0, average_default_rate=0.15),
        CreditScoreDistribution(score_range="650-750", count=350, percentage=35.0, average_default_rate=0.08),
        CreditScoreDistribution(score_range="750-850", count=150, percentage=15.0, average_default_rate=0.03),
    ]


# TODO: Add credit bureau integration endpoint
# TODO: Add score dispute endpoint
# TODO: Add alternative data scoring endpoint