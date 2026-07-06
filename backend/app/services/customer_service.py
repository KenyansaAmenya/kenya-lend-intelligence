# This is my Customer Service. It Handles customer management, search, and health scoring.

from typing import List, Optional
from uuid import UUID

from app.core.audit import AuditEventType, AuditLogger
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.logging_config import get_logger
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate

logger = get_logger(__name__)

class CustomerService:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repo = customer_repository
        self.audit = AuditLogger()
    
    async def create_customer(self, customer_data: CustomerCreate) -> Customer:
        # Check for existing phone
        existing_phone = await self.customer_repo.get_by_phone(customer_data.phone)
        if existing_phone:
            raise ValidationError("Phone number already registered")
        
        # Check for existing national ID
        existing_id = await self.customer_repo.get_by_national_id(customer_data.national_id)
        if existing_id:
            raise ValidationError("National ID already registered")
        
        customer_dict = customer_data.model_dump()
        customer = await self.customer_repo.create(customer_dict)
        
        logger.info("customer_created", customer_id=str(customer.id), phone=customer.phone)
        
        await self.audit.log_event(
            event_type=AuditEventType.CUSTOMER_CREATED,
            resource_type="customer",
            resource_id=str(customer.id),
            details={"phone": customer.phone, "national_id": customer.national_id},
        )
        
        return customer
    
    async def get_customer(self, customer_id: UUID) -> Customer:
        customer = await self.customer_repo.get_by_id(customer_id)
        if not customer:
            raise ResourceNotFoundError("Customer")
        return customer
    
    async def update_customer(self, customer_id: UUID, update_data: CustomerUpdate) -> Customer:
        customer = await self.get_customer(customer_id)
        
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        updated = await self.customer_repo.update(customer, update_dict)
        
        logger.info("customer_updated", customer_id=str(customer_id))
        
        await self.audit.log_event(
            event_type=AuditEventType.CUSTOMER_UPDATED,
            resource_type="customer",
            resource_id=str(customer_id),
            details=update_dict,
        )
        
        return updated
    
    async def search_customers(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        employment_status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Customer]:
        return await self.customer_repo.search_customers(
            query=query,
            location=location,
            employment_status=employment_status,
            skip=skip,
            limit=limit,
        )
    
    async def calculate_health_score(self, customer_id: UUID) -> dict:   
        return {
            "customer_id": customer_id,
            "health_score": 75.0,  # Placeholder
            "score_components": {
                "repayment_history": 80.0,
                "engagement_level": 70.0,
                "financial_stability": 75.0,
            },
            "assessment_date": __import__('datetime').datetime.utcnow().isoformat(),
        }
    
    # TODO: Add KYC verification workflow
    # TODO: Add customer risk profiling
    # TODO: Add customer lifetime value calculation