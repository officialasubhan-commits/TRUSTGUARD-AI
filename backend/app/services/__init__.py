"""
TrustGuard AI Services Module.
"""

from app.services.auth_service import AuthService
from app.services.community_reporting_service import (
    CommunityReportingService,
    get_community_service,
)
from app.services.ml_detection_service import MLDetectionService, get_ml_service
from app.services.risk_scoring_service import RiskScoringService, get_risk_scoring_service
from app.services.scan_history_service import ScanHistoryService, get_scan_history_service
from app.services.scan_service import ScanService
from app.services.ssl_tls_service import SSLValidationService, get_ssl_service
from app.services.threat_classifier import ThreatClassifier
from app.services.url_analyzer import URLAnalyzer
from app.services.url_validator import validate_url_static
from app.services.virustotal_service import VirusTotalService

__all__ = [
    "AuthService",
    "CommunityReportingService",
    "MLDetectionService",
    "RiskScoringService",
    "SSLValidationService",
    "ScanHistoryService",
    "ScanService",
    "ThreatClassifier",
    "URLAnalyzer",
    "VirusTotalService",
    "get_community_service",
    "get_ml_service",
    "get_risk_scoring_service",
    "get_scan_history_service",
    "get_ssl_service",
    "validate_url_static",
]
