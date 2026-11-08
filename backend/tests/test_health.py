"""
Automated tests for TrustGuard AI health checks and routing foundation.
"""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verify that root endpoint GET / returns 200 and expected metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TrustGuard AI"
    assert "version" in data
    assert data["status"] == "online"
    assert data["documentation"] == "/docs"
    assert data["v1_base"] == "/api/v1"


def test_root_health_endpoint(client: TestClient):
    """Verify that root health endpoint GET /health returns 200 and status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "TrustGuard AI"
    assert data["status"] == "healthy"
    assert "app_version" in data
    assert "environment" in data
    assert "database" in data


def test_api_v1_health_endpoint(client: TestClient):
    """Verify that API v1 health endpoint GET /api/v1/health returns 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "TrustGuard AI"
    assert data["status"] == "healthy"
    assert data["environment"] == "development"


def test_invalid_route_returns_json_404(client: TestClient):
    """Verify that requesting an unknown route returns custom JSON 404 response."""
    response = client.get("/nonexistent-endpoint-xyz")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "does not exist" in data["error"]["message"]


def test_v1_submodules_status_endpoints(client: TestClient):
    """Verify that all foundational v1 router submodules respond."""
    for path in [
        "/api/v1/auth/status",
        "/api/v1/scan/status",
        "/api/v1/history/status",
        "/api/v1/reports/status",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


def test_cors_headers_handling(client: TestClient):
    """Verify that CORS preflight or Origin requests receive appropriate headers."""
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
