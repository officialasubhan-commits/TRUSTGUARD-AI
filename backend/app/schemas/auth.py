"""
Pydantic schemas for authentication requests and responses.
Enforces strict input validation on emails and passwords.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserRegisterRequest(BaseModel):
    """Client request schema for registering a new user."""

    email: EmailStr = Field(..., description="Valid user email address")
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="User's full name or display name",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters, at least 1 letter and 1 number/symbol)",
    )
    confirm_password: str = Field(
        ..., min_length=8, max_length=128, description="Password confirmation"
    )

    @model_validator(mode="after")
    def validate_password_strength_and_match(self) -> UserRegisterRequest:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")

        # Require at least one letter and at least one digit or special character
        has_letter = bool(re.search(r"[a-zA-Z]", self.password))
        has_number_or_symbol = bool(re.search(r"[\d\W_]", self.password))

        if not (has_letter and has_number_or_symbol):
            raise ValueError("Password must contain at least one letter and one number or symbol.")

        return self


class UserLoginRequest(BaseModel):
    """Client request schema for authenticating with email and password."""

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, max_length=128, description="User password")


class TokenRefreshRequest(BaseModel):
    """Client request schema for refreshing an expired access token."""

    refresh_token: str = Field(..., min_length=10, description="Supabase refresh token")


class ForgotPasswordRequest(BaseModel):
    """Client request schema for initiating password recovery email."""

    email: EmailStr = Field(..., description="Registered user email address")


class ResetPasswordRequest(BaseModel):
    """Client request schema for setting a new password via recovery."""

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (minimum 8 characters)",
    )
    confirm_new_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_passwords_match(self) -> ResetPasswordRequest:
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match.")
        has_letter = bool(re.search(r"[a-zA-Z]", self.new_password))
        has_number_or_symbol = bool(re.search(r"[\d\W_]", self.new_password))
        if not (has_letter and has_number_or_symbol):
            raise ValueError("Password must contain at least one letter and one number or symbol.")
        return self


class ResendVerificationRequest(BaseModel):
    """Client request schema to resend signup verification email."""

    email: EmailStr = Field(..., description="Registered email address")


class OAuthUrlResponse(BaseModel):
    """Redirection URL for third-party OAuth authentication."""

    url: str = Field(..., description="Authorization URL for OAuth redirection")
    provider: str = Field(default="google", description="Identity provider name")


class OAuthCallbackRequest(BaseModel):
    """Payload delivered to the backend upon return from the OAuth provider."""

    code: Optional[str] = Field(default=None, description="PKCE authorization code")
    access_token: Optional[str] = Field(default=None, description="Access token from hash fragment")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token from hash fragment")


class AuthUserResponse(BaseModel):
    """User metadata returned within authentication payloads."""

    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str = "user"
    email_confirmed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AuthTokenResponse(BaseModel):
    """Response schema containing access and refresh tokens."""

    access_token: str = Field(..., description="Supabase JWT access token")
    token_type: str = Field(default="bearer", description="Token type (Bearer)")
    expires_in: int = Field(default=3600, description="Token validity in seconds")
    refresh_token: Optional[str] = Field(None, description="Supabase refresh token")
    user: AuthUserResponse = Field(..., description="User identity information")


class AuthMessageResponse(BaseModel):
    """Generic status response for auth operations (logout, reset email, etc.)."""

    message: str = Field(..., description="Safe human-readable status message")
    success: bool = Field(default=True, description="Operation success flag")
