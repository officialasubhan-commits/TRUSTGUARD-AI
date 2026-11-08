"""
SSL/TLS Certificate Validation & Security Assessment Engine.

Validates HTTPS certificates for user-submitted URLs using Python's standard
ssl and socket libraries. Implements strict DNS resolution protection,
SSRF mitigation (blocking private/loopback/cloud metadata targets),
direct-IP connection with SNI preservation, validity period checking,
protocol negotiation inspection, and in-memory response caching.

Security Advisory:
A valid SSL/TLS certificate does NOT prove that a website is trustworthy;
phishing operations frequently use valid DV (Domain Validated) certificates.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
import ssl
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.core.config import settings
from app.core.security import _is_private_ip
from app.schemas.ssl import SSLStatusType, SSLValidationResponse
from app.services.url_validator import _BLOCKED_HOSTNAMES

logger = logging.getLogger("trustguard.service.ssl_tls")


class SSLValidationService:
    """Service providing secure, SSRF-guarded SSL/TLS certificate inspection."""

    # In-memory certificate cache: {hostname: (cached_at_datetime, response_object)}
    _cache: Dict[str, Tuple[datetime, SSLValidationResponse]] = {}

    def __init__(self, timeout_seconds: Optional[float] = None):
        self._timeout = timeout_seconds or settings.SSL_CONNECTION_TIMEOUT

    @staticmethod
    def _extract_hostname(url_or_host: str) -> Tuple[str, str]:
        """
        Extracts normalized scheme and hostname from a submitted URL or domain string.
        Returns: (scheme, hostname)
        """
        raw = url_or_host.strip()
        if "://" not in raw:
            # Default assumption if only host provided
            return "https", raw.lower()

        parsed = urlparse(raw)
        scheme = (parsed.scheme or "https").lower()
        hostname = (parsed.hostname or "").lower()
        return scheme, hostname

    @staticmethod
    def _parse_dn_tuple(dn_tuple: Any) -> str:
        """
        Converts Python SSL distinguished name tuples into a readable string:
        e.g. ((('organizationName', 'DigiCert Inc'),), (('commonName', 'DigiCert CA'),))
        """
        if not dn_tuple or not isinstance(dn_tuple, (tuple, list)):
            return "Unknown"

        dn_parts: Dict[str, str] = {}
        for rdn in dn_tuple:
            for item in rdn:
                if isinstance(item, tuple) and len(item) == 2:
                    dn_parts[item[0]] = str(item[1])

        # Prefer Organization + Common Name
        org = dn_parts.get("organizationName")
        cn = dn_parts.get("commonName")
        if org and cn and org != cn:
            return f"{org} ({cn})"
        if org:
            return org
        if cn:
            return cn
        return ", ".join(f"{k}={v}" for k, v in dn_parts.items()) or "Unknown"

    def _get_from_cache(self, hostname: str) -> Optional[SSLValidationResponse]:
        """Retrieves cached certificate evaluation if unexpired."""
        if hostname in self._cache:
            cached_at, report = self._cache[hostname]
            ttl = timedelta(seconds=settings.SSL_CACHE_TTL_SECONDS)
            if datetime.now(timezone.utc) - cached_at < ttl:
                logger.debug("SSL cache hit for hostname: %s", hostname)
                return report.model_copy(update={"cached": True})
            del self._cache[hostname]
        return None

    def _store_in_cache(self, hostname: str, report: SSLValidationResponse) -> None:
        """Stores report in cache."""
        self._cache[hostname] = (datetime.now(timezone.utc), report)

    async def validate_url_ssl(self, url: str) -> SSLValidationResponse:
        """
        Validates the SSL/TLS certificate of the target URL with SSRF protection.

        Workflow:
        1. Parse scheme and host. If scheme is 'http', return HTTPS_NOT_USED immediately.
        2. Validate host statically against internal hostnames and cloud metadata.
        3. Resolve DNS records and verify that EVERY resolved IP address is public.
        4. Connect directly to the validated IP on port 443 while preserving
           the original hostname for TLS SNI and certificate verification.
        5. Verify trust chain, expiration dates, protocol versions, and cipher suites.
        """
        scheme, hostname = self._extract_hostname(url)

        # 1. Scheme Check
        if scheme == "http":
            return SSLValidationResponse(
                status="HTTPS_NOT_USED",
                https_enabled=False,
                hostname=hostname,
                hostname_verified=False,
                certificate_trusted=False,
                ssl_subscore=50,
                findings=[
                    "Website uses unencrypted HTTP protocol; user communications are vulnerable to eavesdropping."
                ],
                message="Target website uses plain unencrypted HTTP. HTTPS is not enabled.",
            )

        if not hostname:
            return SSLValidationResponse(
                status="UNKNOWN",
                https_enabled=False,
                hostname="",
                ssl_subscore=0,
                findings=["URL does not contain a valid hostname."],
                message="Cannot validate SSL: missing hostname.",
            )

        # 2. Check Cache
        cached_result = self._get_from_cache(hostname)
        if cached_result:
            return cached_result

        # 3. Static Hostname Safety Check
        if hostname in _BLOCKED_HOSTNAMES or hostname.startswith("127.") or hostname == "localhost":
            report = SSLValidationResponse(
                status="UNSAFE_DESTINATION",
                https_enabled=True,
                hostname=hostname,
                ssl_subscore=0,
                findings=[
                    "Target hostname refers to internal, loopback, or cloud metadata network space."
                ],
                error_code="SSRF_STATIC_BLOCKED",
                message="Destination is a restricted local or internal address.",
            )
            self._store_in_cache(hostname, report)
            return report

        # 4. DNS Resolution & SSRF Guard
        try:
            addr_infos = socket.getaddrinfo(hostname, 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror as e:
            logger.info("DNS resolution failed for hostname '%s': %s", hostname, e)
            report = SSLValidationResponse(
                status="DNS_RESOLUTION_FAILED",
                https_enabled=True,
                hostname=hostname,
                ssl_subscore=50,
                findings=[f"DNS lookup failed for hostname '{hostname}'."],
                error_code="DNS_GAI_ERROR",
                message="Could not resolve hostname to an IP address.",
            )
            self._store_in_cache(hostname, report)
            return report
        except Exception as e:
            logger.warning("Unexpected error during DNS resolution for '%s': %s", hostname, e)
            return SSLValidationResponse(
                status="DNS_RESOLUTION_FAILED",
                https_enabled=True,
                hostname=hostname,
                ssl_subscore=50,
                findings=[f"DNS resolution encountered an error: {e}"],
                error_code="DNS_ERROR",
                message="DNS resolution error.",
            )

        # Inspect ALL resolved IP addresses
        validated_sockaddr: Optional[Tuple[Any, ...]] = None
        validated_family = socket.AF_INET

        for family, _type, _proto, _canon, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                if (
                    ip_obj.is_private
                    or ip_obj.is_loopback
                    or ip_obj.is_link_local
                    or ip_obj.is_multicast
                    or ip_obj.is_reserved
                    or ip_obj.is_unspecified
                    or _is_private_ip(ip_str)
                ):
                    logger.warning(
                        "SSRF blocked: hostname '%s' resolved to non-public IP '%s'",
                        hostname,
                        ip_str,
                    )
                    report = SSLValidationResponse(
                        status="UNSAFE_DESTINATION",
                        https_enabled=True,
                        hostname=hostname,
                        ssl_subscore=0,
                        findings=[
                            f"Target resolved to non-public or reserved IP address ({ip_str})."
                        ],
                        error_code="SSRF_RESOLVED_PRIVATE_IP",
                        message="Connection blocked: hostname resolves to non-public network space.",
                    )
                    self._store_in_cache(hostname, report)
                    return report
            except ValueError:
                return SSLValidationResponse(
                    status="UNSAFE_DESTINATION",
                    https_enabled=True,
                    hostname=hostname,
                    ssl_subscore=0,
                    findings=["Unparseable IP address returned by DNS."],
                    error_code="UNPARSEABLE_IP",
                    message="Connection blocked: unparseable IP.",
                )

            if validated_sockaddr is None:
                validated_sockaddr = sockaddr
                validated_family = family

        if not validated_sockaddr:
            return SSLValidationResponse(
                status="DNS_RESOLUTION_FAILED",
                https_enabled=True,
                hostname=hostname,
                ssl_subscore=50,
                findings=["No usable network socket addresses resolved."],
                message="DNS returned zero usable socket addresses.",
            )

        # 5. Controlled TLS Connection
        report = self._perform_tls_handshake(
            hostname=hostname,
            sockaddr=validated_sockaddr,
            family=validated_family,
        )

        self._store_in_cache(hostname, report)
        return report

    def _perform_tls_handshake(
        self,
        hostname: str,
        sockaddr: Tuple[Any, ...],
        family: int,
    ) -> SSLValidationResponse:
        """
        Executes a secure TLS handshake connecting directly to the validated IP
        while verifying the certificate against the intended hostname via SNI.
        """
        raw_sock = None
        tls_sock = None

        try:
            # Create standard TLS context with default root CA trust store
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

            # Connect raw TCP socket directly to validated sockaddr (avoids DNS rebinding)
            raw_sock = socket.socket(family, socket.SOCK_STREAM)
            raw_sock.settimeout(self._timeout)
            raw_sock.connect(sockaddr)

            # Wrap socket with TLS; server_hostname sends SNI and validates cert match
            tls_sock = context.wrap_socket(raw_sock, server_hostname=hostname)

            # Retrieve negotiated security parameters
            tls_version = tls_sock.version()
            cipher_info = tls_sock.cipher()
            cipher_name = cipher_info[0] if cipher_info else None

            # Retrieve parsed peer certificate
            cert = tls_sock.getpeercert()
            if not cert:
                return SSLValidationResponse(
                    status="TLS_HANDSHAKE_FAILED",
                    https_enabled=True,
                    hostname=hostname,
                    ssl_subscore=30,
                    findings=["TLS connection completed but peer presented an empty certificate."],
                    error_code="EMPTY_CERTIFICATE",
                    message="Server presented no peer certificate.",
                )

            # Parse subject and issuer
            subject_str = self._parse_dn_tuple(cert.get("subject"))
            issuer_str = self._parse_dn_tuple(cert.get("issuer"))

            # Parse validity dates
            # Format: 'May 15 23:59:59 2025 GMT'
            date_format = "%b %d %H:%M:%S %Y %Z"
            valid_from = None
            valid_until = None

            if "notBefore" in cert:
                try:
                    valid_from = datetime.strptime(cert["notBefore"], date_format).replace(
                        tzinfo=timezone.utc
                    )
                except Exception:
                    pass

            if "notAfter" in cert:
                try:
                    valid_until = datetime.strptime(cert["notAfter"], date_format).replace(
                        tzinfo=timezone.utc
                    )
                except Exception:
                    pass

            now_utc = datetime.now(timezone.utc)
            days_remaining: Optional[int] = None
            if valid_until:
                days_remaining = (valid_until - now_utc).days

            # Determine Certificate Status
            findings: List[str] = []
            ssl_subscore = 100

            if days_remaining is not None and days_remaining < 0:
                status: SSLStatusType = "EXPIRED"
                ssl_subscore = 10
                findings.append(
                    f"Certificate expired on {valid_until.strftime('%Y-%m-%d')} ({abs(days_remaining)} days ago)."
                )
                message = f"SSL certificate expired {abs(days_remaining)} days ago."
            elif days_remaining is not None and days_remaining <= settings.SSL_EXPIRING_SOON_DAYS:
                status = "EXPIRING_SOON"
                ssl_subscore = 75
                findings.append(
                    f"Certificate expires in {days_remaining} days (threshold: {settings.SSL_EXPIRING_SOON_DAYS} days)."
                )
                message = (
                    f"SSL certificate is approaching expiration ({days_remaining} days remaining)."
                )
            else:
                status = "VALID"
                ssl_subscore = 100
                findings.append("Certificate chain is valid and trusted by public authorities.")
                findings.append(f"Negotiated modern protocol: {tls_version}.")
                message = "Valid and trusted SSL/TLS certificate."

            # Evaluate protocol version strength
            if tls_version in ("TLSv1", "TLSv1.1", "SSLv3", "SSLv2"):
                findings.append(f"Deprecated or weak TLS protocol negotiated: {tls_version}.")
                ssl_subscore = max(20, ssl_subscore - 30)

            return SSLValidationResponse(
                status=status,
                https_enabled=True,
                hostname=hostname,
                certificate_subject=subject_str,
                certificate_issuer=issuer_str,
                valid_from=valid_from,
                valid_until=valid_until,
                days_remaining=days_remaining,
                hostname_verified=True,
                certificate_trusted=True,
                tls_version=tls_version,
                cipher=cipher_name,
                ssl_subscore=ssl_subscore,
                findings=findings,
                message=message,
            )

        except ssl.SSLCertVerificationError as e:
            err_msg = str(e).lower()
            logger.info("SSL Certificate Verification Error for %s: %s", hostname, e)

            if "certificate has expired" in err_msg:
                return SSLValidationResponse(
                    status="EXPIRED",
                    https_enabled=True,
                    hostname=hostname,
                    hostname_verified=False,
                    certificate_trusted=False,
                    ssl_subscore=10,
                    findings=["Presented certificate is expired."],
                    error_code="CERT_EXPIRED",
                    message="SSL certificate has expired.",
                )
            elif (
                "doesn't match" in err_msg
                or "hostname" in err_msg
                or "certificate is not valid for" in err_msg
            ):
                return SSLValidationResponse(
                    status="HOSTNAME_MISMATCH",
                    https_enabled=True,
                    hostname=hostname,
                    hostname_verified=False,
                    certificate_trusted=False,
                    ssl_subscore=20,
                    findings=[
                        f"Certificate Subject Alternative Names do not match requested hostname '{hostname}'."
                    ],
                    error_code="HOSTNAME_MISMATCH",
                    message="SSL certificate does not match the requested domain name.",
                )
            elif (
                "self-signed" in err_msg
                or "unable to get local issuer certificate" in err_msg
                or "certificate verify failed" in err_msg
            ):
                return SSLValidationResponse(
                    status="UNTRUSTED_CERTIFICATE",
                    https_enabled=True,
                    hostname=hostname,
                    hostname_verified=False,
                    certificate_trusted=False,
                    ssl_subscore=25,
                    findings=[
                        "Certificate is self-signed or signed by an untrusted / unrecognized Certificate Authority."
                    ],
                    error_code="UNTRUSTED_ROOT",
                    message="SSL certificate is not trusted by public root authorities.",
                )
            else:
                return SSLValidationResponse(
                    status="TLS_HANDSHAKE_FAILED",
                    https_enabled=True,
                    hostname=hostname,
                    hostname_verified=False,
                    certificate_trusted=False,
                    ssl_subscore=30,
                    findings=[f"TLS certificate verification failed: {e}"],
                    error_code="VERIFICATION_FAILED",
                    message="TLS certificate verification failed.",
                )

        except (socket.timeout, TimeoutError):
            logger.info("Connection timeout during TLS handshake to %s", hostname)
            return SSLValidationResponse(
                status="TIMEOUT",
                https_enabled=True,
                hostname=hostname,
                ssl_subscore=50,
                findings=["Connection or TLS handshake timed out."],
                error_code="TIMEOUT",
                message="Connection timed out while negotiating SSL/TLS.",
            )

        except (ConnectionRefusedError, ConnectionResetError, OSError) as e:
            logger.info("Connection error connecting to %s: %s", hostname, e)
            return SSLValidationResponse(
                status="CONNECTION_ERROR",
                https_enabled=True,
                hostname=hostname,
                ssl_subscore=50,
                findings=[f"Network connection failed: {e}"],
                error_code="CONNECTION_REFUSED",
                message="Could not establish connection to port 443.",
            )

        except Exception as e:
            logger.warning("Unexpected SSL validation failure for %s: %s", hostname, e)
            return SSLValidationResponse(
                status="UNKNOWN",
                https_enabled=True,
                hostname=hostname,
                ssl_subscore=50,
                findings=[f"Unexpected error: {e}"],
                error_code="UNEXPECTED_ERROR",
                message="SSL/TLS check encountered an unexpected error.",
            )

        finally:
            if tls_sock:
                try:
                    tls_sock.close()
                except Exception:
                    pass
            elif raw_sock:
                try:
                    raw_sock.close()
                except Exception:
                    pass


# Global singleton instance
_ssl_service_instance: Optional[SSLValidationService] = None


def get_ssl_service() -> SSLValidationService:
    """Returns the cached singleton instance of SSLValidationService."""
    global _ssl_service_instance
    if _ssl_service_instance is None:
        _ssl_service_instance = SSLValidationService()
    return _ssl_service_instance
