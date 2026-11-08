"""
Automated Test Suite for TrustGuard AI Digital Trust Score & Intelligent Risk Assessment Engine.

Validates:
1. Multi-factor weighted score calculation (URL heuristics 15%, VT 40%, ML 30%, SSL 15%).
2. High-severity override rules (VirusTotal malicious, ML phishing, SSRF, obfuscation).
3. Dynamic weight redistribution and assessment coverage tracking.
4. Insufficient data threshold (< 30% coverage -> UNKNOWN / INSUFFICIENT_DATA).
5. Explainable indicator categorization (risk, positive, unknown).
6. Deterministic security recommendations.
7. End-to-end integration with POST /api/v1/scan and database persistence.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.schemas.ml import MLPredictionResponse
from app.schemas.scanner import PreliminaryAnalysis, PreliminaryIndicator
from app.schemas.ssl import SSLValidationResponse
from app.schemas.virustotal import (
    VirusTotalReportResponse,
    VirusTotalThreatClassification,
    VirusTotalVendorStats,
)
from app.services.risk_scoring_service import RiskScoringService

# --------------------------------------------------------------------------- #
# Helpers & Fixtures                                                          #
# --------------------------------------------------------------------------- #


def _make_clean_url_analysis() -> PreliminaryAnalysis:
    return PreliminaryAnalysis(
        risk_level="LOW_CONCERN",
        indicators=[],
        features={
            "url_length": 25,
            "domain_length": 12,
            "has_ip_address": False,
            "has_at_symbol": False,
            "uses_https": True,
            "subdomain_count": 0,
            "suspicious_keyword_count": 0,
        },
    )


def _make_clean_vt_report(url: str = "https://example.com") -> VirusTotalReportResponse:
    stats = VirusTotalVendorStats(
        harmless=75,
        undetected=10,
        malicious=0,
        suspicious=0,
        timeout=0,
    )
    return VirusTotalReportResponse(
        source="VirusTotal v3",
        status="NO_DETECTIONS",
        url=url,
        url_identifier="abc123clean",
        vt_subscore=98,
        statistics=stats,
        classification=VirusTotalThreatClassification(
            status="NO_DETECTIONS",
            detection_ratio="0/85",
            confidence="HIGH",
            threat_categories=[],
            flagged_vendors=[],
            summary="No security vendors flagged this URL as malicious or suspicious.",
        ),
        cached=False,
        message="Scan completed.",
    )


def _make_clean_ml_prediction(url: str = "https://example.com") -> MLPredictionResponse:
    return MLPredictionResponse(
        prediction="LIKELY_LEGITIMATE",
        phishing_probability=0.03,
        ml_subscore=97,
        confidence="HIGH",
        model_version="phishing_rf_v1.joblib",
        model_status="ACTIVE",
        indicators=["Standard registered domain name instead of raw IP host."],
        summary="Machine learning model evaluated structural features with low phishing likelihood.",
    )


def _make_clean_ssl_analysis(domain: str = "example.com") -> SSLValidationResponse:
    return SSLValidationResponse(
        status="VALID",
        https_enabled=True,
        hostname=domain,
        hostname_verified=True,
        certificate_trusted=True,
        certificate_issuer="Let's Encrypt Authority X3",
        valid_from=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc),
        days_remaining=90,
        tls_version="TLSv1.3",
        cipher="TLS_AES_256_GCM_SHA384",
        ssl_subscore=95,
        findings=["Certificate is valid and trusted."],
        message="Valid SSL/TLS certificate.",
        cached=False,
    )


# --------------------------------------------------------------------------- #
# Unit Tests for RiskScoringService                                           #
# --------------------------------------------------------------------------- #


def test_scoring_all_modules_clean_legitimate_url() -> None:
    """When all 4 modules are active and report zero risk, trust score is >= 90 (LOW RISK)."""
    scorer = RiskScoringService()
    assessment = scorer.evaluate(
        url="https://example.com",
        url_analysis=_make_clean_url_analysis(),
        vt_report=_make_clean_vt_report("https://example.com"),
        ml_prediction=_make_clean_ml_prediction("https://example.com"),
        ssl_analysis=_make_clean_ssl_analysis("example.com"),
    )

    assert assessment.digital_trust_score is not None
    assert assessment.digital_trust_score >= 90
    assert assessment.risk_level == "LOW"
    assert assessment.risk_label == "LOW RISK"
    assert assessment.assessment_status == "COMPLETE"
    assert assessment.assessment_coverage == 1.0
    assert assessment.coverage_percentage == 100
    assert assessment.high_severity_override is False
    assert len(assessment.positive_indicators) >= 3
    assert len(assessment.risk_indicators) == 0


def test_scoring_high_severity_override_virustotal_malicious() -> None:
    """VirusTotal >= 3 malicious engines triggers high-severity override (CRITICAL/HIGH risk)."""
    scorer = RiskScoringService()

    bad_vt_stats = VirusTotalVendorStats(
        harmless=20,
        undetected=10,
        malicious=6,
        suspicious=2,
    )
    bad_vt_report = VirusTotalReportResponse(
        source="VirusTotal v3",
        status="MALICIOUS",
        url="https://malicious-phish-domain.xyz",
        url_identifier="bad123",
        vt_subscore=0,
        statistics=bad_vt_stats,
        classification=VirusTotalThreatClassification(
            status="MALICIOUS",
            detection_ratio="6/38",
            confidence="HIGH",
            threat_categories=["phishing", "malware"],
            flagged_vendors=["Google Safe Browsing", "Kaspersky"],
            summary="Flagged by 6 security engines as malicious.",
        ),
        cached=False,
        message="VirusTotal malicious threat detected.",
    )

    assessment = scorer.evaluate(
        url="https://malicious-phish-domain.xyz",
        url_analysis=_make_clean_url_analysis(),
        vt_report=bad_vt_report,
        ml_prediction=_make_clean_ml_prediction("https://malicious-phish-domain.xyz"),
        ssl_analysis=_make_clean_ssl_analysis("malicious-phish-domain.xyz"),
    )

    assert assessment.high_severity_override is True
    assert assessment.override_reason is not None
    assert "VirusTotal" in assessment.override_reason
    assert assessment.digital_trust_score is not None
    assert assessment.digital_trust_score <= 15
    assert assessment.risk_level in ("HIGH", "CRITICAL")
    assert any(
        item.source_module == "virustotal" and item.severity in ("high", "critical")
        for item in assessment.risk_indicators
    )


def test_scoring_high_severity_override_ml_phishing() -> None:
    """ML phishing probability >= 0.85 triggers high-severity override even if other signals are neutral."""
    scorer = RiskScoringService()

    ml_phishing = MLPredictionResponse(
        prediction="PHISHING",
        phishing_probability=0.94,
        ml_subscore=6,
        confidence="HIGH",
        model_version="phishing_rf_v1.joblib",
        model_status="ACTIVE",
        indicators=["Extremely long domain containing brand spoofing terms."],
        summary="High-confidence phishing indicators detected.",
    )

    assessment = scorer.evaluate(
        url="https://secure-login-paypal.com.account-update.xyz",
        url_analysis=_make_clean_url_analysis(),
        vt_report=_make_clean_vt_report(),
        ml_prediction=ml_phishing,
        ssl_analysis=_make_clean_ssl_analysis(),
    )

    assert assessment.high_severity_override is True
    assert assessment.override_reason is not None
    assert "machine learning" in assessment.override_reason.lower()
    assert assessment.digital_trust_score is not None
    assert assessment.digital_trust_score <= 25
    assert assessment.risk_level in ("HIGH", "CRITICAL")


def test_scoring_high_severity_override_ssrf_destination() -> None:
    """SSRF private/metadata destination forces Trust Score to 0 and CRITICAL risk."""
    scorer = RiskScoringService()

    ssrf_ssl = SSLValidationResponse(
        status="UNSAFE_DESTINATION",
        https_enabled=True,
        hostname="169.254.169.254",
        findings=["Target destination resolves to prohibited cloud metadata or internal network."],
        message="SSRF destination prohibited.",
    )

    assessment = scorer.evaluate(
        url="https://169.254.169.254/latest/meta-data",
        url_analysis=_make_clean_url_analysis(),
        vt_report=_make_clean_vt_report(),
        ml_prediction=_make_clean_ml_prediction(),
        ssl_analysis=ssrf_ssl,
    )

    assert assessment.high_severity_override is True
    assert assessment.override_reason is not None
    assert "private, loopback, or cloud metadata" in assessment.override_reason
    assert assessment.digital_trust_score == 0
    assert assessment.risk_level == "CRITICAL"


def test_scoring_high_severity_override_ip_and_at_obfuscation() -> None:
    """Combining raw IP host and @ symbol credential obfuscation triggers override."""
    scorer = RiskScoringService()

    indicators = [
        PreliminaryIndicator(
            name="IP_BASED_HOSTNAME",
            description="URL uses raw IP host.",
            severity="high",
            evidence="192.0.2.1",
            reason="Commonly used to bypass domain reputation checks.",
        ),
        PreliminaryIndicator(
            name="AT_SYMBOL_OBFUSCATION",
            description="URL contains @ symbol.",
            severity="high",
            evidence="@",
            reason="Browser ignores everything before the @ sign.",
        ),
    ]
    url_analysis = PreliminaryAnalysis(
        risk_level="HIGH_CONCERN",
        indicators=indicators,
        features={"has_ip_address": True, "has_at_symbol": True},
    )

    assessment = scorer.evaluate(
        url="http://legitimate.com@192.0.2.1/login",
        url_analysis=url_analysis,
        vt_report=None,
        ml_prediction=None,
        ssl_analysis=None,
    )

    assert assessment.high_severity_override is True
    assert assessment.override_reason is not None
    assert "deception mechanisms" in assessment.override_reason
    assert assessment.digital_trust_score is not None
    assert assessment.digital_trust_score <= 20
    assert assessment.risk_level in ("HIGH", "CRITICAL")


def test_scoring_ssl_expired_or_mismatch() -> None:
    """Invalid SSL certificate (expired / mismatch) heavily penalizes the score and generates risk indicators."""
    scorer = RiskScoringService()

    expired_ssl = SSLValidationResponse(
        status="EXPIRED",
        https_enabled=True,
        hostname="expired-site.com",
        hostname_verified=True,
        certificate_trusted=False,
        valid_until=datetime(2020, 1, 1, tzinfo=timezone.utc),
        days_remaining=-1000,
        ssl_subscore=0,
        findings=["Certificate expired 1000 days ago."],
        message="SSL certificate has expired.",
    )

    assessment = scorer.evaluate(
        url="https://expired-site.com",
        url_analysis=_make_clean_url_analysis(),
        vt_report=_make_clean_vt_report(),
        ml_prediction=_make_clean_ml_prediction(),
        ssl_analysis=expired_ssl,
    )

    assert assessment.digital_trust_score is not None
    # With clean signals on VT (40%), ML (30%), URL (15%), but SSL (15%) at 0:
    # Weighted risk = 0.15 * 90 = 13.5 + ML (0.9) = 14.4 -> trust score ~86
    assert assessment.digital_trust_score <= 88
    assert any("expired" in ind.title.lower() for ind in assessment.risk_indicators)


def test_scoring_plain_http_website() -> None:
    """Plain HTTP website incurs SSL penalty and unencrypted communications indicator."""
    scorer = RiskScoringService()

    http_ssl = SSLValidationResponse(
        status="HTTPS_NOT_USED",
        https_enabled=False,
        hostname="plain-http-site.com",
        ssl_subscore=20,
        findings=["Website uses unencrypted HTTP protocol."],
        message="Plain HTTP.",
    )

    assessment = scorer.evaluate(
        url="http://plain-http-site.com",
        url_analysis=_make_clean_url_analysis(),
        vt_report=_make_clean_vt_report(),
        ml_prediction=_make_clean_ml_prediction(),
        ssl_analysis=http_ssl,
    )

    assert assessment.digital_trust_score is not None
    assert assessment.digital_trust_score <= 95
    assert any("Unencrypted" in ind.title for ind in assessment.risk_indicators)


def test_scoring_partial_coverage_virustotal_unavailable() -> None:
    """When VirusTotal is unavailable (missing key / rate-limited), dynamic weight redistribution applies."""
    scorer = RiskScoringService()

    vt_unavailable = VirusTotalReportResponse(
        source="VirusTotal v3",
        status="API_UNAVAILABLE",
        url="https://example.com",
        url_identifier="abc123",
        vt_subscore=50,
        statistics=VirusTotalVendorStats(),
        classification=VirusTotalThreatClassification(
            status="API_UNAVAILABLE",
            detection_ratio="0/0",
            confidence="LOW",
            threat_categories=[],
            flagged_vendors=[],
            summary="API key missing or disabled.",
        ),
        cached=False,
        message="VT unavailable.",
    )

    assessment = scorer.evaluate(
        url="https://example.com",
        url_analysis=_make_clean_url_analysis(),
        vt_report=vt_unavailable,
        ml_prediction=_make_clean_ml_prediction(),
        ssl_analysis=_make_clean_ssl_analysis(),
    )

    # Remaining weights: URL (0.15), ML (0.30), SSL (0.15) = 0.60
    assert assessment.assessment_coverage == 0.60
    assert assessment.coverage_percentage == 60
    assert assessment.assessment_status == "PARTIAL"
    assert assessment.digital_trust_score is not None
    # Excluded module flagged in unknown_indicators
    assert any("VirusTotal" in ind.title for ind in assessment.unknown_indicators)


def test_scoring_insufficient_data() -> None:
    """When available weight is below 30% threshold, returns INSUFFICIENT_DATA and None trust score."""
    scorer = RiskScoringService()

    # Only URL analysis available (weight 0.15 < 0.30 min threshold)
    assessment = scorer.evaluate(
        url="https://barebones-unknown.com",
        url_analysis=_make_clean_url_analysis(),
        vt_report=None,
        ml_prediction=None,
        ssl_analysis=None,
    )

    assert assessment.assessment_status == "INSUFFICIENT_DATA"
    assert assessment.digital_trust_score is None
    assert assessment.risk_score is None
    assert assessment.risk_level == "UNKNOWN"
    assert assessment.risk_label == "INSUFFICIENT DATA"
    assert assessment.assessment_coverage == 0.15
    assert len(assessment.recommendations) > 0


def test_scoring_explainable_indicators_categorization() -> None:
    """Verifies that positive, risk, and unknown indicators are appropriately separated."""
    scorer = RiskScoringService()

    indicators = [
        PreliminaryIndicator(
            name="SUSPICIOUS_KEYWORDS",
            description="URL path contains password-reset keyword.",
            severity="medium",
            evidence="password-reset",
            reason="Phishing URLs frequently spoof recovery pages.",
        )
    ]
    url_analysis = PreliminaryAnalysis(
        risk_level="MODERATE_CONCERN",
        indicators=indicators,
        features={"suspicious_keyword_count": 1},
    )

    assessment = scorer.evaluate(
        url="https://my-portal.com/password-reset",
        url_analysis=url_analysis,
        vt_report=_make_clean_vt_report(),
        ml_prediction=_make_clean_ml_prediction(),
        ssl_analysis=_make_clean_ssl_analysis(),
    )

    # Check risk indicators contain the keyword finding
    assert any(
        "SUSPICIOUS_KEYWORDS" in ind.title or "Keyword" in ind.title
        for ind in assessment.risk_indicators
    )
    # Positive indicators contain SSL / ML / VT clean findings
    assert len(assessment.positive_indicators) >= 2


def test_scoring_deterministic_recommendations() -> None:
    """Critical threats generate urgent blocking recommendations; legitimate sites generate safe browsing tips."""
    scorer = RiskScoringService()

    # Case A: Critical
    bad_vt = VirusTotalReportResponse(
        source="VirusTotal v3",
        status="MALICIOUS",
        url="https://danger.xyz",
        url_identifier="danger",
        vt_subscore=0,
        statistics=VirusTotalVendorStats(malicious=10, harmless=0, total_engines=10),
        classification=VirusTotalThreatClassification(
            status="MALICIOUS",
            detection_ratio="10/10",
            confidence="HIGH",
            threat_categories=["malware"],
            flagged_vendors=[],
            summary="Malware detected.",
        ),
        cached=False,
    )
    crit_assessment = scorer.evaluate(
        url="https://danger.xyz",
        url_analysis=_make_clean_url_analysis(),
        vt_report=bad_vt,
        ml_prediction=_make_clean_ml_prediction(),
        ssl_analysis=_make_clean_ssl_analysis(),
    )
    assert any("passwords" in rec.lower() for rec in crit_assessment.recommendations)

    # Case B: Low Risk
    safe_assessment = scorer.evaluate(
        url="https://example.com",
        url_analysis=_make_clean_url_analysis(),
        vt_report=_make_clean_vt_report(),
        ml_prediction=_make_clean_ml_prediction(),
        ssl_analysis=_make_clean_ssl_analysis(),
    )
    assert any("technical checks passed" in rec.lower() for rec in safe_assessment.recommendations)


# --------------------------------------------------------------------------- #
# End-to-End API and Integration Tests                                        #
# --------------------------------------------------------------------------- #


def test_scan_api_endpoint_returns_complete_trust_assessment(client: TestClient) -> None:
    """POST /api/v1/scan returns complete Digital Trust Score and structured trust assessment."""
    response = client.post(
        "/api/v1/scan",
        json={"url": "https://python.org", "guest": True},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "trust_assessment" in data
    assert data["trust_assessment"] is not None

    assessment = data["trust_assessment"]
    assert "digital_trust_score" in assessment
    assert "risk_level" in assessment
    assert "module_scores" in assessment
    assert "assessment_coverage" in assessment
    assert assessment["assessment_coverage"] > 0.0

    # Top-level convenience fields
    assert "digital_trust_score" in data
    assert "risk_level" in data
    assert data["digital_trust_score"] == assessment["digital_trust_score"]
    assert data["risk_level"] == assessment["risk_level"]


def test_database_persistence_of_trust_assessment(client: TestClient) -> None:
    """Verifies that scan_history and scan_results record the synthesized trust score."""
    scan_resp = client.post(
        "/api/v1/scan",
        json={"url": "https://fastapi.tiangolo.com", "guest": True},
    )
    assert scan_resp.status_code == 201
    scan_id = scan_resp.json()["scan_id"]

    # Retrieve scan details
    details_resp = client.get(f"/api/v1/scan/{scan_id}")
    assert details_resp.status_code == 200
    details = details_resp.json()

    # Scan history check
    assert "scan" in details
    assert details["scan"]["scan_status"] == "complete"
    assert details["scan"]["trust_score"] is not None
    assert details["scan"]["risk_level"] is not None

    # Scan results check
    assert "result" in details
    assert details["result"] is not None
    assert details["result"]["trust_score"] == details["scan"]["trust_score"]
    assert "score_breakdown" in details["result"]
    assert "module_scores" in details["result"]["score_breakdown"]
