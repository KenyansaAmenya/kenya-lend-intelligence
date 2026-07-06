# This is my Loan Service.
# It Handles loan applications, decisions, and lifecycle management.

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from app.core.audit import AuditEventType, AuditLogger
from app.core.exceptions import BusinessRuleError, ResourceNotFoundError, ValidationError
from app.core.logging_config import get_logger
from app.models.loan import Loan, LoanStatus
from app.repositories.customer_repository import CustomerRepository
from app.repositories.loan_repository import LoanRepository
from app.schemas.loan import LoanCreate, LoanDecisionRequest, LoanDecisionResponse, LoanUpdate

logger = get_logger(__name__)

class LoanService:
    def __init__(
        self,
        loan_repository: LoanRepository,
        customer_repository: CustomerRepository,
    ):
        self.loan_repo = loan_repository
        self.customer_repo = customer_repository
        self.audit = AuditLogger()
    
    async def apply_for_loan(self, loan_data: LoanCreate) -> Loan:
        # Verify customer exists
        customer = await self.customer_repo.get_by_id(loan_data.customer_id)
        if not customer:
            raise ResourceNotFoundError("Customer")
        
        # Check for existing active loans
        existing_loans = await self.loan_repo.get_by_customer(loan_data.customer_id)
        active_loans = [l for l in existing_loans if l.status in [LoanStatus.ACTIVE.value, LoanStatus.DISBURSED.value, LoanStatus.APPROVED.value]]
        
        if len(active_loans) >= 3:  # Max 3 active loans
            raise BusinessRuleError("Maximum active loans reached (3)")
        
        loan_dict = {
            "customer_id": loan_data.customer_id,
            "amount": loan_data.amount,
            "interest_rate": loan_data.interest_rate,
            "status": LoanStatus.PENDING.value,
        }
        
        loan = await self.loan_repo.create(loan_dict)
        
        logger.info("loan_application_submitted", loan_id=str(loan.id), customer_id=str(loan_data.customer_id))
        
        await self.audit.log_event(
            event_type=AuditEventType.LOAN_APPLICATION_SUBMITTED,
            resource_type="loan",
            resource_id=str(loan.id),
            details={
                "amount": loan_data.amount,
                "customer_id": str(loan_data.customer_id),
            },
        )
        
        return loan
    
    async def get_loan(self, loan_id: UUID) -> Loan:
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise ResourceNotFoundError("Loan")
        return loan
    
    async def update_loan(self, loan_id: UUID, update_data: LoanUpdate) -> Loan:
        loan = await self.get_loan(loan_id)
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        updated = await self.loan_repo.update(loan, update_dict)
        
        logger.info("loan_updated", loan_id=str(loan_id), status=updated.status)
        return updated
    
    async def approve_loan(self, loan_id: UUID, approved_amount: Optional[float] = None) -> Loan:
        loan = await self.get_loan(loan_id)
        
        if loan.status != LoanStatus.PENDING.value:
            raise BusinessRuleError(f"Cannot approve loan with status: {loan.status}")
        
        update_dict = {
            "status": LoanStatus.APPROVED.value,
            "approved_amount": approved_amount or loan.amount,
            "approved_at": datetime.now(timezone.utc),
        }
        
        updated = await self.loan_repo.update(loan, update_dict)
        
        logger.info("loan_approved", loan_id=str(loan_id), approved_amount=update_dict["approved_amount"])
        
        await self.audit.log_event(
            event_type=AuditEventType.LOAN_APPROVED,
            resource_type="loan",
            resource_id=str(loan_id),
            details={"approved_amount": update_dict["approved_amount"]},
        )
        
        return updated
    
    async def reject_loan(self, loan_id: UUID, reason: Optional[str] = None) -> Loan:
        loan = await self.get_loan(loan_id)
        
        if loan.status != LoanStatus.PENDING.value:
            raise BusinessRuleError(f"Cannot reject loan with status: {loan.status}")
        
        updated = await self.loan_repo.update(loan, {"status": LoanStatus.REJECTED.value})
        
        logger.info("loan_rejected", loan_id=str(loan_id), reason=reason)
        
        await self.audit.log_event(
            event_type=AuditEventType.LOAN_REJECTED,
            resource_type="loan",
            resource_id=str(loan_id),
            details={"reason": reason},
        )
        
        return updated
    
    async def get_customer_loans(self, customer_id: UUID) -> List[Loan]:
        return await self.loan_repo.get_by_customer(customer_id)
    
    async def get_portfolio_summary(self) -> dict:
        return await self.loan_repo.get_portfolio_metrics()
    
    # TODO: Add automated disbursement via M-Pesa
    # TODO: Add repayment schedule generation
    # TODO: Add collection queue management
    # TODO: Add loan restructuring logic