# Authentication Schemas.
# Request and response models for user authentication,
# registration, and token management.

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    # Base user schema.
    model_config = ConfigDict(from_attributes=True)
    
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name")


class UserCreate(UserBase):
    # Schema for user registration.
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 characters)",
    )
    role: Optional[str] = Field(default="USER", description="User role")
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        # Validate password contains required character types.
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    # user login schema .
    
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")

class UserResponse(UserBase):
    # Schema for user response.
    
    id: UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class Token(BaseModel):
    # JWT token response.
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None

class TokenRefresh(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token")

class PasswordChange(BaseModel):
    # password change scheme."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password",
    )
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        # Validate new password strength.
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# TODO: Add MFA schemas (TOTP setup, verification)
# TODO: Add password reset request/confirm schemas
# TODO: Add SSO callback schemas