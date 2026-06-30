from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import verify_token
from app.database import get_async_db
from app.models.user import User, UserRole
from app.repositories.customer_repository import CustomerRepository
from app.repositories.loan_repository import LoanRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenData
from app.services.auth_service import AuthService
from app.services.churn_service import ChurnService
from app.services.credit_service import CreditService
from app.services.customer_service import CustomerService
from app.services.feature_engineering import FeatureEngineeringService
from app.services.loan_service import LoanService
from app.services.retention_service import RetentionService
from app.services.segmentation_service import SegmentationService
from app.services.statement_service import StatementService

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Repository Dependencies
async def get_user_repository(db: AsyncSession = Depends(get_async_db)) -> UserRepository:
    return UserRepository(db)


async def get_customer_repository(db: AsyncSession = Depends(get_async_db)) -> CustomerRepository:
    return CustomerRepository(db)


async def get_loan_repository(db: AsyncSession = Depends(get_async_db)) -> LoanRepository:
    return LoanRepository(db)


async def get_transaction_repository(db: AsyncSession = Depends(get_async_db)) -> TransactionRepository:
    return TransactionRepository(db)


async def get_prediction_repository(db: AsyncSession = Depends(get_async_db)) -> PredictionRepository:
    return PredictionRepository(db)

# Service Dependencies
async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repo)


async def get_customer_service(
    customer_repo: CustomerRepository = Depends(get_customer_repository),
) -> CustomerService:
    return CustomerService(customer_repo)


async def get_loan_service(
    loan_repo: LoanRepository = Depends(get_loan_repository),
    customer_repo: CustomerRepository = Depends(get_customer_repository),
) -> LoanService:
    return LoanService(loan_repo, customer_repo)


async def get_credit_service(
    customer_repo: CustomerRepository = Depends(get_customer_repository),
    loan_repo: LoanRepository = Depends(get_loan_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
) -> CreditService:
    return CreditService(customer_repo, loan_repo, transaction_repo)


async def get_churn_service(
    customer_repo: CustomerRepository = Depends(get_customer_repository),
    loan_repo: LoanRepository = Depends(get_loan_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
) -> ChurnService:
    return ChurnService(customer_repo, loan_repo, transaction_repo)


async def get_statement_service() -> StatementService:
    return StatementService()


async def get_feature_engineering_service() -> FeatureEngineeringService:
    return FeatureEngineeringService()


async def get_segmentation_service(
    customer_repo: CustomerRepository = Depends(get_customer_repository),
) -> SegmentationService:
    return SegmentationService(customer_repo)


async def get_retention_service(
    churn_service: ChurnService = Depends(get_churn_service),
    segmentation_service: SegmentationService = Depends(get_segmentation_service),
) -> RetentionService:
    return RetentionService(churn_service, segmentation_service)

# Authentication Dependencies
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, role=payload.get("role"))
    except JWTError:
        raise credentials_exception
    
    user = await auth_service.get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_data_scientist(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role not in [UserRole.ADMIN, UserRole.DATA_SCIENTIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data scientist access required",
        )
    return current_user


# TODO: Add caching layer for frequently accessed dependencies
# TODO: Add request-scoped dependency container
# TODO: Add dependency health checks
# TODO: Add distributed tracing context propagation

# Future Enhancements:
    # - Add caching decorators for expensive dependencies
    # - Add circuit breaker patterns for external services
    # - Add request context propagation for distributed tracing


