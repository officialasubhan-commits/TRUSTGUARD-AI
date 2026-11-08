"""
Pydantic schemas for Community Threat Reporting & Moderation.
Supports public sanitized views, user submission history, and admin moderation workflows.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ------------------------------------------------------------------ #
# Allowed Types & Enums                                              #
# ------------------------------------------------------------------ #

ThreatCategoryType = Literal[
    "PHISHING",
    "FAKE_LOGIN_PAGE",
    "MALWARE_DISTRIBUTION",
    "FRAUD_OR_SCAM",
    "IMPERSONATION",
    "SUSPICIOUS_REDIRECT",
    "OTHER",
    # Legacy lowercase support
    "phishing",
    "malware",
    "scam",
    "spam",
    "impersonation",
    "other",
]
ReportReasonType = ThreatCategoryType

ModerationStatusType = Literal[
    "PENDING",
    "UNDER_REVIEW",
    "APPROVED",
    "REJECTED",
    "DUPLICATE",
    # Legacy support
    "pending_review",
    "verified",
    "rejected",
]
ReportStatusType = ModerationStatusType

VerificationStatusType = Literal[
    "UNVERIFIED",
    "COMMUNITY_SUPPORTED",
    "ADMIN_VERIFIED",
    "DISPUTED",
    # Legacy support
    "unverified",
    "verified",
    "false_positive",
]


# ------------------------------------------------------------------ #
# Submission & Update Schemas                                        #
# ------------------------------------------------------------------ #


class CommunityReportCreate(BaseModel):
    """Schema for submitting a new community threat report."""

    submitted_url: str = Field(
        ...,
        min_length=4,
        max_length=2048,
        description="URL being reported as suspicious",
    )
    category: Optional[str] = Field(
        None,
        description="Threat category (e.g. PHISHING, FAKE_LOGIN_PAGE, FRAUD_OR_SCAM)",
    )
    report_reason: Optional[str] = Field(
        None,
        description="Legacy field name for threat category",
    )
    description: Optional[str] = Field(
        None,
        max_length=1500,
        description="User-provided description of the threat or suspicious indicators",
    )
    notes: Optional[str] = Field(
        None,
        max_length=1500,
        description="Legacy field for additional context",
    )
    scan_id: Optional[uuid.UUID] = Field(
        None,
        description="Optional scan ID linked to this report",
    )
    target_brand: Optional[str] = Field(
        None,
        max_length=255,
        description="Brand or entity being impersonated",
    )
    attack_vector: Optional[str] = Field(
        None,
        max_length=64,
        description="Delivery vector (e.g. email, sms, social_media, search_ad)",
    )
    evidence_url: Optional[str] = Field(
        None,
        max_length=2048,
        description="Optional link to public evidence or reference (non-sensitive)",
    )

    @field_validator("submitted_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        url_str = v.strip()
        if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", url_str, re.IGNORECASE):
            raise ValueError("Submitted URL must be a valid HTTP or HTTPS address.")
        return url_str

    @model_validator(mode="before")
    @classmethod
    def unify_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normalize category / report_reason
            raw_reason = data.get("report_reason")
            raw_cat = data.get("category")
            primary = raw_cat or raw_reason or "PHISHING"
            data["category"] = primary.upper() if isinstance(primary, str) else "PHISHING"
            data["report_reason"] = raw_reason if raw_reason else data["category"]

            # Normalize description / notes
            desc = data.get("description") or data.get("notes")
            if desc:
                data["description"] = desc
                data["notes"] = desc
        return data


class CommunityReportModerationUpdate(BaseModel):
    """Schema for administrator moderation action."""

    moderation_status: Literal["PENDING", "UNDER_REVIEW", "APPROVED", "REJECTED", "DUPLICATE"] = (
        Field(..., description="Updated moderation lifecycle state")
    )
    verification_status: Optional[
        Literal["UNVERIFIED", "COMMUNITY_SUPPORTED", "ADMIN_VERIFIED", "DISPUTED"]
    ] = Field(None, description="Optional updated threat verification status")
    moderation_notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Reviewer rationale or moderation comments",
    )
    duplicate_of: Optional[uuid.UUID] = Field(
        None,
        description="Primary canonical report ID if marked as duplicate",
    )


# ------------------------------------------------------------------ #
# Response Schemas                                                   #
# ------------------------------------------------------------------ #


class CommunityReportPublicResponse(BaseModel):
    """
    Sanitized public view of an approved community threat report.
    Never exposes reporter user_id, email, moderator notes, or internal IP.
    """

    id: uuid.UUID
    scan_id: Optional[uuid.UUID] = None
    submitted_url: str
    normalized_url: str
    domain: Optional[str] = None
    category: str
    report_reason: str
    threat_type: Optional[str] = None
    target_brand: Optional[str] = None
    attack_vector: Optional[str] = None
    description: Optional[str] = None
    moderation_status: str = "APPROVED"
    verification_status: str
    upvotes: int = 0
    user_confirmed: Optional[bool] = False
    integrity_hash: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def populate_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            reason = data.get("report_reason") or data.get("category") or "OTHER"
            data["report_reason"] = reason
            data["category"] = reason
            if not data.get("description"):
                data["description"] = data.get("notes")
            if not data.get("moderation_status"):
                data["moderation_status"] = data.get("report_status") or "APPROVED"
        elif hasattr(data, "__dict__"):
            reason = getattr(data, "report_reason", None) or getattr(data, "category", "OTHER")
            setattr(data, "report_reason", reason)
            setattr(data, "category", reason)
            if not getattr(data, "description", None):
                setattr(data, "description", getattr(data, "notes", None))
        return data


class CommunityReportUserResponse(BaseModel):
    """View of a report for the submitting user (includes moderation status)."""

    id: uuid.UUID
    scan_id: Optional[uuid.UUID] = None
    submitted_url: str
    normalized_url: str
    domain: Optional[str] = None
    category: str
    report_reason: str
    target_brand: Optional[str] = None
    attack_vector: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    evidence_url: Optional[str] = None
    moderation_status: str
    moderation_notes: Optional[str] = None
    verification_status: str
    upvotes: int = 0
    duplicate_of: Optional[uuid.UUID] = None
    integrity_hash: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def map_user_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            reason = data.get("report_reason") or data.get("category") or "OTHER"
            data["report_reason"] = reason
            data["category"] = reason
            if not data.get("description"):
                data["description"] = data.get("notes")
            if not data.get("notes"):
                data["notes"] = data.get("description")
        elif hasattr(data, "__dict__"):
            reason = getattr(data, "report_reason", None) or getattr(data, "category", "OTHER")
            setattr(data, "report_reason", reason)
            setattr(data, "category", reason)
            if not getattr(data, "description", None):
                setattr(data, "description", getattr(data, "notes", None))
            if not getattr(data, "notes", None):
                setattr(data, "notes", getattr(data, "description", None))
        return data


class CommunityReportAdminResponse(BaseModel):
    """Full administrative view of a community threat report."""

    id: uuid.UUID
    scan_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    submitted_url: str
    normalized_url: str
    domain: Optional[str] = None
    category: str
    report_reason: str
    threat_type: Optional[str] = None
    target_brand: Optional[str] = None
    attack_vector: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    evidence_url: Optional[str] = None
    moderation_status: str
    moderation_notes: Optional[str] = None
    moderator_id: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    verification_status: str
    duplicate_of: Optional[uuid.UUID] = None
    upvotes: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def map_admin_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            reason = data.get("report_reason") or data.get("category") or "OTHER"
            data["report_reason"] = reason
            data["category"] = reason
            if not data.get("description"):
                data["description"] = data.get("notes")
            if not data.get("notes"):
                data["notes"] = data.get("description")
        return data


# Legacy compatibility alias
class CommunityReportResponse(CommunityReportPublicResponse):
    """Backward compatibility class for legacy code referencing CommunityReportResponse."""

    scan_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    report_status: Optional[str] = "pending_review"


# ------------------------------------------------------------------ #
# Pagination Schema                                                  #
# ------------------------------------------------------------------ #

T = TypeVar("T")


class PaginatedCommunityReports(BaseModel, Generic[T]):
    """Generic paginated wrapper for community reports."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class CommunityStatisticsResponse(BaseModel):
    """Aggregate platform community reporting telemetry."""

    total_reports: int = 0
    pending_review: int = 0
    verified_reports: int = 0
    rejected_reports: int = 0
    resolved_reports: int = 0
    active_confirmations: int = 0
    generated_at: datetime


class CommunityConfirmationToggleResponse(BaseModel):
    """Response returned when an authenticated user confirms or withdraws confirmation."""

    report_id: uuid.UUID
    confirmed: bool
    total_confirmations: int
    message: str


class CommunityReportFlagCreate(BaseModel):
    """Payload to flag a community report for inaccuracies, abuse, or obsolescence."""

    flag_reason: Literal["INACCURATE", "ABUSIVE_OR_SPAM", "DUPLICATE", "RESOLVED_SAFE", "OTHER"] = Field(
        ..., description="Reason for flagging the report"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Additional context for moderators")


class CommunityReportFlagResponse(BaseModel):
    """Confirmation of recorded flag."""

    id: uuid.UUID
    report_id: uuid.UUID
    flag_reason: str
    created_at: datetime
    message: str


class Web3IntegrityProofResponse(BaseModel):
    """Cryptographic proof of canonical threat intelligence record integrity."""

    report_id: uuid.UUID
    canonical_hash: str
    algorithm: str = "SHA-256"
    proof_type: str = "EVM_TESTNET_LOG"
    network: str = "Polygon Amoy Testnet (ChainID 80002)"
    contract_address: Optional[str] = "0x71C35b0E993B49E7fFe5F73E7eEcE8888b13dF82"
    merkle_root: str
    verified: bool = True
    verification_timestamp: datetime
    canonical_payload: Dict[str, Any]

