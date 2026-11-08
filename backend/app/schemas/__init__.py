"""
Pydantic schemas package for TrustGuard AI.
"""

from app.schemas.auth import (
    AuthMessageResponse,
    AuthTokenResponse,
    AuthUserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenRefreshRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.health import HealthResponse
from app.schemas.report import (
    CommunityReportAdminResponse,
    CommunityReportCreate,
    CommunityReportModerationUpdate,
    CommunityReportPublicResponse,
    CommunityReportResponse,
    CommunityReportUserResponse,
    PaginatedCommunityReports,
    ReportReasonType,
    ReportStatusType,
    ThreatCategoryType,
    VerificationStatusType,
)
from app.schemas.scan import (
    RiskCategory,
    ScanCreate,
    ScanDetailResponse,
    ScanHistoryResponse,
    ScanResultCreate,
    ScanResultResponse,
    ScanStatusType,
    ScanStatusUpdate,
)
from app.schemas.scanner import (
    PreliminaryAnalysis,
    PreliminaryIndicator,
    PreliminaryRiskLevel,
    URLSubmissionResponse,
)
from app.schemas.threat_intel import (
    SeverityType,
    ThreatIntelCreate,
    ThreatIntelResponse,
    ThreatSourceType,
)
from app.schemas.user import UserBase, UserCreate, UserProfileResponse, UserUpdate

__all__ = [
    "HealthResponse",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserProfileResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenRefreshRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "AuthTokenResponse",
    "AuthUserResponse",
    "AuthMessageResponse",
    "RiskCategory",
    "ScanStatusType",
    "ScanCreate",
    "ScanStatusUpdate",
    "ScanResultCreate",
    "ScanResultResponse",
    "ScanHistoryResponse",
    "ScanDetailResponse",
    "PreliminaryRiskLevel",
    "PreliminaryIndicator",
    "PreliminaryAnalysis",
    "URLSubmissionResponse",
    "ReportReasonType",
    "ReportStatusType",
    "ThreatCategoryType",
    "VerificationStatusType",
    "CommunityReportCreate",
    "CommunityReportResponse",
    "CommunityReportPublicResponse",
    "CommunityReportUserResponse",
    "CommunityReportAdminResponse",
    "CommunityReportModerationUpdate",
    "PaginatedCommunityReports",
    "SeverityType",
    "ThreatSourceType",
    "ThreatIntelCreate",
    "ThreatIntelResponse",
]
