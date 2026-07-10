# Statement API Router.

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_current_active_user, get_statement_service
from app.models.user import User
from app.schemas.statement import (
    StatementAnalysisRequest,
    StatementAnalysisResponse,
    StatementUploadResponse,
)
from app.services.statement_service import StatementService

router = APIRouter(prefix="/statements", tags=["Statement Processing"])


@router.post("/mpesa/upload", response_model=StatementUploadResponse)
async def upload_mpesa_statement(
    customer_id: UUID,
    file: UploadFile = File(...),
    statement_service: StatementService = Depends(get_statement_service),
    current_user: User = Depends(get_current_active_user),
):
    return await statement_service.process_upload(file, customer_id, "mpesa")


@router.post("/bank/upload", response_model=StatementUploadResponse)
async def upload_bank_statement(
    customer_id: UUID,
    file: UploadFile = File(...),
    statement_service: StatementService = Depends(get_statement_service),
    current_user: User = Depends(get_current_active_user),
):
    return await statement_service.process_upload(file, customer_id, "bank")


@router.post("/analyze", response_model=StatementAnalysisResponse)
async def analyze_statement(
    request: StatementAnalysisRequest,
    statement_service: StatementService = Depends(get_statement_service),
    current_user: User = Depends(get_current_active_user),
):
    return await statement_service.analyze_statement(
        request.customer_id, request.statement_type
    )

# Future enhancements
# TODO: Add statement verification endpoint
# TODO: Add fraud detection endpoint
# TODO: Add statement comparison endpoint