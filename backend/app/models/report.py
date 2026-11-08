"""
SQLAlchemy 2.x model for Community Threat Reports.
Maps to public.community_reports table in Supabase PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.scan import ScanHistory
    from app.models.user import User


class CommunityThreatReport(Base):
    __tablename__ = "community_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scan_history.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submitted_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    normalized_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    report_reason: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Category of threat (phishing, malware, scam, impersonation, etc.)",
    )
    threat_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_brand: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    attack_vector: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Moderation & Verification fields
    moderation_status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING",
        nullable=False,
        index=True,
        doc="PENDING, UNDER_REVIEW, APPROVED, REJECTED, DUPLICATE",
    )
    report_status: Mapped[str] = mapped_column(
        String(32),
        default="pending_review",
        nullable=False,
        doc="Legacy status compatibility: pending_review, verified, rejected",
    )
    verification_status: Mapped[str] = mapped_column(
        String(32),
        default="UNVERIFIED",
        nullable=False,
        doc="UNVERIFIED, COMMUNITY_SUPPORTED, ADMIN_VERIFIED, DISPUTED",
    )
    moderation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    moderator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duplicate_of: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("community_reports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    scan: Mapped[Optional["ScanHistory"]] = relationship(
        "ScanHistory", back_populates="community_reports"
    )
    user: Mapped["User"] = relationship(
        "User", back_populates="community_reports", foreign_keys=[user_id]
    )

    def __repr__(self) -> str:
        return (
            f"<CommunityThreatReport id={self.id} "
            f"domain={self.domain} mod_status={self.moderation_status}>"
        )
