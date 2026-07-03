# User Model.
# Supports admin, data scientist, loan officer, analyst, and basic user roles.

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import sync_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserRole(str, PyEnum):
    USER = "USER"
    ANALYST = "ANALYST"
    LOAN_OFFICER = "LOAN_OFFICER"
    DATA_SCIENTIST = "DATA_SCIENTIST"
    ADMIN = "ADMIN"


class User(Base):
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # TODO: Add last_login_at field for session tracking
    # TODO: Add failed_login_attempts for brute force protection
    # TODO: Add mfa_enabled and mfa_secret for 2FA
    # TODO: Add password_changed_at for password expiry policy
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"
   
# Future Enhancements:
    # - Add multi-factor authentication fields
    # - Add password history for security
    # - Add session management
    # - Add SSO integration fields     