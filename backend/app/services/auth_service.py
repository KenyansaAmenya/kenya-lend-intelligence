# This is my Authentication Service.
# It will Handle user registration, login, token management and password security.

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from app.core.audit import AuditEventType, AuditLogger
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.logging_config import get_logger
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token, UserCreate, UserLogin

logger = get_logger(__name__)

class AuthService:  
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository
        self.audit = AuditLogger()
    
    async def register(self, user_data: UserCreate) -> User:
        # Check if email exists
        existing = await self.user_repo.get_by_email(user_data.email)
        if existing:
            raise ValidationError("Email already registered")
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Create user
        user_dict = {
            "email": user_data.email,
            "password_hash": password_hash,
            "full_name": user_data.full_name,
            "role": user_data.role or UserRole.USER.value,
        }
        
        user = await self.user_repo.create(user_dict)
        
        logger.info("user_registered", user_id=str(user.id), email=user.email)
        
        await self.audit.log_event(
            event_type=AuditEventType.USER_CREATED,
            user_id=str(user.id),
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email, "role": user.role},
        )
        
        return user
    
    async def login(self, login_data: UserLogin) -> Token:
        user = await self.user_repo.get_by_email(login_data.email)
        
        if not user or not verify_password(login_data.password, user.password_hash):
            await self.audit.log_event(
                event_type=AuditEventType.LOGIN_FAILED,
                resource_type="user",
                details={"email": login_data.email, "reason": "invalid_credentials"},
            )
            raise AuthenticationError("Invalid email or password")
        
        if not user.is_active:
            await self.audit.log_event(
                event_type=AuditEventType.LOGIN_FAILED,
                user_id=str(user.id),
                resource_type="user",
                details={"reason": "inactive_account"},
            )
            raise AuthenticationError("Account is inactive")
        
        # Generate tokens
        access_token = create_access_token(str(user.id), user.role)
        refresh_token = create_refresh_token(str(user.id))
        
        logger.info("user_login", user_id=str(user.id), email=user.email)
        
        await self.audit.log_event(
            event_type=AuditEventType.LOGIN,
            user_id=str(user.id),
            resource_type="user",
            resource_id=str(user.id),
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=30 * 60,  # 30 minutes
        )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            uuid_obj = UUID(user_id)
            return await self.user_repo.get_by_id(uuid_obj)
        except ValueError:
            return None
    
    async def refresh_token(self, refresh_token: str) -> Token:
        from jose import jwt
        from app.config import settings
        
        try:
            payload = jwt.decode(
                refresh_token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid refresh token")
            
            user = await self.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")
            
            # Generate new tokens
            new_access = create_access_token(str(user.id), user.role)
            new_refresh = create_refresh_token(str(user.id))
            
            return Token(
                access_token=new_access,
                refresh_token=new_refresh,
                token_type="bearer",
                expires_in=30 * 60,
            )
        except Exception:
            raise AuthenticationError("Invalid refresh token")
    
    # TODO: Add password reset flow
    # TODO: Add email verification
    # TODO: Add session invalidation
    # TODO: Add brute force protection (rate limiting per IP)