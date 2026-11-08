"""
Pydantic schemas for User Profile data management.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name or display name")
    avatar_url: Optional[str] = Field(None, max_length=1024, description="Profile avatar URL")


class UserCreate(UserBase):
    id: uuid.UUID = Field(..., description="Must match auth.users.id from Supabase Auth")
    threat_digest_enabled: bool = Field(default=False, description="Whether threat digest notifications are enabled")


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=1024)
    is_active: Optional[bool] = None
    threat_digest_enabled: Optional[bool] = Field(None, description="Enable or disable periodic threat digest emails")


class UserProfileResponse(UserBase):
    id: uuid.UUID
    scan_count: int = Field(default=0, ge=0)
    is_active: bool = True
    threat_digest_enabled: bool = Field(default=False, description="Email notification preference for threat digests")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""
    threat_digest_enabled: bool = Field(
        ...,
        description="Whether to receive periodic email summaries about relevant security threats and updates"
    )


class NotificationPreferenceResponse(BaseModel):
    """Schema returning current notification preferences."""
    threat_digest_enabled: bool
    email: EmailStr
    updated_at: datetime
    provider_configured: bool = Field(
        default=False,
        description="Indicates whether an active outbound email transport is configured on the platform"
    )
