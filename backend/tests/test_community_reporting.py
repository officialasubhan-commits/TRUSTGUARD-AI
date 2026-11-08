"""
Comprehensive automated tests for TrustGuard AI Community Threat Reporting System.
Tests submission, validation, deduplication, privacy redaction, user history,
admin moderation lifecycle, voting, and non-authoritative risk score isolation.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.services.auth_service import _generate_mock_jwt
from app.services.community_reporting_service import get_community_service


def _auth_header(user_id: uuid.UUID, email: str, role: str = "authenticated") -> dict:
    token = _generate_mock_jwt(user_id=user_id, email=email, role=role)
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------ #
# 1. Report Submission & Validation Tests                            #
# ------------------------------------------------------------------ #


def test_submit_valid_community_report(client: TestClient):
    """Authenticated user successfully submits a valid suspicious URL report."""
    user_id = uuid.uuid4()
    headers = _auth_header(user_id, "analyst@security.org")

    payload = {
        "submitted_url": "https://secure-login-chase-update.com/account/auth",
        "category": "PHISHING",
        "target_brand": "Chase Bank",
        "attack_vector": "email",
        "description": "Received suspicious email prompting immediate account reset.",
        "evidence_url": "https://pastebin.com/raw/example1",
    }

    res = client.post("/api/v1/community/reports", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["submitted_url"] == "https://secure-login-chase-update.com/account/auth"
    assert data["category"] == "PHISHING"
    assert data["target_brand"] == "Chase Bank"
    assert data["attack_vector"] == "email"
    assert data["moderation_status"] == "PENDING"
    assert data["verification_status"] == "UNVERIFIED"
    assert data["upvotes"] == 0
    assert "id" in data


def test_submit_report_unauthenticated_rejected(client: TestClient):
    """Unauthenticated guest cannot submit a threat report."""
    payload = {
        "submitted_url": "https://malicious-crypto-drainer.io",
        "category": "FRAUD_OR_SCAM",
        "description": "Fake giveaway stealing private keys",
    }
    res = client.post("/api/v1/community/reports", json=payload)
    assert res.status_code == 401


def test_submit_report_invalid_url_rejected(client: TestClient):
    """Submissions with malformed or invalid schemes are rejected."""
    user_id = uuid.uuid4()
    headers = _auth_header(user_id, "user1@example.com")

    # 1. Non-HTTP scheme
    res1 = client.post(
        "/api/v1/community/reports",
        json={"submitted_url": "ftp://malicious.org/script.sh", "category": "MALWARE_DISTRIBUTION"},
        headers=headers,
    )
    assert res1.status_code == 422

    # 2. SSRF target (localhost / loopback)
    res2 = client.post(
        "/api/v1/community/reports",
        json={"submitted_url": "http://127.0.0.1:8080/admin", "category": "PHISHING"},
        headers=headers,
    )
    assert res2.status_code == 422

    # 3. SSRF metadata address
    res3 = client.post(
        "/api/v1/community/reports",
        json={"submitted_url": "http://169.254.169.254/latest/meta-data", "category": "OTHER"},
        headers=headers,
    )
    assert res3.status_code == 422


# ------------------------------------------------------------------ #
# 2. Deduplication & Anti-Spam Tests                                 #
# ------------------------------------------------------------------ #


def test_duplicate_submission_by_same_user_rejected(client: TestClient):
    """Submitting the exact same URL twice by the same user raises 409 Conflict."""
    user_id = uuid.uuid4()
    headers = _auth_header(user_id, "spammer_test@example.com")
    url = f"https://scam-site-{uuid.uuid4().hex[:6]}.com/login"

    payload = {
        "submitted_url": url,
        "category": "PHISHING",
        "description": "First submission",
    }

    # First attempt: SUCCESS
    res1 = client.post("/api/v1/community/reports", json=payload, headers=headers)
    assert res1.status_code == 201

    # Second attempt: CONFLICT 409
    res2 = client.post("/api/v1/community/reports", json=payload, headers=headers)
    assert res2.status_code == 409
    assert "already submitted" in res2.json()["error"]["message"].lower()


def test_cross_user_duplicate_links_duplicate_of(client: TestClient):
    """When a different user reports an already-reported URL, it links to the primary report."""
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    headers_a = _auth_header(user_a, "user_a@example.com")
    headers_b = _auth_header(user_b, "user_b@example.com")

    shared_url = f"https://shared-phish-{uuid.uuid4().hex[:6]}.net/verify"

    # User A submits
    res_a = client.post(
        "/api/v1/community/reports",
        json={"submitted_url": shared_url, "category": "PHISHING", "description": "Report by A"},
        headers=headers_a,
    )
    assert res_a.status_code == 201
    primary_id = res_a.json()["id"]

    # User B submits same URL
    res_b = client.post(
        "/api/v1/community/reports",
        json={"submitted_url": shared_url, "category": "PHISHING", "description": "Report by B"},
        headers=headers_b,
    )
    assert res_b.status_code == 201
    dup_id = res_b.json()["id"]
    assert dup_id != primary_id
    assert res_b.json()["duplicate_of"] == primary_id


# ------------------------------------------------------------------ #
# 3. Public Listing & Privacy Redaction Tests                        #
# ------------------------------------------------------------------ #


def test_public_reports_excludes_pending_and_rejected(client: TestClient):
    """Public listing only displays approved reports and hides unapproved submissions."""
    user_id = uuid.uuid4()
    headers = _auth_header(user_id, "user@example.com")
    admin_id = uuid.uuid4()
    admin_headers = _auth_header(admin_id, "admin@trustguard.ai", role="admin")

    # 1. Submit a report (will be PENDING)
    unique_slug = uuid.uuid4().hex[:8]
    pending_url = f"https://pending-{unique_slug}.com"
    res1 = client.post(
        "/api/v1/community/reports",
        json={"submitted_url": pending_url, "category": "SUSPICIOUS_REDIRECT"},
        headers=headers,
    )
    assert res1.status_code == 201
    pending_id = res1.json()["id"]

    # Public list must NOT contain the pending report
    pub_res = client.get(f"/api/v1/community/reports?search={unique_slug}")
    assert pub_res.status_code == 200
    assert not any(item["id"] == pending_id for item in pub_res.json()["items"])

    # 2. Admin approves the report
    mod_res = client.patch(
        f"/api/v1/admin/community/reports/{pending_id}",
        json={
            "moderation_status": "APPROVED",
            "verification_status": "ADMIN_VERIFIED",
            "moderation_notes": "Verified malicious credential harvesting domain.",
        },
        headers=admin_headers,
    )
    assert mod_res.status_code == 200

    # 3. Now the approved report MUST appear in public list
    pub_res2 = client.get(f"/api/v1/community/reports?search={unique_slug}")
    assert pub_res2.status_code == 200
    items = pub_res2.json()["items"]
    assert any(item["id"] == pending_id for item in items)


def test_public_reports_redacts_private_identity_and_notes(client: TestClient):
    """Publicly visible report schema strictly masks user identity and reviewer notes."""
    user_id = uuid.uuid4()
    headers = _auth_header(user_id, "secret_whistleblower@protonmail.com")
    admin_id = uuid.uuid4()
    admin_headers = _auth_header(admin_id, "moderator@trustguard.ai", role="admin")

    unique_slug = uuid.uuid4().hex[:8]
    url = f"https://sanitized-check-{unique_slug}.com"

    res = client.post(
        "/api/v1/community/reports",
        json={
            "submitted_url": url,
            "category": "PHISHING",
            "description": "Public text description",
        },
        headers=headers,
    )
    rep_id = res.json()["id"]

    # Approve report with secret moderation notes
    client.patch(
        f"/api/v1/admin/community/reports/{rep_id}",
        json={
            "moderation_status": "APPROVED",
            "moderation_notes": "INTERNAL ONLY: Analyst inspected reverse shell at /bin/sh",
        },
        headers=admin_headers,
    )

    # Fetch publicly without any auth token
    pub_res = client.get(f"/api/v1/community/reports/{rep_id}")
    assert pub_res.status_code == 200
    data = pub_res.json()

    # Assert sensitive keys are ABSENT from public payload
    assert "user_id" not in data
    assert "email" not in data
    assert "moderation_notes" not in data
    assert "moderator_id" not in data
    assert data["submitted_url"] == url
    assert data["category"] == "PHISHING"


# ------------------------------------------------------------------ #
# 4. User Submission History Tests                                   #
# ------------------------------------------------------------------ #


def test_user_can_view_own_submissions_history(client: TestClient):
    """Users can inspect all their own reports, including pending and rejected."""
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    headers_a = _auth_header(user_a, "alice@security.com")
    headers_b = _auth_header(user_b, "bob@security.com")

    slug_a = uuid.uuid4().hex[:6]
    slug_b = uuid.uuid4().hex[:6]

    client.post(
        "/api/v1/community/reports",
        json={"submitted_url": f"https://alice-{slug_a}.com", "category": "PHISHING"},
        headers=headers_a,
    )
    client.post(
        "/api/v1/community/reports",
        json={"submitted_url": f"https://bob-{slug_b}.com", "category": "MALWARE_DISTRIBUTION"},
        headers=headers_b,
    )

    # Alice views her history
    res_a = client.get("/api/v1/community/my-reports", headers=headers_a)
    assert res_a.status_code == 200
    urls_a = [item["submitted_url"] for item in res_a.json()["items"]]
    assert any(slug_a in u for u in urls_a)
    assert not any(slug_b in u for u in urls_a)


# ------------------------------------------------------------------ #
# 5. Access Control & Anti-Enumeration for Report Details            #
# ------------------------------------------------------------------ #


def test_unapproved_report_anti_enumeration(client: TestClient):
    """Unapproved reports return 404 to unauthorized clients to prevent enumeration."""
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    owner_headers = _auth_header(owner_id, "owner@example.com")
    other_headers = _auth_header(other_user_id, "other@example.com")

    res = client.post(
        "/api/v1/community/reports",
        json={"submitted_url": "https://secret-unreviewed-threat.com", "category": "PHISHING"},
        headers=owner_headers,
    )
    report_id = res.json()["id"]

    # 1. Unauthenticated client -> 404
    assert client.get(f"/api/v1/community/reports/{report_id}").status_code == 404

    # 2. Another normal user -> 404
    assert (
        client.get(f"/api/v1/community/reports/{report_id}", headers=other_headers).status_code
        == 404
    )

    # 3. Submitting owner -> 200 OK
    res_owner = client.get(f"/api/v1/community/reports/{report_id}", headers=owner_headers)
    assert res_owner.status_code == 200
    assert res_owner.json()["moderation_status"] == "PENDING"


# ------------------------------------------------------------------ #
# 6. Admin Moderation & RBAC Tests                                   #
# ------------------------------------------------------------------ #


def test_non_admin_cannot_access_admin_moderation(client: TestClient):
    """Non-administrator requests to /api/v1/admin/community/* receive 403 Forbidden."""
    regular_user = uuid.uuid4()
    headers = _auth_header(regular_user, "regular@trustguard.ai", role="user")

    # 1. List admin queue -> 403
    res1 = client.get("/api/v1/admin/community/reports", headers=headers)
    assert res1.status_code == 403

    # 2. Patch moderation status -> 403
    dummy_id = uuid.uuid4()
    res2 = client.patch(
        f"/api/v1/admin/community/reports/{dummy_id}",
        json={"moderation_status": "APPROVED"},
        headers=headers,
    )
    assert res2.status_code == 403


def test_admin_moderation_lifecycle_flow(client: TestClient):
    """Full lifecycle: User submits -> Admin reviews, rejects, and re-approves."""
    user_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    user_headers = _auth_header(user_id, "reporter@site.com")
    admin_headers = _auth_header(admin_id, "lead_moderator@trustguard.ai", role="admin")

    # 1. Submit
    res = client.post(
        "/api/v1/community/reports",
        json={"submitted_url": "https://lifecycle-test.org/auth", "category": "IMPERSONATION"},
        headers=user_headers,
    )
    rep_id = res.json()["id"]

    # 2. Admin retrieves queue
    queue_res = client.get(
        "/api/v1/admin/community/reports?moderation_status=PENDING", headers=admin_headers
    )
    assert queue_res.status_code == 200
    assert any(item["id"] == rep_id for item in queue_res.json()["items"])

    # 3. Admin rejects report
    reject_res = client.patch(
        f"/api/v1/admin/community/reports/{rep_id}",
        json={
            "moderation_status": "REJECTED",
            "verification_status": "DISPUTED",
            "moderation_notes": "Domain verified as legitimate official partner.",
        },
        headers=admin_headers,
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["moderation_status"] == "REJECTED"
    assert reject_res.json()["verification_status"] == "DISPUTED"

    # 4. Admin transitions to APPROVED
    approve_res = client.patch(
        f"/api/v1/admin/community/reports/{rep_id}",
        json={
            "moderation_status": "APPROVED",
            "verification_status": "ADMIN_VERIFIED",
            "moderation_notes": "New telemetry confirms malicious redirect payload.",
        },
        headers=admin_headers,
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["moderation_status"] == "APPROVED"
    assert approve_res.json()["verification_status"] == "ADMIN_VERIFIED"


# ------------------------------------------------------------------ #
# 7. Upvoting & Consensus Tests                                      #
# ------------------------------------------------------------------ #


def test_upvote_approved_community_report(client: TestClient):
    """Approved reports can be upvoted by community members to reinforce signal."""
    user_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    user_headers = _auth_header(user_id, "voter1@test.org")
    admin_headers = _auth_header(admin_id, "admin@test.org", role="admin")

    # Create and approve report
    sub_res = client.post(
        "/api/v1/community/reports",
        json={
            "submitted_url": f"https://vote-test-{uuid.uuid4().hex[:6]}.com",
            "category": "PHISHING",
        },
        headers=user_headers,
    )
    rep_id = sub_res.json()["id"]

    client.patch(
        f"/api/v1/admin/community/reports/{rep_id}",
        json={"moderation_status": "APPROVED"},
        headers=admin_headers,
    )

    # Vote 1
    vote1 = client.post(f"/api/v1/community/reports/{rep_id}/upvote")
    assert vote1.status_code == 200
    assert vote1.json()["upvotes"] == 1

    # Vote 2
    vote2 = client.post(f"/api/v1/community/reports/{rep_id}/upvote")
    assert vote2.status_code == 200
    assert vote2.json()["upvotes"] == 2


def test_upvote_pending_report_fails(client: TestClient):
    """Unapproved reports cannot be upvoted."""
    user_id = uuid.uuid4()
    user_headers = _auth_header(user_id, "voter2@test.org")

    sub_res = client.post(
        "/api/v1/community/reports",
        json={
            "submitted_url": f"https://unapproved-vote-{uuid.uuid4().hex[:6]}.com",
            "category": "PHISHING",
        },
        headers=user_headers,
    )
    rep_id = sub_res.json()["id"]

    # Upvoting a pending report returns 404
    res = client.post(f"/api/v1/community/reports/{rep_id}/upvote")
    assert res.status_code == 404


# ------------------------------------------------------------------ #
# 8. Decoupled Risk Engine Verification                              #
# ------------------------------------------------------------------ #


def test_unverified_report_does_not_alter_trust_score():
    """
    Architectural guarantee: user submissions do NOT automatically mark
    websites as malicious or lower trust scores without verified consensus.
    """
    service = get_community_service()
    assert hasattr(service, "submit_report")
    # Verify that CommunityReportingService does not unilaterally invoke risk score overrides
    import inspect

    source = inspect.getsource(service.submit_report)
    assert "save_scan_results" not in source
    assert "update_trust_score" not in source
    assert "overall_risk_level" not in source
