"""
Pydantic schemas for TrustGuard AI Admin Panel.
Defines strict type models for Administrator Authentication, User Management,
Threat Moderation, System Monitoring, Maintenance Mode, and Audit Logging.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# -----------------------------------------------------------------------------
# 1. Administrator Authentication & Profile
# -----------------------------------------------------------------------------
class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="Administrator username")
    password: str = Field(..., min_length=8, description="Administrator password")


class AdminUserProfile(BaseModel):
    id: uuid.UUID
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: str = "super_admin"
    is_active: bool = True
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(default=28800, description="Token validity in seconds (8 hours)")
    admin_user: AdminUserProfile


class AdminChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8, description="Must be at least 8 characters with numbers & symbols")


# -----------------------------------------------------------------------------
# 2. Admin Dashboard Statistics & Activity
# -----------------------------------------------------------------------------
class AdminDashboardStats(BaseModel):
    total_users: int = 0
    active_users: int = 0
    total_scans: int = 0
    total_community_reports: int = 0
    pending_reports: int = 0
    verified_reports: int = 0
    rejected_reports: int = 0
    resolved_reports: int = 0
    high_risk_urls: int = 0
    safe_scans: int = 0
    suspicious_scans: int = 0
    malicious_scans: int = 0
    total_contributors: int = 0
    published_pages: int = 0
    system_status: str = "healthy"
    maintenance_enabled: bool = False
    maintenance_message: Optional[str] = None


class DailyActivityPoint(BaseModel):
    date: str
    scans: int = 0
    registrations: int = 0
    reports: int = 0


class ThreatCategoryPoint(BaseModel):
    category: str
    count: int = 0


class ModerationActivityPoint(BaseModel):
    date: str
    approved: int = 0
    rejected: int = 0


class AdminDashboardActivity(BaseModel):
    timeline: List[DailyActivityPoint] = []
    threat_categories: List[ThreatCategoryPoint] = []
    moderation_activity: List[ModerationActivityPoint] = []


class AdminEventItem(BaseModel):
    id: str
    event_type: str
    title: str
    description: str
    timestamp: datetime
    status: Optional[str] = None
    severity: Optional[str] = "info"


# -----------------------------------------------------------------------------
# 3. User Management
# -----------------------------------------------------------------------------
class AdminUserListItem(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    scan_count: int = 0
    is_active: bool = True
    role: str = "user"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedAdminUsers(BaseModel):
    items: List[AdminUserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminUserDetail(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    scan_count: int = 0
    is_active: bool = True
    role: str = "user"
    created_at: datetime
    updated_at: datetime
    recent_scans: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)


class AdminUserStatusUpdate(BaseModel):
    is_active: bool
    reason: str = Field(..., min_length=4, max_length=500, description="Mandatory administrative rationale")


class AdminUserRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(user|security_analyst|moderator|admin)$")
    reason: str = Field(..., min_length=4, max_length=500, description="Mandatory reason for role change")


class AdminUserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AdminUserEmailChangeRequest(BaseModel):
    new_email: EmailStr
    reason: Optional[str] = None


class AdminUserDeleteRequest(BaseModel):
    reason: Optional[str] = None


# -----------------------------------------------------------------------------
# 4. Community Threat Report Moderation
# -----------------------------------------------------------------------------
class AdminReportListItem(BaseModel):
    id: uuid.UUID
    submitted_url: str
    domain: Optional[str] = None
    report_reason: str
    threat_type: Optional[str] = None
    target_brand: Optional[str] = None
    submitter_email: Optional[str] = None
    moderation_status: str = "PENDING"
    report_status: str = "pending_review"
    verification_status: str = "unverified"
    upvotes: int = 0
    attachments_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedAdminReports(BaseModel):
    items: List[AdminReportListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminReportDetail(BaseModel):
    id: uuid.UUID
    submitted_url: str
    normalized_url: str
    domain: Optional[str] = None
    report_reason: str
    threat_type: Optional[str] = None
    target_brand: Optional[str] = None
    attack_vector: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    submitter_email: Optional[str] = None
    submitter_id: Optional[uuid.UUID] = None
    moderation_status: str
    moderation_notes: Optional[str] = None
    reviewer_id: Optional[uuid.UUID] = None
    reviewer_username: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    upvotes: int = 0
    confirmations_count: int = 0
    confirmations: List[Dict[str, Any]] = []
    evidence_items: List[Dict[str, Any]] = []
    associated_scan: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminReportModerationAction(BaseModel):
    action: str = Field(
        ...,
        pattern="^(APPROVE|REJECT|UNDER_REVIEW|RESOLVED|DUPLICATE|REQUEST_EVIDENCE)$",
        description="Moderation outcome verdict",
    )
    reason: str = Field(..., min_length=3, max_length=1000, description="Mandatory rationale for review decision")
    internal_notes: Optional[str] = Field(None, max_length=2000, description="Private admin-only notes")
    duplicate_of: Optional[uuid.UUID] = None


class AdminBulkModerationRequest(BaseModel):
    report_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100)
    action: str = Field(..., pattern="^(APPROVE|REJECT|UNDER_REVIEW|RESOLVED)$")
    reason: str = Field(..., min_length=3, max_length=1000)
    internal_notes: Optional[str] = None


class BulkModerationDetail(BaseModel):
    report_id: uuid.UUID
    success: bool
    status: str
    error: Optional[str] = None


class AdminBulkModerationResponse(BaseModel):
    total_selected: int
    succeeded: int
    failed: int
    details: List[BulkModerationDetail]


# -----------------------------------------------------------------------------
# 5. Evidence & Attachment Management
# -----------------------------------------------------------------------------
class AdminEvidenceItem(BaseModel):
    id: str
    report_id: uuid.UUID
    filename: str
    file_type: str
    file_size_bytes: int
    url: str
    sha256_hash: Optional[str] = None
    is_quarantined: bool = False
    quarantine_reason: Optional[str] = None
    created_at: datetime


# -----------------------------------------------------------------------------
# 6. Threat Intelligence Management
# -----------------------------------------------------------------------------
class ThreatIntelItem(BaseModel):
    id: str
    domain: str
    threat_category: str
    severity: str
    source: str
    verification_status: str
    first_seen: datetime
    evidence_count: int


class AdminThreatIntelSummary(BaseModel):
    total_verified_threats: int
    source_breakdown: Dict[str, int]
    top_threat_categories: List[Dict[str, Any]]
    external_providers: List[Dict[str, Any]]
    recent_threats: List[ThreatIntelItem] = []


# -----------------------------------------------------------------------------
# 7. Website Maintenance Mode
# -----------------------------------------------------------------------------
class MaintenanceConfig(BaseModel):
    maintenance_enabled: bool = False
    maintenance_message: str = (
        "TrustGuard AI is temporarily undergoing scheduled maintenance. "
        "We are optimizing our security analysis engines and will be back shortly."
    )
    estimated_restore_time: Optional[str] = None
    internal_reason: Optional[str] = "Normal scheduled maintenance"
    updated_by: Optional[str] = "system"
    updated_at: Optional[datetime] = None


class MaintenanceUpdateRequest(BaseModel):
    maintenance_enabled: bool
    maintenance_message: Optional[str] = Field(
        None, max_length=500, description="Public announcement visible to visitors"
    )
    estimated_restore_time: Optional[str] = Field(
        None, max_length=100, description="Optional public estimated restoration date/time"
    )
    internal_reason: str = Field(..., min_length=4, max_length=500, description="Mandatory internal audit reason")


# -----------------------------------------------------------------------------
# 8. System Monitoring & Health
# -----------------------------------------------------------------------------
class ServiceHealthItem(BaseModel):
    service_name: str
    status: str = Field(..., description="OPERATIONAL | DEGRADED | UNAVAILABLE | NOT_CONFIGURED")
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    last_checked: datetime
    details: Optional[Dict[str, Any]] = None


class SystemHealthResponse(BaseModel):
    overall_status: str
    services: List[ServiceHealthItem]
    checked_at: datetime


# -----------------------------------------------------------------------------
# 9. Administrator Audit Logs
# -----------------------------------------------------------------------------
class AdminAuditLogItem(BaseModel):
    id: uuid.UUID
    admin_id: Optional[uuid.UUID] = None
    admin_username: str
    action: str
    target_resource: Optional[str] = None
    outcome: str = "SUCCESS"
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedAdminAuditLogs(BaseModel):
    items: List[AdminAuditLogItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# -----------------------------------------------------------------------------
# 10. Contributors Management
# -----------------------------------------------------------------------------
class ContributorSocialLinks(BaseModel):
    github: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    website: Optional[str] = None


class ContributorItem(BaseModel):
    id: str
    name: str
    role: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    social_links: ContributorSocialLinks = ContributorSocialLinks()
    display_order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ContributorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    role: str = Field(..., min_length=2, max_length=120)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None
    social_links: ContributorSocialLinks = ContributorSocialLinks()
    display_order: int = 0
    is_active: bool = True


class ContributorUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    social_links: Optional[ContributorSocialLinks] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class ContributorReorderItem(BaseModel):
    id: str
    display_order: int


class ContributorsPageConfig(BaseModel):
    title: str = "Project Contributors"
    subtitle: str = "The core developers, security researchers, and contributors powering TrustGuard AI."
    header_banner_url: Optional[str] = None
    is_published: bool = True
    show_in_navigation: bool = True
    updated_at: Optional[datetime] = None


class ContributorsPageConfigUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    header_banner_url: Optional[str] = None
    is_published: Optional[bool] = None
    show_in_navigation: Optional[bool] = None


# -----------------------------------------------------------------------------
# 11. Website Pages (CMS)
# -----------------------------------------------------------------------------
class WebsitePageItem(BaseModel):
    id: str
    title: str
    slug: str
    content: str
    meta_description: Optional[str] = None
    is_published: bool = True
    show_in_navigation: bool = False
    nav_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WebsitePageCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    slug: str = Field(..., min_length=2, max_length=100)
    content: str
    meta_description: Optional[str] = None
    is_published: bool = True
    show_in_navigation: bool = False
    nav_order: int = 0


class WebsitePageUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: Optional[bool] = None
    show_in_navigation: Optional[bool] = None
    nav_order: Optional[int] = None


# -----------------------------------------------------------------------------
# 12. Website Scans Management
# -----------------------------------------------------------------------------
class AdminScanItem(BaseModel):
    id: str
    url: str
    domain: Optional[str] = None
    classification: str = "UNKNOWN"
    trust_score: float = 0.0
    is_malicious: bool = False
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    scanned_at: datetime
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedAdminScans(BaseModel):
    items: List[AdminScanItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# -----------------------------------------------------------------------------
# 13. System Settings Configuration
# -----------------------------------------------------------------------------
class SystemSettingsConfig(BaseModel):
    site_name: str = "TrustGuard AI"
    site_tagline: str = "AI-Powered Phishing & Scam URL Detection"
    site_description: str = "Next-generation URL threat intelligence and automated cyber fraud protection."
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    announcement_enabled: bool = False
    announcement_message: Optional[str] = None
    announcement_type: str = "info"  # info | warning | critical
    announcement_link: Optional[str] = None
    allow_registration: bool = True
    allow_guest_scans: bool = True
    allow_community_reports: bool = True
    updated_at: Optional[datetime] = None


class SystemSettingsUpdate(BaseModel):
    site_name: Optional[str] = None
    site_tagline: Optional[str] = None
    site_description: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    announcement_enabled: Optional[bool] = None
    announcement_message: Optional[str] = None
    announcement_type: Optional[str] = None
    announcement_link: Optional[str] = None
    allow_registration: Optional[bool] = None
    allow_guest_scans: Optional[bool] = None
    allow_community_reports: Optional[bool] = None


