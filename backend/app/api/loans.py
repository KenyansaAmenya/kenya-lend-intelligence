# Loan API Router.
# It will Handle loan applications, decisions, and lifecycle management.

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.exceptions import BusinessRuleError, ResourceNotFoundError, handle_app_exception
from app.dependencies import get_credit_service, get_current_active_user, get_loan_service
from app.models.user import User
from app.schemas.loan import (
    LoanApprovalTrend,
    LoanCreate,
    LoanDecisionRequest,
    LoanDecisionResponse,
    LoanListResponse,
    LoanResponse,
    LoanUpdate,
)
from app.services.credit_service import CreditService
from app.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["Loans"])

@router.post("/apply", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_loan(
    loan_data: LoanCreate,
    loan_service: LoanService = Depends(get_loan_service),
    current_user: User = Depends(get_current_active_user),
):

    try:
        return await loan_service.apply_for_loan(loan_data)
    except (ResourceNotFoundError, BusinessRuleError) as e:
        raise handle_app_exception(e)


@router.get("", response_model=LoanListResponse)
async def list_loans(
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    loan_service: LoanService = Depends(get_loan_service),
    current_user: User = Depends(get_current_active_user),
):
    """List loans with filtering."""
    # TODO: Implement filtering
    loans = []
    return LoanListResponse(
        items=loans,
        total=0,
        page=1,
        page_size=limit,
        pages=0,
    )


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: UUID,
    loan_service: LoanService = Depends(get_loan_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await loan_service.get_loan(loan_id)
    except ResourceNotFoundError as e:
        raise handle_app_exception(e)


@router.post("/{loan_id}/approve", response_model=LoanResponse)
async def approve_loan(
    loan_id: UUID,
    approved_amount: Optional[float] = None,
    loan_service: LoanService = Depends(get_loan_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await loan_service.approve_loan(loan_id, approved_amount)
    except (ResourceNotFoundError, BusinessRuleError) as e:
        raise handle_app_exception(e)

@router.post("/{loan_id}/reject", response_model=LoanResponse)
async def reject_loan(
    loan_id: UUID,
    reason: Optional[str] = None,
    loan_service: LoanService = Depends(get_loan_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await loan_service.reject_loan(loan_id, reason)
    except (ResourceNotFoundError, BusinessRuleError) as e:
        raise handle_app_exception(e)


@router.post("/decision/mpesa", response_model=LoanDecisionResponse)
async def loan_decision_mpesa(
    request: LoanDecisionRequest,
    credit_service: CreditService = Depends(get_credit_service),
    current_user: User = Depends(get_current_active_user),
):
    # TODO: Integrate with statement analysis
    from app.schemas.credit import CreditScoreRequest
    from app.schemas.loan import LoanDecisionResponse
    
    credit_result = await credit_service.generate_credit_score(
        CreditScoreRequest(customer_id=request.customer_id)
    )
    
    risk = await credit_service.assess_risk(
        type('obj', (object,), {
            'customer_id': request.customer_id,
            'requested_amount': request.amount,
        })()
    )
    
    # Decision logic
    if risk.probability_of_default > 0.4:
        decision = "REJECTED"
    elif risk.probability_of_default > 0.25:
        decision = "MANUAL_REVIEW"
    else:
        decision = "APPROVED"
    
    return LoanDecisionResponse(
        customer_id=request.customer_id,
        decision=decision,
        approved_amount=risk.recommended_amount if decision == "APPROVED" else None,
        interest_rate=risk.recommended_rate if decision == "APPROVED" else None,
        probability_of_default=risk.probability_of_default,
        credit_score=credit_result.credit_score,
        risk_level=credit_result.risk_level,
        affordability_assessment={
            "monthly_income": risk.max_affordable_payment + risk.debt_to_income_ratio * risk.max_affordable_payment,
            "existing_obligations": risk.debt_to_income_ratio * risk.max_affordable_payment,
            "max_affordable_payment": risk.max_affordable_payment,
            "requested_amount": request.amount,
            "recommended_amount": risk.recommended_amount,
        },
        explanation={
            "credit_score_factors": credit_result.score_factors,
            "risk_assessment": f"Probability of default: {risk.probability_of_default:.2%}",
        },
    )


@router.post("/decision/bank", response_model=LoanDecisionResponse)
async def loan_decision_bank(
    request: LoanDecisionRequest,
    credit_service: CreditService = Depends(get_credit_service),
    current_user: User = Depends(get_current_active_user),
):
    # Same logic as M-Pesa but with bank statement analysis
    return await loan_decision_mpesa(request, credit_service, current_user)


@router.post("/decision/combined", response_model=LoanDecisionResponse)
async def loan_decision_combined(
    request: LoanDecisionRequest,
    credit_service: CreditService = Depends(get_credit_service),
    current_user: User = Depends(get_current_active_user),
):
    # TODO: Implement combined analysis
    return await loan_decision_mpesa(request, credit_service, current_user)


@router.get("/portfolio/summary")
async def get_portfolio_summary(
    loan_service: LoanService = Depends(get_loan_service),
    current_user: User = Depends(get_current_active_user),
):
    return await loan_service.get_portfolio_summary()


# TODO: Add repayment schedule endpoints
# TODO: Add collection workflow endpoints
# TODO: Add loan restructuring endpoints