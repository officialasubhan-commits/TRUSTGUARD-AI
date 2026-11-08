"""
SQLAlchemy 2.x model for Threat Intelligence Records.
Maps to public.threat_reports / public.threat_intelligence_records in Supabase PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.scan import ScanHistory


class ThreatIntelligenceRecord(Base):
    __tablename__ = "threat_reports"

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
    normalized_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    threat_source: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="virustotal, urlhaus, internal_ml, community",
    )
    threat_category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    severity: Mapped[str] = mapped_column(
        String(32),
        default="medium",
        nullable=False,
        doc="critical, high, medium, low, info",
    )
    verification_status: Mapped[str] = mapped_column(
        String(32),
        default="verified",
        nullable=False,
        doc="verified, unverified, disputed",
    )
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    scan: Mapped[Optional["ScanHistory"]] = relationship(
        "ScanHistory", back_populates="threat_reports"
    )

    def __repr__(self) -> str:
        return f"<ThreatIntelligenceRecord id={self.id} source={self.threat_source} severity={self.severity}>"
