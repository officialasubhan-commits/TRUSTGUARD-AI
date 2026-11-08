"""
Automated test suite for TrustGuard AI Authentication & Session Management.
Tests registration, login, JWT validation, expiration, ownership, and profile updates.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.services.auth_service import _generate_mock_jwt


def test_successful_registration(client: TestClient):
    """Verify that a new user can register and receive valid auth tokens."""
    unique_email = f"user_{uuid.uuid4().hex[:8]}@trustguard.ai"
    payload = {
        "email": unique_email,
        "full_name": "Bob Security",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["full_name"] == "Bob Security"


def test_registration_invalid_inputs(client: TestClient):
    """Verify input validation rejects mismatched passwords, weak passwords, and bad emails."""
    # 1. Passwords do not match
    res_mismatch = client.post(
        "/api/v1/auth/register",
        json={
            "email": "valid@trustguard.ai",
            "full_name": "Test User",
            "password": "Password123!",
            "confirm_password": "DifferentPassword123!",
        },
    )
    assert res_mismatch.status_code == 422

    # 2. Password too weak (no numbers or symbols)
    res_weak = client.post(
        "/api/v1/auth/register",
        json={
            "email": "valid@trustguard.ai",
            "full_name": "Test User",
            "password": "onlylettershere",
            "confirm_password": "onlylettershere",
        },
    )
    assert res_weak.status_code == 422

    # 3. Invalid email format
    res_bad_email = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "full_name": "Test User",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert res_bad_email.status_code == 422


def test_duplicate_registration_rejected(client: TestClient):
    """Verify that registering an already registered email returns 409 Conflict."""
    email = f"dup_{uuid.uuid4().hex[:8]}@trustguard.ai"
    payload = {
        "email": email,
        "full_name": "Duplicate User",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    # First registration
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with duplicate email
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "USER_ALREADY_EXISTS"


def test_successful_login(client: TestClient):
    """Verify registered user can successfully authenticate and receive tokens."""
    email = f"login_{uuid.uuid4().hex[:8]}@trustguard.ai"
    password = "CorrectPassword123!"

    # Register
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Login Tester",
            "password": password,
            "confirm_password": password,
        },
    )

    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == email


def test_invalid_login_credentials(client: TestClient):
    """Verify that incorrect passwords return 401 without leaking account existence."""
    res = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@trustguard.ai",
            "password": "WrongPassword123!",
        },
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_missing_auth_token_rejected(client: TestClient):
    """Verify protected endpoints return 401 when Authorization header is absent."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"

    res_user = client.get("/api/v1/users/me")
    assert res_user.status_code == 401


def test_invalid_jwt_rejected(client: TestClient):
    """Verify malformed or invalid JWTs return 401."""
    headers = {"Authorization": "Bearer invalid.token.structure"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_TOKEN"


def test_expired_jwt_rejected(client: TestClient):
    """Verify that expired JWT access tokens are rejected with TOKEN_EXPIRED."""
    user_id = uuid.uuid4()
    # Generate token that expired 10 seconds ago
    expired_token = _generate_mock_jwt(user_id, "expired@trustguard.ai", expires_in=-10)

    headers = {"Authorization": f"Bearer {expired_token}"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_protected_profile_endpoint_and_ownership(client: TestClient):
    """Verify that authenticated users can retrieve and update their own profile."""
    email = f"profile_{uuid.uuid4().hex[:8]}@trustguard.ai"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Original Name",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /api/v1/users/me
    get_res = client.get("/api/v1/users/me", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["email"] == email
    assert get_res.json()["full_name"] == "Original Name"

    # 2. PATCH /api/v1/users/me
    patch_res = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"full_name": "Updated Name", "avatar_url": "https://avatar.example.com/new.png"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["full_name"] == "Updated Name"
    assert patch_res.json()["avatar_url"] == "https://avatar.example.com/new.png"

    # Verify updated profile persists
    get_res_after = client.get("/api/v1/users/me", headers=headers)
    assert get_res_after.json()["full_name"] == "Updated Name"


def test_logout_endpoint(client: TestClient):
    """Verify logout returns successful message."""
    user_id = uuid.uuid4()
    token = _generate_mock_jwt(user_id, "logout@trustguard.ai")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/auth/logout", headers=headers)
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_token_refresh(client: TestClient):
    """Verify session can be refreshed with a valid refresh token."""
    email = f"refresh_{uuid.uuid4().hex[:8]}@trustguard.ai"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Refresh Tester",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    refresh_token = reg_res.json()["refresh_token"]

    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    assert "access_token" in ref_res.json()
    assert "refresh_token" in ref_res.json()


def test_forgot_password_generic_response(client: TestClient):
    """Verify forgot password returns generic safe response."""
    res = client.post("/api/v1/auth/forgot-password", json={"email": "random@trustguard.ai"})
    assert res.status_code == 200
    assert "instructions" in res.json()["message"]
