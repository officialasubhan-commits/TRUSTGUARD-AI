"""
Automated test suite for VirusTotal API Integration & Threat Intelligence Engine.

Verifies:
1. URL identifier base64url calculation (RFC 4648 without padding).
2. Threat classifier decision matrix (MALICIOUS, SUSPICIOUS, NO_DETECTIONS, NOT_FOUND).
3. VirusTotal service handling of clean, malicious, and suspicious URLs.
4. Absence of detections != safe disclaimer enforcement.
5. In-memory response caching and TTL behavior.
6. Rate limiting (429) and authentication failure (401/403) graceful handling.
7. Unseen URL submission (404 -> POST /urls) and async polling behavior.
8. Database persistence to scan_results and threat_reports tables.
9. Threat intelligence API endpoints (GET /api/v1/threat-intelligence/{scan_id} and /lookup).
"""

from __future__ import annotations

import base64
import uuid
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.database.repositories.scan_repo import ScanRepository
from app.database.repositories.threat_repo import ThreatRepository
from app.main import app
from app.schemas.virustotal import VirusTotalVendorStats
from app.services.auth_service import _generate_mock_jwt
from app.services.threat_classifier import ThreatClassifier
from app.services.virustotal_service import VirusTotalService

# ==============================================================================
# 1. URL IDENTIFIER TESTS
# ==============================================================================


def test_url_identifier_computation():
    """Verify base64url encoding without padding as required by VirusTotal v3."""
    url = "https://example.com/test"
    expected = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
    assert VirusTotalService.get_url_identifier(url) == expected
    assert "=" not in VirusTotalService.get_url_identifier(url)

    # Idempotent and deterministic
    assert VirusTotalService.get_url_identifier(url) == VirusTotalService.get_url_identifier(url)


# ==============================================================================
# 2. THREAT CLASSIFIER LOGIC TESTS
# ==============================================================================


def test_threat_classifier_malicious_threshold():
    """Verify >= 3 engines flagged as malicious results in MALICIOUS classification."""
    stats = VirusTotalVendorStats(
        malicious=4,
        suspicious=1,
        harmless=60,
        undetected=10,
        timeout=0,
        total_engines=75,
    )
    engine_results = {
        "Kaspersky": {"category": "malicious", "result": "phishing"},
        "Sophos": {"category": "malicious", "result": "malware"},
        "Fortinet": {"category": "malicious", "result": "malicious site"},
        "CleanMX": {"category": "malicious", "result": "cleanmx"},
    }

    classification, subscore = ThreatClassifier.classify(stats, engine_results)

    assert classification.status == "MALICIOUS"
    assert classification.detection_ratio == "4/75"
    assert classification.confidence in ("HIGH", "MEDIUM")
    assert "phishing" in classification.threat_categories
    assert "Kaspersky" in classification.flagged_vendors
    assert subscore <= 50  # Significantly penalized
    assert "NO_DETECTIONS" not in classification.summary
    assert "safe" in classification.safety_disclaimer.lower()


def test_threat_classifier_suspicious_threshold():
    """Verify 1-2 malicious or multiple suspicious engines results in SUSPICIOUS."""
    stats = VirusTotalVendorStats(
        malicious=1,
        suspicious=2,
        harmless=65,
        undetected=7,
        timeout=0,
        total_engines=75,
    )
    engine_results = {
        "VendorA": {"category": "malicious", "result": "suspicious link"},
        "VendorB": {"category": "suspicious", "result": "unrated"},
        "VendorC": {"category": "suspicious", "result": ""},
    }

    classification, subscore = ThreatClassifier.classify(stats, engine_results)

    assert classification.status == "SUSPICIOUS"
    assert classification.detection_ratio == "1/75"
    assert classification.confidence == "MEDIUM"
    assert 20 <= subscore <= 80


def test_threat_classifier_no_detections():
    """
    Verify 0 malicious and 0 suspicious yields NO_DETECTIONS and 100 subscore,
    while retaining the explicit security disclaimer that NO_DETECTIONS != SAFE.
    """
    stats = VirusTotalVendorStats(
        malicious=0,
        suspicious=0,
        harmless=70,
        undetected=5,
        timeout=0,
        total_engines=75,
    )

    classification, subscore = ThreatClassifier.classify(stats)

    assert classification.status == "NO_DETECTIONS"
    assert classification.detection_ratio == "0/75"
    assert subscore == 100
    assert "Zero security vendors" in classification.summary
    # Critical requirement: explicit disclaimer
    assert (
        "Absence of detections (NO_DETECTIONS) does not guarantee that a website is safe"
        in classification.safety_disclaimer
    )


def test_threat_classifier_not_found():
    """Verify 0 total engines yields NOT_FOUND classification."""
    stats = VirusTotalVendorStats(total_engines=0)
    classification, subscore = ThreatClassifier.classify(stats)

    assert classification.status == "NOT_FOUND"
    assert classification.confidence == "INSUFFICIENT"
    assert subscore == 100


# ==============================================================================
# 3. VIRUSTOTAL SERVICE UNIT TESTS WITH MOCKED HTTP
# ==============================================================================


@pytest.mark.asyncio
async def test_virustotal_service_missing_api_key():
    """Verify graceful API_UNAVAILABLE fallback when API key is missing or placeholder."""
    service = VirusTotalService(api_key="")
    report = await service.lookup_url("https://example.com/test-no-key")

    assert report.status == "API_UNAVAILABLE"
    assert report.vt_subscore == 100
    assert "not configured" in report.message.lower()
    assert report.statistics.total_engines == 0


@pytest.mark.asyncio
async def test_virustotal_service_successful_lookup():
    """Verify successful 200 OK parsing and threat classification."""
    url = "https://phishing-portal.com/login"
    mock_vt_response = {
        "data": {
            "attributes": {
                "last_analysis_stats": {
                    "malicious": 8,
                    "suspicious": 2,
                    "harmless": 50,
                    "undetected": 10,
                    "timeout": 0,
                },
                "last_analysis_results": {
                    "Google Safebrowsing": {"category": "malicious", "result": "phishing"},
                    "Kaspersky": {"category": "malicious", "result": "phishing"},
                    "Sophos": {"category": "malicious", "result": "malware"},
                },
                "last_analysis_date": 1700000000,
            }
        }
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        status_code=200,
        json=mock_vt_response,
        request=httpx.Request("GET", "https://www.virustotal.com/api/v3/urls/dummy"),
    )
    mock_client.get.return_value = mock_resp

    service = VirusTotalService(api_key="real-test-api-key-12345", http_client=mock_client)
    report = await service.lookup_url(url)

    assert report.status == "MALICIOUS"
    assert report.statistics.malicious == 8
    assert report.statistics.total_engines == 70
    assert report.classification.detection_ratio == "8/70"
    assert "phishing" in report.classification.threat_categories
    assert "Google Safebrowsing" in report.classification.flagged_vendors
    assert report.vt_subscore <= 30
    assert report.cached is False


@pytest.mark.asyncio
async def test_virustotal_service_in_memory_caching():
    """Verify that a second lookup for the same URL hits local cache without second HTTP call."""
    url = "https://cached-domain.com/"
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        status_code=200,
        json={
            "data": {
                "attributes": {
                    "last_analysis_stats": {
                        "malicious": 0,
                        "suspicious": 0,
                        "harmless": 65,
                        "undetected": 5,
                        "timeout": 0,
                    },
                    "last_analysis_results": {},
                    "last_analysis_date": 1700000000,
                }
            }
        },
        request=httpx.Request("GET", "https://www.virustotal.com/api/v3/urls/dummy"),
    )
    mock_client.get.return_value = mock_resp

    service = VirusTotalService(api_key="valid-api-key-123", http_client=mock_client)

    # First lookup: hits HTTP client
    report1 = await service.lookup_url(url)
    assert report1.cached is False
    assert mock_client.get.call_count == 1

    # Second lookup: must be served from cache
    report2 = await service.lookup_url(url)
    assert report2.cached is True
    # HTTP client was NOT called again
    assert mock_client.get.call_count == 1


@pytest.mark.asyncio
async def test_virustotal_service_rate_limit_429():
    """Verify HTTP 429 response is gracefully mapped to RATE_LIMITED without crashing."""
    url = "https://rate-limited-test.com/"
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        status_code=429,
        text="Quota exceeded",
        request=httpx.Request("GET", "https://www.virustotal.com/api/v3/urls/dummy"),
    )
    mock_client.get.return_value = mock_resp

    service = VirusTotalService(api_key="valid-key", http_client=mock_client)
    report = await service.lookup_url(url)

    assert report.status == "RATE_LIMITED"
    assert report.classification.status == "RATE_LIMITED"
    assert "rate limit" in report.message.lower()


@pytest.mark.asyncio
async def test_virustotal_service_unauthorized_401():
    """Verify HTTP 401 response is gracefully mapped to API_UNAVAILABLE."""
    url = "https://auth-fail.com/"
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        status_code=401,
        text="Wrong API key",
        request=httpx.Request("GET", "https://www.virustotal.com/api/v3/urls/dummy"),
    )
    mock_client.get.return_value = mock_resp

    service = VirusTotalService(api_key="invalid-key", http_client=mock_client)
    report = await service.lookup_url(url)

    assert report.status == "API_UNAVAILABLE"
    assert "authentication failed" in report.message.lower()


@pytest.mark.asyncio
async def test_virustotal_service_timeout_handling():
    """Verify network timeout raises no unhandled exception and yields ERROR status."""
    url = "https://timeout-test.com/"
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")

    service = VirusTotalService(api_key="valid-key", http_client=mock_client)
    report = await service.lookup_url(url)

    assert report.status == "ERROR"
    assert "timed out" in report.message.lower()


@pytest.mark.asyncio
async def test_virustotal_service_404_submission():
    """Verify 404 triggers asynchronous submission to POST /urls."""
    url = "https://brand-new-site.org/register"
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # GET returns 404
    mock_get_resp = httpx.Response(
        status_code=404,
        json={"error": {"code": "NotFoundError"}},
        request=httpx.Request("GET", "https://www.virustotal.com/api/v3/urls/dummy"),
    )
    mock_client.get.return_value = mock_get_resp

    # POST returns 200 with analysis ID
    mock_post_resp = httpx.Response(
        status_code=200,
        json={"data": {"id": "u-dummyanalysisid-12345", "type": "analysis"}},
        request=httpx.Request("POST", "https://www.virustotal.com/api/v3/urls"),
    )
    mock_client.post.return_value = mock_post_resp

    service = VirusTotalService(api_key="valid-key", http_client=mock_client)
    report = await service.lookup_url(url)

    assert report.status == "PENDING"
    assert "queued" in report.message.lower()
    assert mock_client.post.call_count == 1


@pytest.mark.asyncio
async def test_virustotal_service_database_persistence():
    """Verify that when a scan_id is provided, findings are persisted to threat_reports."""
    scan_id = uuid.uuid4()
    url = "https://malicious-test-site.net/login"

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        status_code=200,
        json={
            "data": {
                "attributes": {
                    "last_analysis_stats": {
                        "malicious": 5,
                        "suspicious": 1,
                        "harmless": 40,
                        "undetected": 10,
                        "timeout": 0,
                    },
                    "last_analysis_results": {
                        "Kaspersky": {"category": "malicious", "result": "phishing"},
                    },
                    "last_analysis_date": 1700000000,
                }
            }
        },
        request=httpx.Request("GET", "https://www.virustotal.com/api/v3/urls/dummy"),
    )
    mock_client.get.return_value = mock_resp

    threat_repo = ThreatRepository()
    scan_repo = ScanRepository()
    service = VirusTotalService(
        api_key="valid-key",
        http_client=mock_client,
        threat_repo=threat_repo,
        scan_repo=scan_repo,
    )

    report = await service.lookup_url(url, scan_id=scan_id)
    assert report.status == "MALICIOUS"

    # Verify record was stored in repository
    records = await threat_repo.get_threat_records_by_url(url)
    assert len(records) >= 1
    assert records[0].threat_source == "virustotal"
    assert records[0].severity in ("high", "critical")


# ==============================================================================
# 4. API ENDPOINT TESTS
# ==============================================================================


def test_threat_intelligence_lookup_endpoint():
    """Verify GET /api/v1/threat-intelligence/lookup endpoint."""
    client = TestClient(app)
    response = client.get(
        "/api/v1/threat-intelligence/lookup?url=https://example.com/test-endpoint"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "VirusTotal v3"
    assert "status" in data
    assert "statistics" in data
    assert "classification" in data
    assert "url_identifier" in data


def test_threat_intelligence_by_scan_id_endpoint():
    """Verify GET /api/v1/threat-intelligence/{scan_id} endpoint."""
    client = TestClient(app)

    # 1. Submit a guest scan first
    submit_resp = client.post("/api/v1/scan", json={"url": "https://threat-test-sample.org/path"})
    assert submit_resp.status_code == 201
    scan_id = submit_resp.json()["scan_id"]

    # 2. Query threat intelligence by scan_id
    ti_resp = client.get(f"/api/v1/threat-intelligence/{scan_id}")
    assert ti_resp.status_code == 200
    ti_data = ti_resp.json()

    assert ti_data["scan_id"] == scan_id
    assert ti_data["url"] == "https://threat-test-sample.org/path"
    assert "classification" in ti_data
    assert "safety_disclaimer" in ti_data["classification"]


def test_threat_intelligence_ownership_isolation():
    """Verify authenticated user private scans cannot be accessed by other users."""
    client = TestClient(app)
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    token_a = _generate_mock_jwt(user_a_id, "usera@example.com")
    token_b = _generate_mock_jwt(user_b_id, "userb@example.com")

    # User A creates a scan
    headers_a = {"Authorization": f"Bearer {token_a}"}
    submit_resp = client.post(
        "/api/v1/scan", json={"url": "https://private-user-a.com/"}, headers=headers_a
    )
    assert submit_resp.status_code == 201
    scan_id = submit_resp.json()["scan_id"]

    # User A can access it
    ok_resp = client.get(f"/api/v1/threat-intelligence/{scan_id}", headers=headers_a)
    assert ok_resp.status_code == 200

    # User B cannot access User A's scan (403 Forbidden)
    headers_b = {"Authorization": f"Bearer {token_b}"}
    forbidden_resp = client.get(f"/api/v1/threat-intelligence/{scan_id}", headers=headers_b)
    assert forbidden_resp.status_code == 403
