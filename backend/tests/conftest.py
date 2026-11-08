"""
Pytest configuration and fixtures for TrustGuard AI backend tests.
"""

import os

import pytest
from fastapi.testclient import TestClient

# Ensure test environment mode is active
os.environ["APP_ENV"] = "development"
os.environ["APP_DEBUG"] = "true"

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    TestClient fixture for executing API tests.
    """
    with TestClient(app) as test_client:
        yield test_client
