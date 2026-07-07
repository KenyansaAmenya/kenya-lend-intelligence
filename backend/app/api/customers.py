# Customer API Router.
# It handles customer CRUD operations, search, and health scoring.

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.exceptions import ResourceNotFoundError, ValidationError, handle_app_exception
from app.dependencies import get_current_active_user, get_customer_service
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerHealthScore,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: User = Depends(get_current_active_user),
):

    try:
        customer = await customer_service.create_customer(customer_data)
        return customer
    except ValidationError as e:
        raise handle_app_exception(e)

@router.get("", response_model=CustomerListResponse)
async def list_customers(
    query: Optional[str] = Query(None, description="Search by name, phone, or ID"),
    location: Optional[str] = Query(None, description="Filter by location/county"),
    employment_status: Optional[str] = Query(None, description="Filter by employment status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: User = Depends(get_current_active_user),
):

    customers = await customer_service.search_customers(
        query=query,
        location=location,
        employment_status=employment_status,
        skip=skip,
        limit=limit,
    )
    
    return CustomerListResponse(
        items=customers,
        total=len(customers),
        page=skip // limit + 1,
        page_size=limit,
        pages=1,
    )

@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer(
    customer_id: UUID,
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        customer = await customer_service.get_customer(customer_id)
        return customer
    except ResourceNotFoundError as e:
        raise handle_app_exception(e)

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    update_data: CustomerUpdate,
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: User = Depends(get_current_active_user),
):

    try:
        return await customer_service.update_customer(customer_id, update_data)
    except ResourceNotFoundError as e:
        raise handle_app_exception(e)

@router.get("/{customer_id}/health", response_model=CustomerHealthScore)
async def get_customer_health(
    customer_id: UUID,
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: User = Depends(get_current_active_user),
):

    try:
        return await customer_service.calculate_health_score(customer_id)
    except ResourceNotFoundError as e:
        raise handle_app_exception(e)


# TODO: Add bulk import endpoint
# TODO: Add customer merge endpoint
# TODO: Add KYC document upload endpoint
# TODO: Add customer export endpoint