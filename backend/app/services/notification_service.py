"""
Notification Service and Provider Abstraction for TrustGuard AI.
Handles email notification preference management, recipient checks,
and clean provider interfaces for outbound threat digest notifications.
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.exceptions import DatabaseError
from app.database.repositories.user_repo import UserRepository
from app.schemas.user import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    UserCreate,
    UserUpdate,
)

logger = logging.getLogger("trustguard.service.notification")


class INotificationProvider(ABC):
    """
    Abstract interface for outbound email delivery providers
    (e.g., SMTP, Resend, SendGrid, Amazon SES).
    """

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Indicates whether active credentials and network configuration exist."""
        pass

    @abstractmethod
    async def send_email(
        self,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        """Sends an email notification. Returns True if successfully accepted by provider."""
        pass


class DisabledNotificationProvider(INotificationProvider):
    """
    Null provider used when no third-party email transport is configured.
    Safely prevents sending fake emails while allowing full preference management.
    """

    @property
    def is_configured(self) -> bool:
        return False

    async def send_email(
        self,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
    ) -> bool:
        logger.info(
            "Outbound email transport unconfigured; omitted digest to %s ('%s')",
            recipient,
            subject,
        )
        return False


class NotificationService:
    """
    Manages user notification preferences and orchestrates threat digest eligibility.
    """

    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        provider: Optional[INotificationProvider] = None,
    ):
        self._user_repo = user_repo or UserRepository()
        self._provider = provider or DisabledNotificationProvider()

    @property
    def provider_configured(self) -> bool:
        return self._provider.is_configured

    async def get_user_preferences(
        self,
        user_id: uuid.UUID,
        user_email: str,
    ) -> NotificationPreferenceResponse:
        """
        Retrieves current email notification preference for an authenticated user.
        """
        profile = await self._user_repo.get_user_profile(user_id)
        if not profile:
            profile = await self._user_repo.create_user_profile(
                UserCreate(id=user_id, email=user_email, full_name=None)
            )

        return NotificationPreferenceResponse(
            threat_digest_enabled=profile.threat_digest_enabled,
            email=profile.email,
            updated_at=profile.updated_at,
            provider_configured=self._provider.is_configured,
        )

    async def update_user_preferences(
        self,
        user_id: uuid.UUID,
        user_email: str,
        update_in: NotificationPreferenceUpdate,
    ) -> NotificationPreferenceResponse:
        """
        Updates the threat digest email preference for an authenticated user.
        """
        existing = await self._user_repo.get_user_profile(user_id)
        if not existing:
            await self._user_repo.create_user_profile(
                UserCreate(id=user_id, email=user_email, full_name=None)
            )

        updated = await self._user_repo.update_user_profile(
            user_id,
            UserUpdate(threat_digest_enabled=update_in.threat_digest_enabled),
        )

        if not updated:
            raise DatabaseError("Failed to update notification preferences.")

        logger.info(
            "User %s updated threat_digest_enabled to %s",
            user_id,
            update_in.threat_digest_enabled,
        )

        now = datetime.now(timezone.utc)
        return NotificationPreferenceResponse(
            threat_digest_enabled=updated.threat_digest_enabled,
            email=updated.email,
            updated_at=now,
            provider_configured=self._provider.is_configured,
        )


# Singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service

