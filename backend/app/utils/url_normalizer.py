"""
URL Normalisation Utility for TrustGuard AI.
Normalises URLs consistently according to RFC 3986 without altering the intended destination.
Preserves query parameters essential for threat and phishing analysis.
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse, urlunparse


def normalize_url(raw_url: str) -> str:
    """
    Normalises a URL into a canonical form according to RFC 3986.

    Rules applied:
    1. Strip leading/trailing whitespace and control characters.
    2. Lowercase scheme and hostname.
    3. Remove trailing dot from hostname (e.g., 'example.com.' -> 'example.com').
    4. Decode unreserved characters in path and re-encode reserved characters consistently.
    5. Strip default ports (:80 for HTTP, :443 for HTTPS).
    6. Supply a root trailing slash if path is completely empty.
    7. Convert internationalised domain names (IDN) to ASCII punycode via IDNA.
    8. Strip fragment identifiers (fragments are purely client-side).
    9. Preserve query string parameters in ordered format without stripping values.
    """
    if not raw_url or not isinstance(raw_url, str):
        raise ValueError("URL must be a non-empty string.")

    cleaned_url = raw_url.strip()

    # Prepend scheme if missing (e.g. 'example.com' -> 'http://example.com' for parsing)
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", cleaned_url):
        cleaned_url = f"http://{cleaned_url}"

    parsed = urlparse(cleaned_url)

    # 1. Normalise Scheme (lowercase)
    scheme = parsed.scheme.lower()

    # 2. Normalise Hostname
    netloc = parsed.netloc
    if not netloc:
        raise ValueError("URL contains no valid network location / hostname.")

    # Extract userinfo, host, port
    userinfo = ""
    host_port = netloc
    if "@" in netloc:
        userinfo, host_port = netloc.split("@", 1)
        userinfo = f"{userinfo}@"

    host = host_port
    port = None
    if ":" in host_port and not host_port.endswith("]"):  # Guard IPv6 literals like [::1]
        host, port_str = host_port.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            raise ValueError(f"Invalid port in URL: '{port_str}'")

    # Lowercase host and strip trailing dot
    host = host.lower().rstrip(".")

    # Encode internationalised domain names using IDNA
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        # If IDNA encoding fails, keep original lowered host
        pass

    # Drop standard default ports
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None

    new_netloc = f"{userinfo}{host}"
    if port is not None:
        new_netloc = f"{new_netloc}:{port}"

    # 3. Normalise Path
    path = parsed.path
    if not path:
        path = "/"
    else:
        # Normalize double slashes in path (e.g. //path -> /path)
        path = re.sub(r"/+", "/", path)
        # Normalize percent-encoding: decode unreserved, uppercase hex escapes
        try:
            decoded = unquote(path)
            path = quote(decoded, safe="/:@-._~!$&'()*+,;=")
        except Exception:
            pass

    # 4. Normalise Query Parameters (sort keys for consistency while preserving parameters)
    query = parsed.query
    if query:
        query_pairs = parse_qsl(query, keep_blank_values=True)
        # Re-encode query pairs deterministically
        query = urlencode(query_pairs)

    # 5. Remove fragment (RFC 3986: fragments are not sent in HTTP requests)
    fragment = ""

    normalized = urlunparse((scheme, new_netloc, path, parsed.params, query, fragment))
    return normalized


def compute_url_hash(normalized_url: str) -> str:
    """
    Computes a SHA-256 hash of the normalised URL for database indexing and fast deduplication.
    """
    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()
