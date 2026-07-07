# Authentication API Router.
# Handles user registration, login, token refresh, and password management.

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.exceptions import AuthenticationError, ValidationError, handle_app_exception
from app.dependencies import get_auth_service, get_current_active_user, get_current_user
from app.models.user import User
from app.schemas.auth import Token, TokenRefresh, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):

    try:
        user = await auth_service.register(user_data)
        return user
    except ValidationError as e:
        raise handle_app_exception(e)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    # Authenticate user and obtain JWT tokens.
  
    try:
        login_data = UserLogin(email=form_data.username, password=form_data.password)
        return await auth_service.login(login_data)
    except AuthenticationError as e:
        raise handle_app_exception(e)

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: TokenRefresh,
    auth_service: AuthService = Depends(get_auth_service),
):
    # Refresh access token using valid refresh token.

    try:
        return await auth_service.refresh_token(refresh_data.refresh_token)
    except AuthenticationError as e:
        raise handle_app_exception(e)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    # Get current authenticated user information.
    return current_user

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    # Logout current user.
    # TODO: Add token to blacklist (Redis)
    return {"message": "Successfully logged out"}


# TODO: Add /forgot-password endpoint
# TODO: Add /reset-password endpoint
# TODO: Add /verify-email endpoint
# TODO: Add /mfa/setup and /mfa/verify endpoints