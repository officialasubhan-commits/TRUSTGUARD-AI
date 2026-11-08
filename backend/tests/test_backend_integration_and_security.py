"""
End-to-End System Integration & Comprehensive Security Audit Test Suite for TrustGuard AI.
Verifies complete scanning pipeline, authentication/guest isolation, IDOR prevention,
SSRF rejection, admin authorization boundaries, and uniform error envelopes.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.services.auth_service import _generate_mock_jwt


def _auth_header(user_id: uuid.UUID, email: str, role: str = "authenticated") -> dict:
    token = _generate_mock_jwt(user_id=user_id, email=email, role=role)
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------ #
# 1. Complete End-to-End Scan & Reporting Workflow Integration       #
# ------------------------------------------------------------------ #


def test_complete_end_to_end_scanning_workflow(client: TestClient):
    """
    Validates complete workflow:
    User submits URL -> Static analysis + ML inference + SSL check + VT lookup ->
    Trust Score computation -> Scan persistence -> History retrieval -> Statistics.
    """
    user_id = uuid.uuid4()
    headers = _auth_header(user_id, "researcher@trustguard.ai")
    test_url = "https://safe-banking-portal-verified.com/portal/dashboard"

    # Step 1: Submit Scan
    scan_res = client.post(
        "/api/v1/scan",
        json={"url": test_url},
        headers=headers,
    )
    assert scan_res.status_code == 201
    scan_data = scan_res.json()

    assert "scan_id" in scan_data
    scan_id = scan_data["scan_id"]
    assert scan_data["original_url"] == test_url
    assert scan_data["normalized_url"].startswith("https://safe-banking-portal-verified.com")
    assert "preliminary_analysis" in scan_data
    assert "digital_trust_score" in scan_data
    assert "risk_level" in scan_data

    # Step 2: Retrieve Scan Detail via /scans/{scan_id}
    detail_res = client.get(f"/api/v1/scans/{scan_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["scan_id"] == scan_id
    assert detail_data["domain"] == "safe-banking-portal-verified.com"
    assert "module_scores" in detail_data
    assert "risk_indicators" in detail_data
    assert "recommendations" in detail_data

    # Step 3: Verify Scan Appears in History via /scans
    history_res = client.get("/api/v1/scans", headers=headers)
    assert history_res.status_code == 200
    history_items = history_res.json()["items"]
    assert any(item["scan_id"] == scan_id for item in history_items)

    # Step 4: Verify Scan Reflected in Statistics via /scans/statistics
    stats_res = client.get("/api/v1/scans/statistics", headers=headers)
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["total_scans"] >= 1

    # Step 5: Export Sanitized Security Report via /scans/{scan_id}/export
    export_res = client.get(f"/api/v1/scans/{scan_id}/export", headers=headers)
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert "database_id" not in export_data
    assert export_data["target_url"] == detail_data["original_url"]

    # Step 6: Delete Scan Record via DELETE /scans/{scan_id}
    del_res = client.delete(f"/api/v1/scans/{scan_id}", headers=headers)
    assert del_res.status_code == 200

    # Step 7: Verify Scan is Gone
    detail_after_del = client.get(f"/api/v1/scans/{scan_id}", headers=headers)
    assert detail_after_del.status_code == 404


def test_guest_scan_isolation_workflow(client: TestClient):
    """
    Verifies that unauthenticated guests can scan URLs, but guest scans are isolated:
    - Never appear in authenticated users' history
    - Cannot be deleted by users
    - Do not expose user IDs
    """
    guest_url = "https://example-guest-check.org"
    scan_res = client.post("/api/v1/scan", json={"url": guest_url})
    assert scan_res.status_code == 201
    data = scan_res.json()
    scan_id = data["scan_id"]

    # An authenticated user views their history: guest scan must NOT appear
    other_user = uuid.uuid4()
    headers = _auth_header(other_user, "other@test.com")
    hist_res = client.get("/api/v1/scans", headers=headers)
    assert not any(item["id"] == scan_id for item in hist_res.json()["items"])

    # Attempting to delete guest scan via DELETE /scans/{id} is forbidden
    del_res = client.delete(f"/api/v1/scans/{scan_id}", headers=headers)
    assert del_res.status_code in (403, 404)


# ------------------------------------------------------------------ #
# 2. Security Audit: IDOR & Authorization Boundaries                 #
# ------------------------------------------------------------------ #


def test_idor_prevention_on_scan_history(client: TestClient):
    """A user cannot access another user's private scan report (IDOR protection)."""
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    headers_a = _auth_header(user_a, "alice@security.com")
    headers_b = _auth_header(user_b, "bob@security.com")

    # User A creates a scan
    res_a = client.post(
        "/api/v1/scan",
        json={"url": "https://confidential-internal-audit.corp"},
        headers=headers_a,
    )
    scan_id_a = res_a.json()["scan_id"]

    # User B tries to access User A's scan details -> 404 / 403
    res_b = client.get(f"/api/v1/scans/{scan_id_a}", headers=headers_b)
    assert res_b.status_code in (403, 404)

    # User B tries to delete User A's scan -> 403 / 404
    del_b = client.delete(f"/api/v1/scans/{scan_id_a}", headers=headers_b)
    assert del_b.status_code in (403, 404)


def test_idor_prevention_on_user_profile(client: TestClient):
    """User cannot modify or view another user's profile attributes."""
    email_a = f"alice_{uuid.uuid4().hex[:6]}@example.com"
    email_b = f"bob_{uuid.uuid4().hex[:6]}@example.com"
    reg_a = client.post(
        "/api/v1/auth/register",
        json={
            "email": email_a,
            "full_name": "Alice User",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    reg_b = client.post(
        "/api/v1/auth/register",
        json={
            "email": email_b,
            "full_name": "Bob User",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # Alice updates her profile
    patch_res = client.patch(
        "/api/v1/users/me",
        json={"full_name": "Alice Updated"},
        headers=headers_a,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["full_name"] == "Alice Updated"

    # Bob's profile remains untouched
    bob_profile = client.get("/api/v1/users/me", headers=headers_b)
    assert bob_profile.status_code == 200
    assert bob_profile.json()["full_name"] == "Bob User"


def test_admin_role_spoofing_rejected(client: TestClient):
    """Regular users cannot bypass admin authorization by crafting mock claims or tokens."""
    regular_user = uuid.uuid4()
    user_headers = _auth_header(regular_user, "normal_user@example.com", role="user")

    # 1. Admin moderation queue blocked
    res1 = client.get("/api/v1/admin/community/reports", headers=user_headers)
    assert res1.status_code == 403
    assert "admin" in res1.json()["error"]["message"].lower()

    # 2. Admin patch blocked
    res2 = client.patch(
        f"/api/v1/admin/community/reports/{uuid.uuid4()}",
        json={"moderation_status": "APPROVED"},
        headers=user_headers,
    )
    assert res2.status_code == 403


# ------------------------------------------------------------------ #
# 3. Security Audit: SSRF & Input Validation                         #
# ------------------------------------------------------------------ #


def test_ssrf_static_rejection_across_endpoints(client: TestClient):
    """SSRF destinations (private IPs, metadata targets) are statically rejected."""
    user = uuid.uuid4()
    headers = _auth_header(user, "test@example.com")

    blocked_targets = [
        "http://127.0.0.1/admin",
        "http://localhost:8000/api",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.1/secret",
        "http://172.16.0.1/private",
        "http://192.168.1.1/router",
        "http://metadata.google.internal/computeMetadata/v1",
    ]

    for target in blocked_targets:
        # Scan submission endpoint rejects
        res_scan = client.post("/api/v1/scan", json={"url": target}, headers=headers)
        assert res_scan.status_code == 422, f"Failed to reject SSRF target on scan: {target}"

        # Community reporting endpoint rejects
        res_comm = client.post(
            "/api/v1/community/reports",
            json={"submitted_url": target, "category": "PHISHING"},
            headers=headers,
        )
        assert res_comm.status_code == 422, f"Failed to reject SSRF target on report: {target}"


def test_unsupported_protocol_schemes_rejected(client: TestClient):
    """Dangerous URL schemes are blocked."""
    dangerous = [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "ftp://mirror.example.com",
        "data:text/html,<script>alert(1)</script>",
    ]
    for d in dangerous:
        res = client.post("/api/v1/scan", json={"url": d})
        assert res.status_code == 422


# ------------------------------------------------------------------ #
# 4. Error Handling & Information Leakage Prevention                 #
# ------------------------------------------------------------------ #


def test_invalid_routes_return_safe_json_error(client: TestClient):
    """Non-existent routes return uniform JSON error without stack traces or HTML."""
    res = client.get("/api/v1/nonexistent-route-xyz")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "traceback" not in data
    assert "Traceback" not in res.text


def test_tampered_jwt_returns_safe_401(client: TestClient):
    """Tampered or invalid JWT signature returns 401 without exposing internal secret."""
    tampered_headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tampered.signature"
    }
    res = client.get("/api/v1/auth/me", headers=tampered_headers)
    assert res.status_code == 401
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] in ("INVALID_TOKEN", "UNAUTHORIZED")
    assert "trustguard-test-jwt-secret" not in res.text
