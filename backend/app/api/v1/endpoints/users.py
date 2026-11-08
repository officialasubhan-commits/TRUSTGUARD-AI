"""
User Profile API Endpoints for TrustGuard AI.
Allows authenticated users to view and update their public profile.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status

from app.core.exceptions import DatabaseError
from app.core.security import AuthenticatedUser, get_current_user
from app.database.repositories.user_repo import UserRepository
from app.schemas.user import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    UserCreate,
    UserProfileResponse,
    UserUpdate,
)
from app.services.notification_service import NotificationService, get_notification_service

logger = logging.getLogger("trustguard.api.users")
router = APIRouter()


def get_user_repository() -> UserRepository:
    return UserRepository()


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User Profile",
    description="Retrieves the authenticated user's profile record from the database.",
)
async def get_my_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserProfileResponse:
    profile = await user_repo.get_user_profile(current_user.user_id)
    if not profile:
        # If user exists in Auth but profile row is missing, initialize it automatically
        logger.info("Initializing missing profile row for user %s", current_user.user_id)
        profile = await user_repo.create_user_profile(
            UserCreate(
                id=current_user.user_id,
                email=current_user.email or "user@trustguard.ai",
                full_name=None,
            )
        )
    return profile


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Profile",
    description="Updates user profile fields (full name, avatar URL). Users cannot modify their role.",
)
async def update_my_profile(
    update_in: UserUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserProfileResponse:
    # Restrict updates to safe profile fields only (cannot change is_active, scan_count, role)
    safe_update = UserUpdate(
        full_name=update_in.full_name,
        avatar_url=update_in.avatar_url,
        threat_digest_enabled=update_in.threat_digest_enabled,
    )
    updated = await user_repo.update_user_profile(current_user.user_id, safe_update)
    if not updated:
        raise DatabaseError("Profile not found or could not be updated.")
    return updated


@router.get(
    "/me/notifications",
    response_model=NotificationPreferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Email Notification Preferences",
    description="Retrieves the authenticated user's threat digest email preferences.",
)
async def get_my_notification_preferences(
    current_user: AuthenticatedUser = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationPreferenceResponse:
    return await notification_service.get_user_preferences(
        user_id=current_user.user_id,
        user_email=current_user.email or "user@trustguard.ai",
    )


@router.patch(
    "/me/notifications",
    response_model=NotificationPreferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Email Notification Preferences",
    description="Enables or disables periodic threat digest email summaries for the authenticated user.",
)
async def update_my_notification_preferences(
    update_in: NotificationPreferenceUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationPreferenceResponse:
    return await notification_service.update_user_preferences(
        user_id=current_user.user_id,
        user_email=current_user.email or "user@trustguard.ai",
        update_in=update_in,
    )
