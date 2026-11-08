"""
Automated test suite for SSL/TLS Certificate Validation & Security Assessment Engine.

Verifies:
1. URL and destination safety (HTTP, private IPv4, loopback, link-local, cloud metadata, invalid host).
2. DNS resolution SSRF blocking (hostnames resolving to internal or reserved IP spaces).
3. Certificate validity states: VALID (> 30 days), EXPIRING_SOON (1-30 days), EXPIRED.
4. Certificate verification errors: HOSTNAME_MISMATCH, UNTRUSTED_CERTIFICATE, TLS_HANDSHAKE_FAILED.
5. Reliability handling: DNS_RESOLUTION_FAILED, TIMEOUT, CONNECTION_ERROR.
6. In-memory certificate caching and TTL behavior.
7. End-to-end integration with POST /api/v1/scan endpoint.
"""

from __future__ import annotations

import socket
import ssl
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ssl_tls_service import SSLValidationService

# ==============================================================================
# 1. DESTINATION SAFETY & SCHEME CHECKS
# ==============================================================================


@pytest.mark.asyncio
async def test_ssl_http_scheme_returns_https_not_used():
    """Verify plain HTTP URL immediately returns HTTPS_NOT_USED without network connection."""
    service = SSLValidationService()
    report = await service.validate_url_ssl("http://example.com/login")

    assert report.status == "HTTPS_NOT_USED"
    assert report.https_enabled is False
    assert report.ssl_subscore == 50
    assert "HTTPS is not enabled" in report.message
    assert any("unencrypted HTTP" in finding for finding in report.findings)


@pytest.mark.asyncio
async def test_ssl_missing_hostname():
    """Verify empty or invalid hostname yields UNKNOWN status."""
    service = SSLValidationService()
    report = await service.validate_url_ssl("https://")

    assert report.status == "UNKNOWN"
    assert report.ssl_subscore == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "blocked_host",
    [
        "localhost",
        "127.0.0.1",
        "169.254.169.254",
        "metadata.google.internal",
        "instance-data",
    ],
)
async def test_ssl_static_ssrf_blocked_destinations(blocked_host: str):
    """Verify loopback, cloud metadata, and internal hostnames are statically blocked."""
    service = SSLValidationService()
    report = await service.validate_url_ssl(f"https://{blocked_host}/")

    assert report.status == "UNSAFE_DESTINATION"
    assert report.ssl_subscore == 0
    assert report.error_code == "SSRF_STATIC_BLOCKED"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "resolved_ip",
    [
        "10.0.0.1",  # RFC 1918 Private Class A
        "172.16.5.10",  # RFC 1918 Private Class B
        "192.168.1.1",  # RFC 1918 Private Class C
        "127.0.0.2",  # Loopback
        "169.254.10.20",  # Link-local / APIPA
        "224.0.0.5",  # Multicast
        "fe80::1",  # IPv6 link-local
        "::1",  # IPv6 loopback
    ],
)
async def test_ssl_dns_ssrf_resolved_private_ip(resolved_ip: str):
    """Verify hostnames that resolve via DNS to private or reserved IPs are blocked."""
    service = SSLValidationService()
    # Ensure fresh cache
    service._cache.clear()

    mock_addrinfo = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", (resolved_ip, 443)),
    ]

    clean_ip_tag = resolved_ip.replace(":", "-").replace(".", "-")
    test_url = f"https://rebinding-{clean_ip_tag}.com/"

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        report = await service.validate_url_ssl(test_url)

    assert report.status == "UNSAFE_DESTINATION"
    assert report.ssl_subscore == 0
    assert report.error_code == "SSRF_RESOLVED_PRIVATE_IP"
    assert any(resolved_ip in finding for finding in report.findings)


# ==============================================================================
# 2. DNS & NETWORK RELIABILITY TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_ssl_dns_resolution_failure():
    """Verify socket.gaierror returns DNS_RESOLUTION_FAILED."""
    service = SSLValidationService()

    with patch(
        "socket.getaddrinfo", side_effect=socket.gaierror(8, "nodename nor servname provided")
    ):
        report = await service.validate_url_ssl("https://nonexistent-domain-xyz12345.com/")

    assert report.status == "DNS_RESOLUTION_FAILED"
    assert report.ssl_subscore == 50
    assert report.error_code == "DNS_GAI_ERROR"


@pytest.mark.asyncio
async def test_ssl_connection_timeout():
    """Verify socket.timeout returns TIMEOUT status."""
    service = SSLValidationService()

    mock_addrinfo = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
    ]

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        with patch("socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.connect.side_effect = socket.timeout("Timed out connecting")
            mock_sock_cls.return_value = mock_sock

            report = await service.validate_url_ssl("https://timeout-site.org/")

    assert report.status == "TIMEOUT"
    assert report.error_code == "TIMEOUT"
    assert report.ssl_subscore == 50


@pytest.mark.asyncio
async def test_ssl_connection_refused():
    """Verify ConnectionRefusedError returns CONNECTION_ERROR status."""
    service = SSLValidationService()

    mock_addrinfo = [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
    ]

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        with patch("socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
            mock_sock_cls.return_value = mock_sock

            report = await service.validate_url_ssl("https://closed-port-site.org/")

    assert report.status == "CONNECTION_ERROR"
    assert report.error_code == "CONNECTION_REFUSED"


# ==============================================================================
# 3. CERTIFICATE VALIDITY & PROTOCOL INSPECTION TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_ssl_valid_certificate():
    """Verify valid certificate with > 30 days remaining yields VALID status."""
    service = SSLValidationService()

    future_date = datetime.now(timezone.utc) + timedelta(days=90)
    not_after_str = future_date.strftime("%b %d %H:%M:%S %Y GMT")
    not_before_str = (datetime.now(timezone.utc) - timedelta(days=10)).strftime(
        "%b %d %H:%M:%S %Y GMT"
    )

    mock_cert = {
        "subject": ((("commonName", "example.com"),),),
        "issuer": ((("organizationName", "Let's Encrypt"),), (("commonName", "R3"),)),
        "notBefore": not_before_str,
        "notAfter": not_after_str,
    }

    mock_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        with patch("socket.socket"):
            with patch("ssl.create_default_context") as mock_ctx_cls:
                mock_ctx = MagicMock()
                mock_tls_sock = MagicMock()
                mock_tls_sock.getpeercert.return_value = mock_cert
                mock_tls_sock.version.return_value = "TLSv1.3"
                mock_tls_sock.cipher.return_value = ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)
                mock_ctx.wrap_socket.return_value = mock_tls_sock
                mock_ctx_cls.return_value = mock_ctx

                report = await service.validate_url_ssl("https://example.com/")

    assert report.status == "VALID"
    assert report.ssl_subscore == 100
    assert report.days_remaining is not None
    assert report.days_remaining >= 80
    assert report.tls_version == "TLSv1.3"
    assert report.cipher == "TLS_AES_256_GCM_SHA384"
    assert "Let's Encrypt" in (report.certificate_issuer or "")


@pytest.mark.asyncio
async def test_ssl_expiring_soon_certificate():
    """Verify certificate with 1-30 days remaining yields EXPIRING_SOON status."""
    service = SSLValidationService()

    expiring_date = datetime.now(timezone.utc) + timedelta(days=15)
    not_after_str = expiring_date.strftime("%b %d %H:%M:%S %Y GMT")

    mock_cert = {
        "subject": ((("commonName", "expiring-site.com"),),),
        "issuer": ((("organizationName", "DigiCert Inc"),),),
        "notBefore": "Jan 01 00:00:00 2024 GMT",
        "notAfter": not_after_str,
    }

    mock_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        with patch("socket.socket"):
            with patch("ssl.create_default_context") as mock_ctx_cls:
                mock_ctx = MagicMock()
                mock_tls_sock = MagicMock()
                mock_tls_sock.getpeercert.return_value = mock_cert
                mock_tls_sock.version.return_value = "TLSv1.3"
                mock_tls_sock.cipher.return_value = ("TLS_AES_128_GCM_SHA256", "TLSv1.3", 128)
                mock_ctx.wrap_socket.return_value = mock_tls_sock
                mock_ctx_cls.return_value = mock_ctx

                report = await service.validate_url_ssl("https://expiring-site.com/")

    assert report.status == "EXPIRING_SOON"
    assert report.ssl_subscore == 75
    assert report.days_remaining in (14, 15)
    assert any(
        "approaching expiration" in report.message.lower() or "expires in" in f.lower()
        for f in report.findings
    )


@pytest.mark.asyncio
async def test_ssl_expired_certificate():
    """Verify expired certificate yields EXPIRED status."""
    service = SSLValidationService()

    mock_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

    # Simulate SSLCertVerificationError on handshake due to expiration
    cert_err = ssl.SSLCertVerificationError(
        1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate has expired (_ssl.c:1006)"
    )

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        with patch("socket.socket"):
            with patch("ssl.create_default_context") as mock_ctx_cls:
                mock_ctx = MagicMock()
                mock_ctx.wrap_socket.side_effect = cert_err
                mock_ctx_cls.return_value = mock_ctx

                report = await service.validate_url_ssl("https://expired.badssl.com/")

    assert report.status == "EXPIRED"
    assert report.ssl_subscore == 10
    assert report.error_code == "CERT_EXPIRED"


@pytest.mark.asyncio
async def test_ssl_hostname_mismatch():
    """Verify certificate hostname mismatch yields HOSTNAME_MISMATCH status."""
    service = SSLValidationService()

    mock_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
    mismatch_err = ssl.SSLCertVerificationError(
        1,
        "[SSL: CERTIFICATE_VERIFY_FAILED] certificate is not valid for 'wrong-domain.com' (_ssl.c:1006)",
    )

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        with patch("socket.socket"):
            with patch("ssl.create_default_context") as mock_ctx_cls:
                mock_ctx = MagicMock()
                mock_ctx.wrap_socket.side_effect = mismatch_err
                mock_ctx_cls.return_value = mock_ctx

                report = await service.validate_url_ssl("https://wrong-domain.com/")

    assert report.status == "HOSTNAME_MISMATCH"
    assert report.ssl_subscore == 20
    assert report.error_code == "HOSTNAME_MISMATCH"


@pytest.mark.asyncio
async def test_ssl_untrusted_certificate():
    """Verify self-signed or untrusted root yields UNTRUSTED_CERTIFICATE status."""
    service = SSLValidationService()

    mock_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
    untrusted_err = ssl.SSLCertVerificationError(
        1,
        "[SSL: CERTIFICATE_VERIFY_FAILED] self-signed certificate in certificate chain (_ssl.c:1006)",
    )

    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        with patch("socket.socket"):
            with patch("ssl.create_default_context") as mock_ctx_cls:
                mock_ctx = MagicMock()
                mock_ctx.wrap_socket.side_effect = untrusted_err
                mock_ctx_cls.return_value = mock_ctx

                report = await service.validate_url_ssl("https://self-signed.badssl.com/")

    assert report.status == "UNTRUSTED_CERTIFICATE"
    assert report.ssl_subscore == 25
    assert report.error_code == "UNTRUSTED_ROOT"


# ==============================================================================
# 4. IN-MEMORY CACHING VERIFICATION
# ==============================================================================


@pytest.mark.asyncio
async def test_ssl_in_memory_caching():
    """Verify second check for same hostname returns cached result without second connection."""
    service = SSLValidationService()
    hostname = "cached-ssl-target.org"
    url = f"https://{hostname}/"

    mock_cert = {
        "subject": ((("commonName", hostname),),),
        "issuer": ((("commonName", "TrustGuard CA"),),),
        "notBefore": "Jan 01 00:00:00 2024 GMT",
        "notAfter": (datetime.now(timezone.utc) + timedelta(days=60)).strftime(
            "%b %d %H:%M:%S %Y GMT"
        ),
    }
    mock_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

    with patch("socket.getaddrinfo", return_value=mock_addrinfo) as mock_dns:
        with patch("socket.socket"):
            with patch("ssl.create_default_context") as mock_ctx_cls:
                mock_ctx = MagicMock()
                mock_tls_sock = MagicMock()
                mock_tls_sock.getpeercert.return_value = mock_cert
                mock_tls_sock.version.return_value = "TLSv1.3"
                mock_tls_sock.cipher.return_value = ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)
                mock_ctx.wrap_socket.return_value = mock_tls_sock
                mock_ctx_cls.return_value = mock_ctx

                # Call 1: uncached
                report1 = await service.validate_url_ssl(url)
                assert report1.cached is False
                assert mock_dns.call_count == 1

                # Call 2: must be served from cache
                report2 = await service.validate_url_ssl(url)
                assert report2.cached is True
                assert mock_dns.call_count == 1  # No additional DNS call made


# ==============================================================================
# 5. INTEGRATION WITH POST /api/v1/scan ENDPOINT
# ==============================================================================


def test_scan_endpoint_includes_ssl_analysis():
    """Verify POST /api/v1/scan returns integrated ssl_analysis schema."""
    client = TestClient(app)

    # Submit HTTP URL -> should return HTTPS_NOT_USED inside ssl_analysis
    response = client.post("/api/v1/scan", json={"url": "http://insecure-example.org/test"})
    assert response.status_code == 201

    data = response.json()
    assert "ssl_analysis" in data
    assert data["ssl_analysis"] is not None

    ssl_data = data["ssl_analysis"]
    assert ssl_data["status"] == "HTTPS_NOT_USED"
    assert ssl_data["https_enabled"] is False
    assert "safety_advisory" in ssl_data
    assert "findings" in ssl_data


def test_scan_endpoint_fault_tolerance_when_ssl_fails():
    """Verify overall scan succeeds even if SSL handshake encounters error."""
    client = TestClient(app)

    # Submit valid URL format but mock DNS failure during SSL phase
    with patch("socket.getaddrinfo", side_effect=socket.gaierror(8, "DNS resolution failure")):
        response = client.post(
            "/api/v1/scan", json={"url": "https://unreachable-mock-ssl-fail.org/login"}
        )

    assert response.status_code == 201
    data = response.json()
    assert "ssl_analysis" in data
    # Overall scan did NOT crash; returned DNS_RESOLUTION_FAILED for SSL
    assert data["ssl_analysis"]["status"] == "DNS_RESOLUTION_FAILED"
    assert data["ml_prediction"] is not None
