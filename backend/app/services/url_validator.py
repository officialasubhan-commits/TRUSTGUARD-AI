"""
URL Validation Service for TrustGuard AI.
Performs rigorous static validation of URL structure, schemes, hostnames, and ports.
Enforces SSRF prevention by statically rejecting private IPs, loopbacks, and cloud metadata targets.
Never executes or fetches URL content.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Dict, Optional
from urllib.parse import urlparse

from app.core.config import settings

_ALLOWED_SCHEMES = {"http", "https"}
_DISALLOWED_SCHEMES = {
    "file",
    "javascript",
    "data",
    "ftp",
    "gopher",
    "blob",
    "vbscript",
    "ws",
    "wss",
    "ldap",
    "dict",
    "tftp",
}

# Cloud metadata endpoints and known internal hostnames
_BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "169.254.169.254",
    "instance-data",
    "metadata.azure.com",
}

# RFC private, loopback, and reserved IP ranges (checked statically)
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


class ValidationResult:
    """Encapsulates the outcome of static URL validation."""

    def __init__(
        self,
        is_valid: bool,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, str]] = None,
    ) -> None:
        self.is_valid = is_valid
        self.error_message = error_message
        self.error_code = error_code
        self.details = details or {}

    def __bool__(self) -> bool:
        return self.is_valid

    def __repr__(self) -> str:
        return f"<ValidationResult is_valid={self.is_valid} error={self.error_code}>"


def validate_url_static(url: str) -> ValidationResult:
    """
    Statically validates a submitted URL string without performing network requests.

    Validation checks:
    1. String presence, type, and max length constraint (<= 2048 chars).
    2. Disallow raw control characters (ASCII < 32 or == 127).
    3. Scheme validation (strictly http or https).
    4. Hostname extraction and structural validation.
    5. Port validation (must be 1-65535).
    6. SSRF prevention: statically blocks IP literals in private/loopback/metadata ranges.
    7. Blocks dangerous schemes (file, javascript, data, etc.).
    8. Validates percent-encoding syntax.
    """
    if not url or not isinstance(url, str):
        return ValidationResult(
            is_valid=False,
            error_message="URL cannot be empty.",
            error_code="EMPTY_URL",
        )

    cleaned = url.strip()

    # 1. Length constraint
    if len(cleaned) > settings.URL_MAX_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message=f"URL exceeds maximum allowed length of {settings.URL_MAX_LENGTH} characters.",
            error_code="URL_TOO_LONG",
        )

    if len(cleaned) < 3:
        return ValidationResult(
            is_valid=False,
            error_message="URL is too short to be valid.",
            error_code="URL_TOO_SHORT",
        )

    # 2. Control characters & whitespace check
    if any(ord(c) < 32 or ord(c) == 127 for c in cleaned):
        return ValidationResult(
            is_valid=False,
            error_message="URL contains invalid control characters.",
            error_code="INVALID_CHARACTERS",
        )

    if " " in cleaned:
        return ValidationResult(
            is_valid=False,
            error_message="URL must not contain unencoded whitespace characters.",
            error_code="INVALID_WHITESPACE",
        )

    # 3. Percent-encoding check (no malformed %XX)
    if re.search(r"%[^0-9a-fA-F]|%[0-9a-fA-F]?$", cleaned):
        return ValidationResult(
            is_valid=False,
            error_message="URL contains malformed percent-encoding.",
            error_code="MALFORMED_PERCENT_ENCODING",
        )

    # 4. Scheme check
    parsed = urlparse(cleaned)
    raw_scheme = parsed.scheme.lower() if parsed.scheme else ""

    if not raw_scheme:
        # Check if the user entered scheme-less URL (e.g. 'example.com')
        # Treat as malformed if it has no scheme or scheme syntax
        if not re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", cleaned):
            return ValidationResult(
                is_valid=False,
                error_message="URL must include a valid HTTP or HTTPS protocol scheme (e.g., https://example.com).",
                error_code="MISSING_SCHEME",
            )
        # Re-parse with prepended https for validation
        parsed = urlparse(f"https://{cleaned}")
        raw_scheme = "https"

    if raw_scheme in _DISALLOWED_SCHEMES:
        return ValidationResult(
            is_valid=False,
            error_message=f"URL scheme '{raw_scheme}' is not allowed for security reasons. Only HTTP and HTTPS are supported.",
            error_code="UNSUPPORTED_SCHEME",
        )

    if raw_scheme not in _ALLOWED_SCHEMES:
        return ValidationResult(
            is_valid=False,
            error_message=f"Unsupported scheme '{raw_scheme}'. Only HTTP and HTTPS are permitted.",
            error_code="INVALID_SCHEME",
        )

    # 5. Hostname check
    hostname = parsed.hostname
    if not hostname:
        return ValidationResult(
            is_valid=False,
            error_message="URL does not contain a valid hostname.",
            error_code="MISSING_HOSTNAME",
        )

    lowered_hostname = hostname.lower().rstrip(".")

    # SSRF: Blocked hostname names
    if lowered_hostname in _BLOCKED_HOSTNAMES:
        return ValidationResult(
            is_valid=False,
            error_message=f"Access to hostname '{lowered_hostname}' is blocked for security reasons (SSRF protection).",
            error_code="BLOCKED_HOSTNAME_SSRF",
        )

    # 6. Static IP literal check (IPv4 & IPv6)
    try:
        ip_obj = ipaddress.ip_address(lowered_hostname)
        # Check against private / loopback / link-local / reserved networks
        for net in _BLOCKED_NETWORKS:
            if ip_obj in net:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"IP address '{lowered_hostname}' belongs to a private, loopback, or reserved network range and cannot be scanned.",
                    error_code="PRIVATE_IP_SSRF",
                )
    except ValueError:
        # Not an IP literal — validate domain syntax
        # Domain must contain at least one dot or be a valid FQDN
        if "." not in lowered_hostname and lowered_hostname != "localhost":
            return ValidationResult(
                is_valid=False,
                error_message=f"Hostname '{lowered_hostname}' must be a fully qualified domain name with a valid top-level domain.",
                error_code="INVALID_DOMAIN_SYNTAX",
            )

        # Hostname character validation (RFC 1123)
        # Allow punycode prefixes (xn--) and valid domain labels
        labels = lowered_hostname.split(".")
        for label in labels:
            if not label:
                return ValidationResult(
                    is_valid=False,
                    error_message="Hostname contains empty domain labels.",
                    error_code="INVALID_DOMAIN_LABELS",
                )
            if len(label) > 63:
                return ValidationResult(
                    is_valid=False,
                    error_message="Domain label exceeds maximum 63 characters.",
                    error_code="DOMAIN_LABEL_TOO_LONG",
                )
            if not re.match(r"^[a-zA-Z0-9_-]+$", label):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Domain label '{label}' contains invalid characters.",
                    error_code="INVALID_DOMAIN_CHARACTERS",
                )

    # 7. Port validation
    try:
        port = parsed.port
    except ValueError:
        return ValidationResult(
            is_valid=False,
            error_message="URL contains an invalid or out-of-range port number (must be 1-65535).",
            error_code="INVALID_PORT_RANGE",
        )

    if port is not None:
        if not (1 <= port <= 65535):
            return ValidationResult(
                is_valid=False,
                error_message=f"Port '{port}' is outside the valid range (1-65535).",
                error_code="INVALID_PORT_RANGE",
            )

    return ValidationResult(is_valid=True)
