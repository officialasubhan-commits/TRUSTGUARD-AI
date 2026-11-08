"""
SQLAlchemy 2.x models for URL Scan History and Detailed Scan Results.
Maps to public.scan_history and public.scan_results tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.report import CommunityThreatReport
    from app.models.threat_intel import ThreatIntelligenceRecord
    from app.models.user import User


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Null for guest scans, set for registered users",
    )
    submitted_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    normalized_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="Extracted host domain name",
    )
    url_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="SHA-256 for fast deduplication",
    )
    scan_status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        doc="pending, processing, complete, error",
    )
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        doc="SAFE, LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN",
    )
    trust_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="0-100 composite score"
    )
    risk_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, doc="0-100 synthesized risk score"
    )
    assessment_status: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, doc="COMPLETE, PARTIAL, INSUFFICIENT_DATA"
    )
    assessment_coverage: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, doc="Fractional evaluation coverage (0.0 to 1.0)"
    )
    scoring_version: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, doc="Version of scoring algorithm used"
    )
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="scans")
    result: Mapped[Optional["ScanResult"]] = relationship(
        "ScanResult",
        back_populates="scan",
        uselist=False,
        cascade="all, delete-orphan",
    )
    community_reports: Mapped[List["CommunityThreatReport"]] = relationship(
        "CommunityThreatReport",
        back_populates="scan",
    )
    threat_reports: Mapped[List["ThreatIntelligenceRecord"]] = relationship(
        "ThreatIntelligenceRecord",
        back_populates="scan",
    )

    def __repr__(self) -> str:
        return f"<ScanHistory id={self.id} status={self.scan_status} score={self.trust_score}>"


class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scan_history.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    trust_score: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Final Digital Trust Score 0-100"
    )
    overall_risk_level: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="SAFE, LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN",
    )

    # ML Intelligence
    phishing_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ml_prediction: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ml_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ml_features: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # VirusTotal & External Threat Intelligence
    virustotal_detection_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    virustotal_total_engines: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    threat_intelligence_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    vt_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vt_raw: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # SSL / TLS Analysis
    ssl_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ssl_valid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    ssl_issuer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ssl_expiry_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ssl_days_remaining: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ssl_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ssl_raw: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # URL Heuristics & Breakdown
    url_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    url_risk_indicators: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB, nullable=True
    )
    score_breakdown: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    analysis_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    scan: Mapped["ScanHistory"] = relationship("ScanHistory", back_populates="result")

    def __repr__(self) -> str:
        return f"<ScanResult id={self.id} scan_id={self.scan_id} score={self.trust_score}>"
