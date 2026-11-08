"""
Authentication API Endpoints for TrustGuard AI.
Handles user registration, login, session refresh, logout, password recovery,
and authenticated identity retrieval.
"""

from __future__ import annotations

import logging

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.auth import (
    AuthMessageResponse,
    AuthTokenResponse,
    AuthUserResponse,
    ForgotPasswordRequest,
    OAuthCallbackRequest,
    OAuthUrlResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenRefreshRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.services.auth_service import AuthService

logger = logging.getLogger("trustguard.api.auth")
router = APIRouter()


def get_auth_service() -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService()


@router.get(
    "/status",
    summary="Auth Service Status",
    description="Check authentication service status and Supabase provider integration.",
)
async def auth_status():
    return {
        "message": "Authentication service online. Supabase Auth and JWT verification active.",
        "status": "ready",
    }


@router.post(
    "/register",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Registers a new user through Supabase Auth and initialises their public profile record.",
)
async def register(
    reg_in: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    logger.info("Register attempt for email: %s", reg_in.email)
    return await auth_service.register_user(reg_in)


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticates with email and password via Supabase Auth and returns JWT session tokens.",
)
async def login(
    login_in: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    logger.info("Login attempt for email: %s", login_in.email)
    return await auth_service.login_user(login_in)


@router.post(
    "/logout",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Terminates the user's active session.",
)
async def logout(
    current_user: AuthenticatedUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthMessageResponse:
    logger.info("User %s logging out", current_user.user_id)
    return await auth_service.logout_user(access_token=current_user.token)


@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Session Token",
    description="Exchanges a valid Supabase refresh token for a newly signed access token.",
)
async def refresh_token(
    refresh_in: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    return await auth_service.refresh_session(refresh_in)


@router.post(
    "/forgot-password",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Password Reset",
    description="Initiates password recovery instructions to the provided email without exposing user existence.",
)
async def forgot_password(
    forgot_in: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthMessageResponse:
    return await auth_service.forgot_password(forgot_in)


@router.post(
    "/reset-password",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset Password",
    description="Sets a new password for the authenticated recovery session.",
)
async def reset_password(
    reset_in: ResetPasswordRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthMessageResponse:
    return await auth_service.reset_password(reset_in, access_token=current_user.token or "")


@router.post(
    "/resend-verification",
    response_model=AuthMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend Verification Email",
    description="Resends the account confirmation email for an unverified account.",
)
async def resend_verification(
    req: ResendVerificationRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthMessageResponse:
    logger.info("Resend verification requested for: %s", req.email)
    return await auth_service.resend_verification_email(req.email)


@router.get(
    "/oauth/google",
    response_model=OAuthUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate Google OAuth",
    description="Returns the Supabase Google OAuth authorization redirection URL.",
)
async def initiate_google_oauth(
    redirect_to: Optional[str] = Query(
        default=None,
        description="Permitted frontend redirect URI (defaults to /auth/callback)",
    ),
    auth_service: AuthService = Depends(get_auth_service),
) -> OAuthUrlResponse:
    auth_url = await auth_service.get_google_oauth_url(redirect_to=redirect_to)
    return OAuthUrlResponse(url=auth_url, provider="google")


@router.post(
    "/oauth/callback",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete OAuth Authentication",
    description="Finalises Google OAuth flow using authorization code or tokens.",
)
async def oauth_callback(
    callback_in: OAuthCallbackRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    return await auth_service.handle_oauth_callback(
        code=callback_in.code,
        access_token=callback_in.access_token,
        refresh_token=callback_in.refresh_token,
    )


@router.get(
    "/me",
    response_model=AuthUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated Identity",
    description="Returns the currently authenticated user's Auth identity and metadata.",
)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthUserResponse:
    # Fetch additional profile details if available
    profile = await auth_service._user_repo.get_user_profile(current_user.user_id)
    return AuthUserResponse(
        id=current_user.user_id,
        email=current_user.email or (profile.email if profile else "user@trustguard.ai"),
        full_name=profile.full_name if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        role=current_user.role,
    )
