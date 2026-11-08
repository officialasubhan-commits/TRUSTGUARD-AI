"""
Pydantic schemas for Scan History, Detailed Security Reports, Statistics, and Exports.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.risk_scoring import FindingItem
from app.schemas.scan import RiskCategory, ScanStatusType

SortOptionType = Literal[
    "newest", "oldest", "highest_score", "lowest_score", "created_at", "trust_score"
]
RiskFilterType = Literal[
    "LOW_RISK",
    "MODERATE_RISK",
    "HIGH_RISK",
    "CRITICAL_RISK",
    "INSUFFICIENT_DATA",
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    "SAFE",
    "UNKNOWN",
]
DateFilterType = Literal["today", "last_7_days", "last_30_days", "custom"]


class ScanHistorySummary(BaseModel):
    """Compact summary of a scan record for history list and statistical views."""

    scan_id: uuid.UUID = Field(..., description="Unique scan identifier")
    domain: Optional[str] = Field(None, description="Extracted target domain / host")
    submitted_url: str = Field(..., description="Target URL originally entered by the user")
    normalized_url: str = Field(..., description="Canonical URL representation")
    scan_status: ScanStatusType = Field(
        ..., description="Lifecycle status: pending, processing, complete, error"
    )
    digital_trust_score: Optional[int] = Field(
        None, ge=0, le=100, description="Calculated Digital Trust Score (0-100)"
    )
    risk_score: Optional[int] = Field(
        None, ge=0, le=100, description="Synthesized risk score (0-100)"
    )
    risk_level: Optional[RiskCategory] = Field(None, description="Risk level category")
    risk_label: Optional[str] = Field(
        None, description="Human-readable risk label (e.g. LOW RISK, CRITICAL RISK)"
    )
    assessment_status: Optional[str] = Field(
        None, description="Assessment completeness: COMPLETE, PARTIAL, INSUFFICIENT_DATA"
    )
    assessment_coverage: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Evaluation telemetry coverage (0.0 to 1.0)"
    )
    coverage_percentage: Optional[int] = Field(
        None, ge=0, le=100, description="Coverage expressed as percentage"
    )
    scoring_version: Optional[str] = Field(None, description="Algorithm scoring version utilized")
    created_at: datetime = Field(..., description="Timestamp when scan was initiated")
    completed_at: Optional[datetime] = Field(None, description="Timestamp when analysis completed")

    model_config = ConfigDict(from_attributes=True)


class PaginatedScanHistoryResponse(BaseModel):
    """Server-side paginated response of scan history records."""

    total_items: int = Field(..., ge=0, description="Total matching scan records")
    total_pages: int = Field(..., ge=0, description="Total number of pages given page_size")
    current_page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    has_next: bool = Field(..., description="True if a subsequent page of results exists")
    has_prev: bool = Field(..., description="True if a previous page of results exists")
    items: List[ScanHistorySummary] = Field(
        default_factory=list, description="Page of scan history summaries"
    )

    model_config = ConfigDict(from_attributes=True)


class ScanStatisticsResponse(BaseModel):
    """Aggregated scan metrics and activity statistics for an authenticated user."""

    total_scans: int = Field(
        default=0, ge=0, description="Total historical scans submitted by user"
    )
    low_risk_scans: int = Field(
        default=0, ge=0, description="Scans categorized as LOW or SAFE risk"
    )
    moderate_risk_scans: int = Field(
        default=0, ge=0, description="Scans categorized as MEDIUM / MODERATE risk"
    )
    high_risk_scans: int = Field(default=0, ge=0, description="Scans categorized as HIGH risk")
    critical_risk_scans: int = Field(
        default=0, ge=0, description="Scans categorized as CRITICAL risk"
    )
    incomplete_assessments: int = Field(
        default=0, ge=0, description="Scans marked pending, error, or with insufficient telemetry"
    )
    average_trust_score: Optional[float] = Field(
        None, description="Average Digital Trust Score across eligible completed scans"
    )
    recent_scans: List[ScanHistorySummary] = Field(
        default_factory=list, description="Up to 5 most recent scans"
    )
    generated_at: datetime = Field(..., description="Timestamp when statistics were computed")

    model_config = ConfigDict(from_attributes=True)


class DailyScanActivity(BaseModel):
    """Daily aggregated scan count and threat distribution for activity visualization."""

    date: str = Field(..., description="Calendar date (YYYY-MM-DD)")
    scan_count: int = Field(default=0, ge=0, description="Total scans conducted on this date")
    threat_count: int = Field(
        default=0, ge=0, description="High and critical risk detections on this date"
    )
    safe_count: int = Field(
        default=0, ge=0, description="Safe and low risk inspections on this date"
    )
    moderate_count: int = Field(
        default=0, ge=0, description="Moderate/medium risk evaluations on this date"
    )

    model_config = ConfigDict(from_attributes=True)


class DetailedSecurityReportResponse(BaseModel):
    """Complete, historical security report for a specific scanned URL."""

    scan_id: uuid.UUID = Field(..., description="Unique scan identifier")
    original_url: str = Field(..., description="Original submitted URL")
    normalized_url: str = Field(..., description="RFC 3986 normalized URL")
    domain: str = Field(..., description="Extracted domain or hostname")
    is_guest: bool = Field(default=False, description="Whether scan was submitted anonymously")
    scan_status: ScanStatusType = Field(..., description="Processing status")
    digital_trust_score: Optional[int] = Field(
        None, ge=0, le=100, description="Final Digital Trust Score (0-100)"
    )
    risk_score: Optional[int] = Field(
        None, ge=0, le=100, description="Synthesized risk score (0-100)"
    )
    risk_level: Optional[RiskCategory] = Field(None, description="Overall risk category")
    risk_label: Optional[str] = Field(None, description="Human-readable risk label")
    assessment_status: Optional[str] = Field(
        None, description="COMPLETE, PARTIAL, or INSUFFICIENT_DATA"
    )
    assessment_coverage: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Available weight coverage"
    )
    coverage_percentage: Optional[int] = Field(
        None, ge=0, le=100, description="Coverage percentage"
    )
    high_severity_override: bool = Field(
        default=False, description="True if an active critical override was triggered"
    )
    override_reason: Optional[str] = Field(
        None, description="Explanation of high-severity override trigger"
    )
    scoring_version: Optional[str] = Field(None, description="Preserved algorithm scoring version")
    model_version: Optional[str] = Field(None, description="Preserved ML model version artifact")
    submitted_at: datetime = Field(..., description="When the scan was initiated")
    completed_at: Optional[datetime] = Field(None, description="When the analysis completed")
    summary: Optional[str] = Field(None, description="Executive narrative summary")
    recommendations: List[str] = Field(
        default_factory=list, description="Actionable safety guidance"
    )
    risk_indicators: List[FindingItem] = Field(
        default_factory=list, description="Identified risk factors and anomalies"
    )
    positive_indicators: List[FindingItem] = Field(
        default_factory=list, description="Positive security affirmations"
    )
    unknown_indicators: List[FindingItem] = Field(
        default_factory=list, description="Inconclusive or rate-limited feeds"
    )
    module_scores: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed per-module risk contributions"
    )

    # Modular sub-results
    url_analysis: Optional[Dict[str, Any]] = None
    virustotal_findings: Optional[Dict[str, Any]] = None
    ml_phishing_prediction: Optional[Dict[str, Any]] = None
    ssl_tls_validation: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ExportableSecurityReport(BaseModel):
    """Sanitized, shareable security report formatted for export without internal implementation details."""

    report_id: str = Field(..., description="Unique report reference")
    target_url: str = Field(..., description="Target URL analyzed")
    domain: str = Field(..., description="Analyzed domain")
    digital_trust_score: Optional[int] = Field(None, description="Digital Trust Score (0-100)")
    risk_level: Optional[str] = Field(
        None, description="Risk Level (LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN)"
    )
    risk_label: Optional[str] = Field(None, description="Descriptive Risk Label")
    assessment_status: str = Field(..., description="Assessment completion status")
    coverage_percentage: Optional[int] = Field(None, description="Assessment coverage percentage")
    summary: Optional[str] = Field(None, description="Executive summary")
    recommendations: List[str] = Field(default_factory=list, description="User guidance")
    risk_indicators: List[Dict[str, Any]] = Field(
        default_factory=list, description="Identified risks"
    )
    positive_indicators: List[Dict[str, Any]] = Field(
        default_factory=list, description="Positive security signals"
    )
    unknown_indicators: List[Dict[str, Any]] = Field(
        default_factory=list, description="Unchecked or offline telemetry"
    )
    scan_timestamp: datetime = Field(..., description="Timestamp of analysis")
    scoring_version: Optional[str] = Field(None, description="Scoring engine version")
    platform: str = Field(default="TrustGuard AI", description="Issuing security engine")
    disclaimer: str = Field(
        default=(
            "Notice: TrustGuard AI evaluations are automated predictive security assessments. "
            "Absence of detections does not guarantee absolute safety. Always verify critical credentials."
        ),
        description="Legal and security advisory disclaimer",
    )

    model_config = ConfigDict(from_attributes=True)


class ScanDeleteResponse(BaseModel):
    """Response returned upon successful scan record deletion."""

    success: bool = Field(
        default=True, description="Indicates whether record was successfully deleted"
    )
    scan_id: uuid.UUID = Field(..., description="UUID of the deleted scan")
    message: str = Field(default="Scan record and associated results successfully deleted.")
    deleted_at: datetime = Field(..., description="Timestamp of deletion")
