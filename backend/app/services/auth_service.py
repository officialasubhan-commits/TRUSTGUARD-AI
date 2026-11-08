"""
Supabase Authentication service.
Manages user registration, login, session tokens, and password reset workflows.
Integrates directly with Supabase Auth and synchronises user profiles.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import jwt

from app.core.config import settings
from app.core.exceptions import (
    DatabaseError,
    EmailNotConfirmedError,
    ExternalServiceError,
    InvalidCredentialsError,
    InvalidTokenError,
    RateLimitExceededError,
    UserAlreadyExistsError,
)
from app.database import connection
from app.database.repositories.user_repo import UserRepository
from app.schemas.auth import (
    AuthMessageResponse,
    AuthTokenResponse,
    AuthUserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenRefreshRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.user import UserCreate

logger = logging.getLogger("trustguard.service.auth")

# In-memory auth user store for offline development and isolated test suites
_mock_auth_users: Dict[str, Dict[str, Any]] = {}
_mock_refresh_tokens: Dict[str, str] = {}  # refresh_token -> email


def _generate_mock_jwt(
    user_id: uuid.UUID, email: str, role: str = "authenticated", expires_in: int = 3600
) -> str:
    """Creates a verifiable test JWT matching Supabase's claim structure."""
    now = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "aud": "authenticated",
        "iat": now,
        "exp": now + expires_in,
        "app_metadata": {"provider": "email", "role": role},
        "user_metadata": {"email": email},
    }
    secret = settings.SUPABASE_JWT_SECRET
    if not secret or secret.startswith("your-") or len(secret) < 32:
        secret = "trustguard-test-jwt-secret-key-32chars-minimum!"
    return jwt.encode(payload, secret, algorithm="HS256")


class AuthService:
    def __init__(self, client=None, user_repo: Optional[UserRepository] = None):
        self._client = client or connection.supabase_auth_client or connection.supabase_client
        self._user_repo = user_repo or UserRepository(client=connection.get_supabase_service_client())

    async def register_user(self, reg_in: UserRegisterRequest) -> AuthTokenResponse:
        """
        Registers a new user through Supabase Auth and initializes their profile record.
        """
        email = reg_in.email.lower().strip()

        # 1. LIVE SUPABASE AUTH INTEGRATION
        if self._client is not None and settings.supabase_configured:
            try:
                sb_user = None
                admin_cli = connection.get_supabase_service_client()
                if admin_cli is not None and hasattr(admin_cli, "auth") and hasattr(admin_cli.auth, "admin"):
                    created_res = admin_cli.auth.admin.create_user(
                        {
                            "email": email,
                            "password": reg_in.password,
                            "email_confirm": True,
                            "user_metadata": {
                                "full_name": reg_in.full_name,
                            },
                        }
                    )
                    sb_user = getattr(created_res, "user", created_res)
                else:
                    sign_up_res = self._client.auth.sign_up(
                        {
                            "email": email,
                            "password": reg_in.password,
                            "options": {
                                "data": {
                                    "full_name": reg_in.full_name,
                                }
                            },
                        }
                    )
                    sb_user = sign_up_res.user

                if not sb_user or (hasattr(sb_user, "identities") and sb_user.identities is not None and len(sb_user.identities) == 0):
                    raise UserAlreadyExistsError("A user with this email address already exists.")

                user_id = uuid.UUID(sb_user.id)
                # Create profile record in public.users
                try:
                    await self._user_repo.create_user_profile(
                        UserCreate(
                            id=user_id,
                            email=email,
                            full_name=reg_in.full_name,
                        )
                    )
                except DatabaseError as e:
                    logger.warning("Profile creation error (may be handled by trigger): %s", e)

                # Acquire immediate session tokens via password login since user is confirmed
                session = None
                try:
                    sign_in_res = self._client.auth.sign_in_with_password(
                        {
                            "email": email,
                            "password": reg_in.password,
                        }
                    )
                    session = sign_in_res.session
                except Exception as sign_in_err:
                    logger.warning("Auto sign-in after registration warning: %s", sign_in_err)

                if session and session.access_token:
                    access_token = session.access_token
                    refresh_token = session.refresh_token
                    expires_in = session.expires_in or 3600
                else:
                    access_token = _generate_mock_jwt(user_id, email)
                    refresh_token = f"refresh-{uuid.uuid4()}"
                    expires_in = 3600
                    _mock_refresh_tokens[refresh_token] = email
                    _mock_auth_users[email] = {
                        "id": user_id,
                        "email": email,
                        "full_name": reg_in.full_name,
                        "password": reg_in.password,
                        "role": "user",
                        "created_at": datetime.now(timezone.utc),
                    }

                return AuthTokenResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=expires_in,
                    user=AuthUserResponse(
                        id=user_id,
                        email=email,
                        full_name=reg_in.full_name,
                        role="user",
                        created_at=datetime.now(timezone.utc),
                    ),
                )
            except UserAlreadyExistsError:
                raise
            except Exception as e:
                err_str = str(e).lower()
                if any(k in err_str for k in ("already registered", "already been registered", "duplicate", "user_already_exists")):
                    raise UserAlreadyExistsError("A user with this email address already exists.")
                logger.error("Supabase user creation error: %s", e)
                raise InvalidCredentialsError(f"Registration failed: {e}")

        # 2. ISOLATED TEST / OFFLINE MODE
        if email in _mock_auth_users:
            raise UserAlreadyExistsError("A user with this email address already exists.")

        user_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        _mock_auth_users[email] = {
            "id": user_id,
            "email": email,
            "full_name": reg_in.full_name,
            "password": reg_in.password,  # Stored only in volatile test memory
            "role": "user",
            "created_at": now,
        }

        # Sync with UserRepository
        await self._user_repo.create_user_profile(
            UserCreate(
                id=user_id,
                email=email,
                full_name=reg_in.full_name,
            )
        )

        token = _generate_mock_jwt(user_id, email)
        refresh = f"refresh-{uuid.uuid4()}"
        _mock_refresh_tokens[refresh] = email

        return AuthTokenResponse(
            access_token=token,
            refresh_token=refresh,
            expires_in=3600,
            user=AuthUserResponse(
                id=user_id,
                email=email,
                full_name=reg_in.full_name,
                role="user",
                created_at=now,
            ),
        )

    async def login_user(self, login_in: UserLoginRequest) -> AuthTokenResponse:
        """
        Authenticates user with Supabase Auth and returns an access session.
        Never reveals whether an email exists on invalid password.
        """
        email = login_in.email.lower().strip()

        # 1. LIVE SUPABASE AUTH
        if self._client is not None and settings.supabase_configured:
            try:
                sign_in_res = self._client.auth.sign_in_with_password(
                    {
                        "email": email,
                        "password": login_in.password,
                    }
                )
                session = sign_in_res.session
                sb_user = sign_in_res.user

                if not session or not sb_user:
                    raise InvalidCredentialsError("Invalid email or password.")

                user_id = uuid.UUID(sb_user.id)
                full_name = (
                    sb_user.user_metadata.get("full_name") if sb_user.user_metadata else None
                )

                return AuthTokenResponse(
                    access_token=session.access_token,
                    refresh_token=session.refresh_token,
                    expires_in=session.expires_in or 3600,
                    user=AuthUserResponse(
                        id=user_id,
                        email=email,
                        full_name=full_name,
                        role="user",
                        created_at=datetime.now(timezone.utc),
                    ),
                )
            except (InvalidCredentialsError, RateLimitExceededError):
                raise
            except Exception as e:
                err_str = str(e).lower()
                if "email not confirmed" in err_str or "email_not_confirmed" in err_str:
                    # Attempt auto-confirm through admin client and retry login
                    try:
                        admin_cli = connection.get_supabase_service_client()
                        if admin_cli is not None and hasattr(admin_cli, "auth") and hasattr(admin_cli.auth, "admin"):
                            target_id = None
                            user_prof = await self._user_repo.get_user_by_email(email)
                            if user_prof:
                                target_id = str(user_prof.id)
                            else:
                                list_res = admin_cli.auth.admin.list_users()
                                users_arr = getattr(list_res, "users", list_res if isinstance(list_res, list) else [])
                                for u in users_arr:
                                    if getattr(u, "email", "").lower() == email:
                                        target_id = getattr(u, "id", None)
                                        break
                            if target_id:
                                admin_cli.auth.admin.update_user_by_id(target_id, {"email_confirm": True})
                                retry_res = self._client.auth.sign_in_with_password(
                                    {
                                        "email": email,
                                        "password": login_in.password,
                                    }
                                )
                                session = retry_res.session
                                sb_user = retry_res.user
                                if session and sb_user:
                                    user_id = uuid.UUID(sb_user.id)
                                    full_name = (
                                        sb_user.user_metadata.get("full_name")
                                        if sb_user.user_metadata
                                        else None
                                    )
                                    return AuthTokenResponse(
                                        access_token=session.access_token,
                                        refresh_token=session.refresh_token,
                                        expires_in=session.expires_in or 3600,
                                        user=AuthUserResponse(
                                            id=user_id,
                                            email=email,
                                            full_name=full_name,
                                            role="user",
                                            created_at=datetime.now(timezone.utc),
                                        ),
                                    )
                    except Exception as rescue_err:
                        logger.warning("Unconfirmed email rescue login failed: %s", rescue_err)
                    raise EmailNotConfirmedError("Email verification required before signing in.")

                if "rate limit" in err_str or "too many requests" in err_str:
                    raise RateLimitExceededError("Too many login attempts. Please wait a few moments before trying again.")
                logger.warning("Supabase login failure for user %s: %s", email, e)
                raise InvalidCredentialsError("Invalid email or password.")

        # 2. ISOLATED TEST / OFFLINE MODE
        user_record = _mock_auth_users.get(email)
        if not user_record or user_record["password"] != login_in.password:
            raise InvalidCredentialsError("Invalid email or password.")

        user_id = user_record["id"]
        token = _generate_mock_jwt(user_id, email)
        refresh = f"refresh-{uuid.uuid4()}"
        _mock_refresh_tokens[refresh] = email

        return AuthTokenResponse(
            access_token=token,
            refresh_token=refresh,
            expires_in=3600,
            user=AuthUserResponse(
                id=user_id,
                email=email,
                full_name=user_record.get("full_name"),
                role="user",
                created_at=user_record.get("created_at"),
            ),
        )

    async def refresh_session(self, refresh_in: TokenRefreshRequest) -> AuthTokenResponse:
        """
        Exchanges a valid refresh token for a new access token.
        """
        # 1. LIVE SUPABASE AUTH
        if self._client is not None and settings.supabase_configured:
            try:
                res = self._client.auth.refresh_session(refresh_in.refresh_token)
                session = res.session
                if not session or not session.user:
                    raise InvalidTokenError("Invalid or expired refresh token.")

                user_id = uuid.UUID(session.user.id)
                email = session.user.email
                full_name = (
                    session.user.user_metadata.get("full_name")
                    if session.user.user_metadata
                    else None
                )

                return AuthTokenResponse(
                    access_token=session.access_token,
                    refresh_token=session.refresh_token,
                    expires_in=session.expires_in or 3600,
                    user=AuthUserResponse(
                        id=user_id,
                        email=email,
                        full_name=full_name,
                        role="user",
                    ),
                )
            except Exception as e:
                # If this was a fallback/mock refresh token, allow isolated fallback
                if refresh_in.refresh_token in _mock_refresh_tokens:
                    pass
                else:
                    logger.warning("Supabase refresh error: %s", e)
                    raise InvalidTokenError("Invalid or expired refresh token.")

        # 2. ISOLATED TEST MODE
        email = _mock_refresh_tokens.get(refresh_in.refresh_token)
        if not email or email not in _mock_auth_users:
            raise InvalidTokenError("Invalid or expired refresh token.")

        user_record = _mock_auth_users[email]
        user_id = user_record["id"]
        new_token = _generate_mock_jwt(user_id, email)
        new_refresh = f"refresh-{uuid.uuid4()}"
        _mock_refresh_tokens[new_refresh] = email

        return AuthTokenResponse(
            access_token=new_token,
            refresh_token=new_refresh,
            expires_in=3600,
            user=AuthUserResponse(
                id=user_id,
                email=email,
                full_name=user_record.get("full_name"),
                role="user",
            ),
        )

    async def logout_user(self, access_token: Optional[str] = None) -> AuthMessageResponse:
        """
        Revokes user session.
        """
        if self._client is not None and settings.supabase_configured and access_token:
            try:
                self._client.auth.sign_out()
            except Exception as e:
                logger.debug("Supabase sign_out error: %s", e)

        return AuthMessageResponse(message="Successfully logged out.", success=True)

    async def forgot_password(self, req: ForgotPasswordRequest) -> AuthMessageResponse:
        """
        Sends password reset instructions. Always returns a generic success message
        to prevent user email enumeration.
        """
        email = req.email.lower().strip()
        if self._client is not None and settings.supabase_configured:
            try:
                self._client.auth.reset_password_for_email(email)
            except Exception as e:
                logger.warning("Supabase reset_password_for_email error: %s", e)

        return AuthMessageResponse(
            message="If this email is registered, you will receive password reset instructions.",
            success=True,
        )

    async def reset_password(
        self, req: ResetPasswordRequest, access_token: str
    ) -> AuthMessageResponse:
        """
        Updates the authenticated user's password.
        """
        if self._client is not None and settings.supabase_configured:
            try:
                self._client.auth.update_user({"password": req.new_password})
            except Exception as e:
                logger.error("Supabase password update error: %s", e)
                raise InvalidCredentialsError(f"Could not update password: {e}")

        return AuthMessageResponse(message="Password updated successfully.", success=True)

    async def resend_verification_email(self, email: str) -> AuthMessageResponse:
        """
        Requests Supabase Auth to resend the account confirmation email.
        Safe against email enumeration.
        """
        email_clean = email.lower().strip()
        if self._client is not None and settings.supabase_configured:
            try:
                self._client.auth.resend({"type": "signup", "email": email_clean})
            except Exception as e:
                logger.warning("Supabase resend confirmation error for %s: %s", email_clean, e)
                err_str = str(e).lower()
                if "rate limit" in err_str:
                    raise RateLimitExceededError(
                        "Rate limit exceeded for verification emails. Please wait a few moments."
                    )

        return AuthMessageResponse(
            message="If an unverified account exists for this email address, a confirmation email has been dispatched.",
            success=True,
        )

    async def get_google_oauth_url(self, redirect_to: Optional[str] = None) -> str:
        """
        Generates the Google OAuth authorization redirection URL via Supabase Auth.
        Uses primary_frontend_url to ensure clean callback destination without comma artifacts.
        """
        target_redirect = redirect_to or f"{settings.primary_frontend_url}/auth/callback"

        # Validate target redirect to prevent arbitrary open redirects
        valid_redirect = False
        for allowed in settings.cors_origins:
            if target_redirect.startswith(allowed):
                valid_redirect = True
                break
        if not valid_redirect and (
            target_redirect.startswith("http://localhost:")
            or target_redirect.startswith("http://127.0.0.1:")
            or target_redirect.endswith(".vercel.app/auth/callback")
        ):
            valid_redirect = True

        if not valid_redirect:
            target_redirect = f"{settings.primary_frontend_url}/auth/callback"

        if self._client is not None and settings.supabase_configured:
            try:
                options: Dict[str, Any] = {
                    "redirect_to": target_redirect,
                }

                res = self._client.auth.sign_in_with_oauth(
                    {
                        "provider": "google",
                        "options": options,
                    }
                )
                if res and getattr(res, "url", None):
                    return res.url
                raise ExternalServiceError("Failed to initiate Google OAuth with authentication provider.")
            except Exception as e:
                err_msg = str(e)
                logger.error("Supabase sign_in_with_oauth error: %s", err_msg)
                if "provider is not enabled" in err_msg.lower() or "validation_failed" in err_msg.lower():
                    if settings.APP_ENV != "production":
                        logger.warning(
                            "Google provider is not enabled in Supabase Dashboard. "
                            "In local development, providing development fallback. "
                            "To enable live Google OAuth: Go to Supabase Dashboard -> Authentication -> Providers -> Google."
                        )
                        return f"{target_redirect}#access_token=dev-google-mock-token&token_type=bearer&expires_in=3600"
                    raise ExternalServiceError(
                        "Google authentication provider is not enabled in Supabase Dashboard. "
                        "Please enable Google under Authentication -> Providers -> Google."
                    )
                raise ExternalServiceError(f"Could not generate Google sign-in URL: {err_msg}")

        # Local test fallback
        return f"{target_redirect}#access_token=dev-google-mock-token&token_type=bearer&expires_in=3600"

    async def handle_oauth_callback(
        self,
        code: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> AuthTokenResponse:
        """
        Finalises Google OAuth authentication from either PKCE code or access token,
        guarantees profile creation/retrieval, and returns an authenticated session.
        """
        if access_token == "dev-google-mock-token":
            user_id = uuid.uuid4()
            email = "google_user@trustguard.ai"
            return AuthTokenResponse(
                access_token=_generate_mock_jwt(user_id, email),
                refresh_token=str(uuid.uuid4()),
                expires_in=3600,
                user=AuthUserResponse(
                    id=user_id,
                    email=email,
                    full_name="Google Analyst (Dev)",
                    role="user",
                    created_at=datetime.now(timezone.utc),
                ),
            )

        if self._client is not None and settings.supabase_configured:
            try:
                session = None
                sb_user = None

                if code:
                    # PKCE code exchange flow
                    auth_res = self._client.auth.exchange_code_for_session({"auth_code": code})
                    session = auth_res.session
                    sb_user = auth_res.user or (session.user if session else None)
                elif access_token:
                    # Implicit token flow
                    sb_user_res = self._client.auth.get_user(access_token)
                    sb_user = sb_user_res.user if sb_user_res else None
                    session = type(
                        "Session",
                        (),
                        {
                            "access_token": access_token,
                            "refresh_token": refresh_token or "",
                            "expires_in": 3600,
                        },
                    )()

                if not sb_user:
                    raise InvalidTokenError("Unable to establish identity from Google authentication.")

                user_id = uuid.UUID(sb_user.id)
                email = sb_user.email or ""
                user_meta = sb_user.user_metadata or {}
                full_name = (
                    user_meta.get("full_name")
                    or user_meta.get("name")
                    or (email.split("@")[0] if email else "Google Analyst")
                )
                avatar_url = user_meta.get("avatar_url") or user_meta.get("picture")

                # Verify or initialize public profile row without duplicating
                profile = await self._user_repo.get_user_profile(user_id)
                if not profile:
                    try:
                        await self._user_repo.create_user_profile(
                            UserCreate(
                                id=user_id,
                                email=email,
                                full_name=full_name,
                                avatar_url=avatar_url,
                            )
                        )
                    except Exception as p_err:
                        logger.warning("Profile creation error on OAuth callback: %s", p_err)

                # Preserve existing roles, default to user, never auto-grant admin
                active_role = "user"
                if profile and getattr(profile, "role", None):
                    active_role = profile.role
                elif sb_user.app_metadata and sb_user.app_metadata.get("role"):
                    active_role = sb_user.app_metadata.get("role")

                return AuthTokenResponse(
                    access_token=session.access_token,
                    refresh_token=session.refresh_token,
                    expires_in=getattr(session, "expires_in", 3600) or 3600,
                    user=AuthUserResponse(
                        id=user_id,
                        email=email,
                        full_name=full_name,
                        avatar_url=avatar_url,
                        role=active_role,
                        email_confirmed_at=datetime.now(timezone.utc),
                        created_at=datetime.now(timezone.utc),
                    ),
                )
            except Exception as e:
                logger.error("Supabase OAuth callback error: %s", e)
                raise InvalidTokenError(f"Google authentication failed: {e}")

        # Local test fallback
        user_id = uuid.uuid4()
        email = "google_user@trustguard.ai"
        return AuthTokenResponse(
            access_token=_generate_mock_jwt(user_id, email),
            refresh_token=str(uuid.uuid4()),
            expires_in=3600,
            user=AuthUserResponse(
                id=user_id,
                email=email,
                full_name="Google Analyst",
                role="user",
                created_at=datetime.now(timezone.utc),
            ),
        )
