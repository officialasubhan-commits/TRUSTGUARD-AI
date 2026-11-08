"""
Automated Test Suite for Scan History, Detailed Reporting, Filtering, Sorting,
Statistics, and Security Report Management.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.database.repositories.scan_repo import _mock_results_store, _mock_scans_store
from app.services.auth_service import _generate_mock_jwt


def _create_auth_headers(user_id: uuid.UUID, email: str = "history_tester@trustguard.ai") -> dict:
    token = _generate_mock_jwt(user_id, email)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. SCAN HISTORY RETRIEVAL & PAGINATION TESTS
# ==============================================================================


def test_user_with_no_scans_receives_empty_history(client: TestClient):
    """Authenticated user with zero scans receives a valid empty paginated list."""
    empty_user_id = uuid.uuid4()
    headers = _create_auth_headers(empty_user_id, "empty_user@trustguard.ai")

    response = client.get("/api/v1/scans", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_items"] == 0
    assert data["total_pages"] == 0
    assert data["current_page"] == 1
    assert data["has_next"] is False
    assert data["has_prev"] is False
    assert data["items"] == []


def test_authenticated_user_retrieves_own_scans_and_pagination(client: TestClient):
    """Verify pagination mechanics and that users retrieve only their own non-guest scans."""
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    headers_a = _create_auth_headers(user_a, "user_a@trustguard.ai")

    # Clear mock stores for predictable pagination testing
    _mock_scans_store.clear()
    _mock_results_store.clear()

    # Populate 15 scans for user A over different domains
    for i in range(15):
        _mock_scans_store[uuid.uuid4()] = {
            "id": uuid.uuid4(),
            "user_id": user_a,
            "submitted_url": f"https://domain-{i:02d}.com/page",
            "normalized_url": f"https://domain-{i:02d}.com/page",
            "domain": f"domain-{i:02d}.com",
            "url_hash": f"hash_{i:02d}",
            "scan_status": "complete",
            "risk_level": "LOW" if i % 2 == 0 else "HIGH",
            "trust_score": 90 if i % 2 == 0 else 25,
            "risk_score": 10 if i % 2 == 0 else 75,
            "assessment_status": "COMPLETE",
            "assessment_coverage": 1.0,
            "scoring_version": "v1.0.0",
            "is_guest": False,
            "created_at": datetime.now(timezone.utc) - timedelta(minutes=i),
            "completed_at": datetime.now(timezone.utc),
        }

    # Add 3 scans for user B (should not appear in user A's queries)
    for j in range(3):
        _mock_scans_store[uuid.uuid4()] = {
            "id": uuid.uuid4(),
            "user_id": user_b,
            "submitted_url": f"https://user-b-{j}.com/",
            "normalized_url": f"https://user-b-{j}.com/",
            "domain": f"user-b-{j}.com",
            "url_hash": f"hash_b_{j}",
            "scan_status": "complete",
            "risk_level": "LOW",
            "trust_score": 95,
            "risk_score": 5,
            "is_guest": False,
            "created_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
        }

    # Page 1: 10 items
    res_p1 = client.get("/api/v1/scans?page=1&page_size=10", headers=headers_a)
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert data_p1["total_items"] == 15
    assert data_p1["total_pages"] == 2
    assert data_p1["current_page"] == 1
    assert data_p1["page_size"] == 10
    assert data_p1["has_next"] is True
    assert data_p1["has_prev"] is False
    assert len(data_p1["items"]) == 10

    # Page 2: remaining 5 items
    res_p2 = client.get("/api/v1/scans?page=2&page_size=10", headers=headers_a)
    assert res_p2.status_code == 200
    data_p2 = res_p2.json()
    assert data_p2["total_items"] == 15
    assert data_p2["current_page"] == 2
    assert data_p2["has_next"] is False
    assert data_p2["has_prev"] is True
    assert len(data_p2["items"]) == 5


# ==============================================================================
# 2. SEARCH, FILTERING & SORTING TESTS
# ==============================================================================


def test_scan_history_search_by_domain_and_url(client: TestClient):
    """Verify keyword search across domain and submitted URL."""
    user_id = uuid.uuid4()
    headers = _create_auth_headers(user_id)
    _mock_scans_store.clear()

    # Seed 3 distinct scans
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://paypal-security-alert.xyz/verify",
        "normalized_url": "https://paypal-security-alert.xyz/verify",
        "domain": "paypal-security-alert.xyz",
        "scan_status": "complete",
        "risk_level": "CRITICAL",
        "trust_score": 10,
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
    }
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://github.com/torvalds/linux",
        "normalized_url": "https://github.com/torvalds/linux",
        "domain": "github.com",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 98,
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
    }

    # Search for paypal
    res_pp = client.get("/api/v1/scans?search=paypal", headers=headers)
    assert res_pp.status_code == 200
    data_pp = res_pp.json()
    assert data_pp["total_items"] == 1
    assert "paypal" in data_pp["items"][0]["domain"].lower()

    # Search for linux
    res_lx = client.get("/api/v1/scans?search=linux", headers=headers)
    assert res_lx.status_code == 200
    data_lx = res_lx.json()
    assert data_lx["total_items"] == 1
    assert data_lx["items"][0]["domain"] == "github.com"


def test_scan_history_risk_level_filter(client: TestClient):
    """Verify filtering by friendly risk aliases (e.g. HIGH_RISK, LOW_RISK)."""
    user_id = uuid.uuid4()
    headers = _create_auth_headers(user_id)
    _mock_scans_store.clear()

    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://high-threat.org/",
        "normalized_url": "https://high-threat.org/",
        "domain": "high-threat.org",
        "scan_status": "complete",
        "risk_level": "HIGH",
        "trust_score": 35,
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
    }
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://safe-domain.com/",
        "normalized_url": "https://safe-domain.com/",
        "domain": "safe-domain.com",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 95,
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
    }

    # Filter by HIGH_RISK
    res_high = client.get("/api/v1/scans?risk_level=HIGH_RISK", headers=headers)
    assert res_high.status_code == 200
    data_high = res_high.json()
    assert data_high["total_items"] == 1
    assert data_high["items"][0]["risk_level"] == "HIGH"

    # Filter by LOW_RISK
    res_low = client.get("/api/v1/scans?risk_level=LOW_RISK", headers=headers)
    assert res_low.status_code == 200
    assert res_low.json()["total_items"] == 1


def test_scan_history_date_filtering(client: TestClient):
    """Verify date filtering presets (today, last_7_days, last_30_days)."""
    user_id = uuid.uuid4()
    headers = _create_auth_headers(user_id)
    _mock_scans_store.clear()

    now = datetime.now(timezone.utc)
    # Today's scan
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://site-today.com/",
        "normalized_url": "https://site-today.com/",
        "domain": "site-today.com",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 90,
        "is_guest": False,
        "created_at": now - timedelta(hours=2),
    }
    # 5 days ago scan
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://site-5days.com/",
        "normalized_url": "https://site-5days.com/",
        "domain": "site-5days.com",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 90,
        "is_guest": False,
        "created_at": now - timedelta(days=5),
    }
    # 45 days ago scan
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://site-old.com/",
        "normalized_url": "https://site-old.com/",
        "domain": "site-old.com",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 90,
        "is_guest": False,
        "created_at": now - timedelta(days=45),
    }

    # Today: should return 1
    res_today = client.get("/api/v1/scans?date_filter=today", headers=headers)
    assert res_today.status_code == 200
    assert res_today.json()["total_items"] == 1

    # Last 7 days: should return 2
    res_7d = client.get("/api/v1/scans?date_filter=last_7_days", headers=headers)
    assert res_7d.status_code == 200
    assert res_7d.json()["total_items"] == 2

    # Last 30 days: should return 2
    res_30d = client.get("/api/v1/scans?date_filter=last_30_days", headers=headers)
    assert res_30d.status_code == 200
    assert res_30d.json()["total_items"] == 2


def test_scan_history_sorting_options(client: TestClient):
    """Verify sorting by highest score, lowest score, and chronological order."""
    user_id = uuid.uuid4()
    headers = _create_auth_headers(user_id)
    _mock_scans_store.clear()

    now = datetime.now(timezone.utc)
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://score-low.com/",
        "normalized_url": "https://score-low.com/",
        "domain": "score-low.com",
        "scan_status": "complete",
        "risk_level": "CRITICAL",
        "trust_score": 12,
        "is_guest": False,
        "created_at": now - timedelta(days=2),
    }
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://score-high.com/",
        "normalized_url": "https://score-high.com/",
        "domain": "score-high.com",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 99,
        "is_guest": False,
        "created_at": now - timedelta(days=1),
    }

    # Sort highest_score
    res_hi = client.get("/api/v1/scans?sort_by=highest_score", headers=headers)
    assert res_hi.status_code == 200
    items_hi = res_hi.json()["items"]
    assert items_hi[0]["digital_trust_score"] == 99

    # Sort lowest_score
    res_lo = client.get("/api/v1/scans?sort_by=lowest_score", headers=headers)
    assert res_lo.status_code == 200
    items_lo = res_lo.json()["items"]
    assert items_lo[0]["digital_trust_score"] == 12


# ==============================================================================
# 3. DETAILED SECURITY REPORT & INTEGRITY TESTS
# ==============================================================================


def test_get_detailed_security_report_owner_success(client: TestClient):
    """Owner can retrieve full structured security report with preserved metrics."""
    user_id = uuid.uuid4()
    scan_id = uuid.uuid4()
    headers = _create_auth_headers(user_id)
    _mock_scans_store.clear()
    _mock_results_store.clear()

    _mock_scans_store[scan_id] = {
        "id": scan_id,
        "user_id": user_id,
        "submitted_url": "https://detailed-report-target.com",
        "normalized_url": "https://detailed-report-target.com/",
        "domain": "detailed-report-target.com",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 94,
        "risk_score": 6,
        "assessment_status": "COMPLETE",
        "assessment_coverage": 1.0,
        "scoring_version": "v1.0.0",
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
        "completed_at": datetime.now(timezone.utc),
    }
    _mock_results_store[scan_id] = {
        "id": uuid.uuid4(),
        "scan_id": scan_id,
        "trust_score": 94,
        "overall_risk_level": "LOW",
        "phishing_probability": 0.05,
        "ml_prediction": "LIKELY_LEGITIMATE",
        "ml_score": 95,
        "virustotal_detection_count": 0,
        "virustotal_total_engines": 75,
        "threat_intelligence_status": "NO_DETECTIONS",
        "vt_score": 98,
        "ssl_status": "VALID",
        "ssl_valid": True,
        "ssl_issuer": "Let's Encrypt Authority X3",
        "ssl_days_remaining": 88,
        "score_breakdown": {
            "summary": "Verified clean domain profile.",
            "recommendations": ["Safe browsing practices advised."],
            "risk_indicators": [],
            "positive_indicators": [
                {
                    "title": "Clean Vendor Feeds",
                    "description": "Zero security engines flagged this URL.",
                    "source_module": "virustotal",
                    "severity": "info",
                    "evidence": "0/75",
                    "affects_score": True,
                    "explanation": "No malicious reports detected.",
                }
            ],
            "unknown_indicators": [],
            "scoring_version": "v1.0.0",
            "high_severity_override": False,
        },
        "analysis_summary": "Verified clean domain profile.",
        "created_at": datetime.now(timezone.utc),
    }

    response = client.get(f"/api/v1/scans/{scan_id}", headers=headers)
    assert response.status_code == 200
    report = response.json()

    assert report["scan_id"] == str(scan_id)
    assert report["domain"] == "detailed-report-target.com"
    assert report["digital_trust_score"] == 94
    assert report["risk_level"] == "LOW"
    assert report["scoring_version"] == "v1.0.0"
    assert len(report["positive_indicators"]) == 1
    assert report["positive_indicators"][0]["title"] == "Clean Vendor Feeds"


def test_cross_user_report_access_blocked_without_leakage(client: TestClient):
    """Unauthorized user attempting to access another user's scan receives 404 (preventing enumeration)."""
    user_owner = uuid.uuid4()
    user_attacker = uuid.uuid4()
    scan_id = uuid.uuid4()
    headers_attacker = _create_auth_headers(user_attacker, "attacker@trustguard.ai")
    _mock_scans_store.clear()

    _mock_scans_store[scan_id] = {
        "id": scan_id,
        "user_id": user_owner,
        "submitted_url": "https://confidential-enterprise-site.internal",
        "normalized_url": "https://confidential-enterprise-site.internal/",
        "domain": "confidential-enterprise-site.internal",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 90,
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
    }

    # Attacker tries to get owner's scan
    response = client.get(f"/api/v1/scans/{scan_id}", headers=headers_attacker)
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["error"]["message"].lower()


def test_exportable_security_report_endpoint(client: TestClient):
    """GET /api/v1/scans/{scan_id}/export returns sanitized export format."""
    user_id = uuid.uuid4()
    scan_id = uuid.uuid4()
    headers = _create_auth_headers(user_id)
    _mock_scans_store.clear()
    _mock_results_store.clear()

    _mock_scans_store[scan_id] = {
        "id": scan_id,
        "user_id": user_id,
        "submitted_url": "https://export-test.org",
        "normalized_url": "https://export-test.org/",
        "domain": "export-test.org",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 96,
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
    }

    res = client.get(f"/api/v1/scans/{scan_id}/export", headers=headers)
    assert res.status_code == 200
    export_data = res.json()
    assert "TGA-REP-" in export_data["report_id"]
    assert export_data["domain"] == "export-test.org"
    assert export_data["platform"] == "TrustGuard AI"
    assert "disclaimer" in export_data


# ==============================================================================
# 4. SCAN DELETION & CASCADING TESTS
# ==============================================================================


def test_user_can_delete_own_scan_and_cascades(client: TestClient):
    """Authenticated owner can delete their scan record, cascading to scan_results."""
    user_id = uuid.uuid4()
    scan_id = uuid.uuid4()
    headers = _create_auth_headers(user_id)
    _mock_scans_store.clear()
    _mock_results_store.clear()

    _mock_scans_store[scan_id] = {
        "id": scan_id,
        "user_id": user_id,
        "submitted_url": "https://delete-me.com",
        "normalized_url": "https://delete-me.com/",
        "domain": "delete-me.com",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 90,
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
    }
    _mock_results_store[scan_id] = {
        "id": uuid.uuid4(),
        "scan_id": scan_id,
        "trust_score": 90,
        "overall_risk_level": "LOW",
        "score_breakdown": {},
        "created_at": datetime.now(timezone.utc),
    }

    # Delete scan
    del_res = client.delete(f"/api/v1/scans/{scan_id}", headers=headers)
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["success"] is True
    assert del_data["scan_id"] == str(scan_id)

    # Verify scan is deleted from store
    assert scan_id not in _mock_scans_store
    assert scan_id not in _mock_results_store

    # Subsequent GET returns 404
    get_res = client.get(f"/api/v1/scans/{scan_id}", headers=headers)
    assert get_res.status_code == 404


def test_user_cannot_delete_another_users_scan(client: TestClient):
    """User cannot delete another user's scan record (returns 404)."""
    user_owner = uuid.uuid4()
    user_attacker = uuid.uuid4()
    scan_id = uuid.uuid4()
    headers_attacker = _create_auth_headers(user_attacker)
    _mock_scans_store.clear()

    _mock_scans_store[scan_id] = {
        "id": scan_id,
        "user_id": user_owner,
        "submitted_url": "https://protected-site.com",
        "normalized_url": "https://protected-site.com/",
        "domain": "protected-site.com",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 90,
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
    }

    del_res = client.delete(f"/api/v1/scans/{scan_id}", headers=headers_attacker)
    assert del_res.status_code == 404
    assert scan_id in _mock_scans_store  # Still exists untouched


def test_delete_nonexistent_scan_returns_404(client: TestClient):
    """Attempting to delete a non-existent scan returns 404."""
    user_id = uuid.uuid4()
    headers = _create_auth_headers(user_id)
    random_id = uuid.uuid4()

    del_res = client.delete(f"/api/v1/scans/{random_id}", headers=headers)
    assert del_res.status_code == 404


# ==============================================================================
# 5. SCAN STATISTICS TESTS
# ==============================================================================


def test_scan_statistics_aggregation_and_averages(client: TestClient):
    """Verify statistics counts, risk breakdown, and average DTS exclusion rules."""
    user_id = uuid.uuid4()
    headers = _create_auth_headers(user_id)
    _mock_scans_store.clear()

    now = datetime.now(timezone.utc)
    # 2 LOW risk complete scans (scores: 90, 100) -> eligible avg = 95.0
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://site1.com",
        "normalized_url": "https://site1.com/",
        "domain": "site1.com",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 90,
        "assessment_status": "COMPLETE",
        "is_guest": False,
        "created_at": now - timedelta(minutes=10),
    }
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://site2.com",
        "normalized_url": "https://site2.com/",
        "domain": "site2.com",
        "scan_status": "complete",
        "risk_level": "SAFE",
        "trust_score": 100,
        "assessment_status": "COMPLETE",
        "is_guest": False,
        "created_at": now - timedelta(minutes=5),
    }
    # 1 HIGH risk complete scan (score: 40)
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://site3.com",
        "normalized_url": "https://site3.com/",
        "domain": "site3.com",
        "scan_status": "complete",
        "risk_level": "HIGH",
        "trust_score": 40,
        "assessment_status": "COMPLETE",
        "is_guest": False,
        "created_at": now - timedelta(minutes=2),
    }
    # 1 INCOMPLETE scan (error status, score: None -> must be excluded from average)
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://site-failed.com",
        "normalized_url": "https://site-failed.com/",
        "domain": "site-failed.com",
        "scan_status": "error",
        "risk_level": "UNKNOWN",
        "trust_score": None,
        "assessment_status": "INSUFFICIENT_DATA",
        "is_guest": False,
        "created_at": now - timedelta(minutes=1),
    }

    res = client.get("/api/v1/scans/statistics", headers=headers)
    assert res.status_code == 200
    stats = res.json()

    assert stats["total_scans"] == 4
    assert stats["low_risk_scans"] == 2
    assert stats["moderate_risk_scans"] == 0
    assert stats["high_risk_scans"] == 1
    assert stats["critical_risk_scans"] == 0
    assert stats["incomplete_assessments"] == 1
    # Average of [90, 100, 40] = 230 / 3 = 76.7
    assert stats["average_trust_score"] == 76.7
    assert len(stats["recent_scans"]) == 4


# ==============================================================================
# 6. AUTHENTICATION & ACCESS CONTROL ENFORCEMENT
# ==============================================================================


def test_unauthenticated_access_to_protected_endpoints_rejected(client: TestClient):
    """Unauthenticated requests to protected endpoints return 401 Unauthorized."""
    # 1. Scans list
    res_list = client.get("/api/v1/scans")
    assert res_list.status_code == 401

    # 2. Statistics
    res_stats = client.get("/api/v1/scans/statistics")
    assert res_stats.status_code == 401

    # 3. Deletion
    res_del = client.delete(f"/api/v1/scans/{uuid.uuid4()}")
    assert res_del.status_code == 401


def test_guest_scans_are_isolated_from_user_history(client: TestClient):
    """Guest scans (is_guest=True) must never appear in user history lists."""
    user_id = uuid.uuid4()
    headers = _create_auth_headers(user_id)
    _mock_scans_store.clear()

    # User's own registered scan
    _mock_scans_store[uuid.uuid4()] = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "submitted_url": "https://user-site.org",
        "normalized_url": "https://user-site.org/",
        "domain": "user-site.org",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 90,
        "is_guest": False,
        "created_at": datetime.now(timezone.utc),
    }

    # Anonymous guest scan
    guest_scan_id = uuid.uuid4()
    _mock_scans_store[guest_scan_id] = {
        "id": guest_scan_id,
        "user_id": None,
        "submitted_url": "https://guest-site.org",
        "normalized_url": "https://guest-site.org/",
        "domain": "guest-site.org",
        "scan_status": "complete",
        "risk_level": "LOW",
        "trust_score": 90,
        "is_guest": True,
        "created_at": datetime.now(timezone.utc),
    }

    # Query history: only the user's scan should appear
    res = client.get("/api/v1/scans", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_items"] == 1
    assert data["items"][0]["domain"] == "user-site.org"

    # Direct query of guest scan with scan_id is allowed for guest session access
    res_guest = client.get(f"/api/v1/scans/{guest_scan_id}")
    assert res_guest.status_code == 200
    assert res_guest.json()["is_guest"] is True
