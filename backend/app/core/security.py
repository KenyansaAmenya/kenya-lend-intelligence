# My Security Module.
# To Handle authentication, authorization, password hashing, and JWT token management.

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)  

# JWT token management
def create_access_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else: 
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )    

    to_encode = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }    

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return encoded_jwt

def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try: 
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )    
        return payload
    except jwt.JWTError:
        return None

#Role-Based Access Control (RBAC)
def has_role(user_role: str, required_role: str) -> bool:
    role_hierarchy = {
        "USER": 1,
        "ANALYST": 2,
        "LOAN_OFFICER": 3,
        "DATA_SCIENTIST": 4,
        "ADMIN": 5,
    }

    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)

    return user_level >= required_level

# TODO: Add API key generation and validation for service-to-service auth
# TODO: Add OAuth2/OIDC integration for enterprise SSO
# TODO: Add rate limiting per user/role
# TODO: Add token blacklisting for logout
# TODO: Integrate with HashiCorp Vault for secret rotation    


# Future Enhancements:
    # - Integrate with HashiCorp Vault for secrets management
    # - Add OAuth2/OIDC support for SSO
    # - Implement API key authentication for service-to-service calls
    # - Add hardware security module (HSM) integration
