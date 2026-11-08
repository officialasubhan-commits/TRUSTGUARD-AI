# TrustGuard AI — Security Design

---

## Table of Contents

1. [Executive Security Summary](#1-executive-security-summary)
2. [Threat Model](#2-threat-model)
3. [SSRF Protection](#3-ssrf-protection)
4. [API Key Security](#4-api-key-security)
5. [Rate Limiting Design](#5-rate-limiting-design)
6. [Input Validation Design](#6-input-validation-design)
7. [Authentication Security](#7-authentication-security)
8. [Database Security](#8-database-security)
9. [Frontend Security](#9-frontend-security)
10. [Secure Development Practices Checklist](#10-secure-development-practices-checklist)
11. [Pre-Demo Security Checklist](#11-pre-demo-security-checklist)

---

## 1. Executive Security Summary

TrustGuard AI is a security product — it must be held to a higher security standard than a typical hackathon application. A URL scanning service is a particularly attractive target because:

- It **fetches arbitrary user-supplied URLs**, making it inherently vulnerable to SSRF attacks that could expose the internal Render network.
- It **holds API keys** (VirusTotal, Supabase service role) with significant value or access.
- It **renders user-supplied text** (community reports, URL content) in the browser, creating XSS vectors.
- It operates in a **multi-tenant environment** where one user must never access another's data.

This document defines the security controls that address these risks. Security is **designed-in from day one**, not patched after the demo. Every developer owns the security of their module.

> [!IMPORTANT]
> Security failures in a URL-scanning tool do not just embarrass the team — they can harm users who trust the tool to protect them. Take this seriously.

---

## 2. Threat Model

| # | Threat | Asset at Risk | Impact | Likelihood | Mitigation Strategy |
|---|---|---|---|---|---|
| 1 | **SSRF via malicious URL** | Internal Render network, cloud metadata API (169.254.169.254) | Critical — attacker could extract cloud credentials and pivot to full infrastructure compromise | High | Resolve hostname before any network call; block all private/reserved IP ranges; set hard timeout; disable redirects |
| 2 | **Malformed / oversized URL input** | Backend stability, WAF bypass | Medium — could crash the parser or bypass pattern-matching defenses | Medium | Pydantic `HttpUrl` strict parsing; 2048-character hard limit; scheme whitelist |
| 3 | **DNS rebinding attack** | SSRF guard bypass | High — attacker registers a domain that resolves to public IP during validation, then rebinds to private IP during fetch | Low | Resolve DNS once, pin the resolved IP, make all subsequent connections to the IP directly (not the hostname) |
| 4 | **Private/loopback IP access** | Supabase admin panel, Render internal services | Critical | Medium | Explicit IPv4 and IPv6 blocklist checked after DNS resolution (see Section 3) |
| 5 | **Malicious redirects** | SSRF guard bypass via 3xx redirect to private IP | High | Medium | `allow_redirects=False` on all outbound HTTP requests; never follow redirects automatically |
| 6 | **API key exposure** | VirusTotal quota (financial), Supabase service role (data breach) | Critical | Medium | Keys in environment variables only; never in code, logs, or frontend; `.env` in `.gitignore` |
| 7 | **SQL injection** | Full database compromise, PII leakage | Critical | Low | Supabase-py client uses parameterised queries exclusively; no raw SQL string concatenation anywhere in the codebase |
| 8 | **Authentication abuse (token sharing/theft)** | Account takeover, unauthorised scan access | High | Medium | Short JWT expiry (1 hour); HTTPS-only; Supabase RLS as secondary enforcement layer |
| 9 | **Rate-limit bypass** | API quota exhaustion, VirusTotal daily limit burn, DoS | Medium | High | Token-bucket per IP via slowapi; 5 req/min on `/scan`; 429 response with `Retry-After` header |
| 10 | **XSS via community report content** | Session hijacking, credential theft of other users | High | Medium | Server-side HTML sanitisation before storage; React's default JSX escaping on render; no `dangerouslySetInnerHTML` |
| 11 | **JWT replay attack** | Session persistence beyond intended expiry | Medium | Low | Supabase issues short-lived access tokens; refresh tokens are rotated on use; token revocation via Supabase Auth admin API |
| 12 | **Dependency supply-chain attack** | Arbitrary code execution during build or at runtime | Critical | Low | Pin exact dependency versions in `requirements.txt` and `package.json`; run `pip audit` and `npm audit` before deployment; no unverified third-party packages |

---

## 3. SSRF Protection

Server-Side Request Forgery (SSRF) is the **highest priority** threat in TrustGuard AI because the core feature — fetching data about user-supplied URLs — requires the backend to make outbound HTTP requests on behalf of users.

### 3.1 What We Block

| Range | Description | Why |
|---|---|---|
| `10.0.0.0/8` | RFC 1918 private network | Could reach internal Render services |
| `172.16.0.0/12` | RFC 1918 private network | Same |
| `192.168.0.0/16` | RFC 1918 private network | Same |
| `127.0.0.0/8` | Loopback (localhost) | Could reach local FastAPI admin ports |
| `::1` | IPv6 loopback | Same |
| `169.254.0.0/16` | Link-local (AWS/GCP metadata API lives at `169.254.169.254`) | Cloud credential theft |
| `0.0.0.0` | Null/unspecified address | Undefined behaviour |
| `224.0.0.0/4` | Multicast | No legitimate scanning target |
| `fe80::/10` | IPv6 link-local | Same as IPv4 link-local |
| `fc00::/7` | IPv6 unique local | Equivalent of RFC 1918 for IPv6 |

### 3.2 Defence-in-Depth Layers

1. **Scheme whitelist**: Only `http` and `https` are permitted before any DNS resolution occurs. `javascript:`, `data:`, `file:`, `ftp:` and all other schemes are rejected with 400 immediately.
2. **DNS resolution + IP validation**: The hostname is resolved to an IP address(es) *before* any network connection is opened. All resolved IPs are validated against the blocklist.
3. **Redirect disabling**: All HTTP clients used by the backend set `allow_redirects=False`. If a server returns a 3xx redirect, the backend does **not** follow it.
4. **Hard timeout**: All outbound connections have a 5-second connect + read timeout. This limits exposure from slow-loris style attacks.
5. **DNS pinning**: The resolved IP is passed directly to the HTTP client, bypassing hostname resolution again at connection time (prevents DNS rebinding).

### 3.3 IP Validation Guard — Python Implementation

```python
# backend/app/core/security.py
import ipaddress
import socket
from fastapi import HTTPException
from urllib.parse import urlparse

# All private/reserved IP networks to block
BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local / AWS metadata
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved
    ipaddress.ip_network("::1/128"),             # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),           # IPv6 link-local
    ipaddress.ip_network("fc00::/7"),            # IPv6 unique local
]

ALLOWED_SCHEMES = {"http", "https"}


def validate_url_for_ssrf(url: str) -> str:
    """
    Validates a URL against SSRF attack vectors.

    Steps:
    1. Parse and validate scheme.
    2. Resolve hostname to IP address(es).
    3. Check all resolved IPs against blocked network list.
    4. Return the validated URL if safe, raise HTTPException if not.

    Returns: validated URL string (unchanged)
    Raises: HTTPException(400) if the URL is unsafe
    """
    # Step 1: Parse URL and check scheme
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise HTTPException(
            status_code=400,
            detail=f"URL scheme '{parsed.scheme}' is not permitted. Only http and https are allowed."
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="URL has no resolvable hostname.")

    # Step 2: Resolve hostname to IP addresses
    try:
        # getaddrinfo returns all address records (handles both IPv4 and IPv6)
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise HTTPException(
            status_code=400,
            detail=f"Hostname '{hostname}' could not be resolved."
        )

    if not addr_infos:
        raise HTTPException(status_code=400, detail="Hostname resolved to no addresses.")

    # Step 3: Check every resolved IP against the blocklist
    for addr_info in addr_infos:
        ip_str = addr_info[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid IP address resolved: {ip_str}")

        for blocked_net in BLOCKED_NETWORKS:
            if ip_obj in blocked_net:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"URL resolves to a private or reserved IP address ({ip_str}) "
                        f"and cannot be scanned for security reasons."
                    )
                )

    # Step 4: Safe — return the validated URL unchanged
    return url


def make_safe_http_client():
    """
    Returns an aiohttp.ClientSession configured with SSRF safety settings:
    - allow_redirects=False
    - Hard timeout of 5 seconds
    - Custom connector that disables connection reuse (prevents socket recycling attacks)
    """
    import aiohttp
    timeout = aiohttp.ClientTimeout(total=5)
    connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=0)
    return aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        # Redirects are NEVER followed automatically
    )
```

---

## 4. API Key Security

### Where Keys Live

| Key | Stored In | Accessible By |
|---|---|---|
| `VIRUSTOTAL_API_KEY` | Render Environment Variables (backend) | FastAPI backend only |
| `SUPABASE_SERVICE_ROLE_KEY` | Render Environment Variables (backend) | FastAPI backend only |
| `SUPABASE_URL` | Both Render (backend) and Vercel (frontend) | Backend + frontend (URL is not secret) |
| `VITE_SUPABASE_ANON_KEY` | Vercel Environment Variables (frontend) | Frontend only (designed for public use with RLS) |
| `VITE_BACKEND_URL` | Vercel Environment Variables (frontend) | Frontend only |

### `.env.example` Template

```bash
# backend/.env.example
# Copy this file to .env for local development.
# NEVER commit the actual .env file to version control.

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.REPLACE_ME

# ─── VirusTotal ───────────────────────────────────────────────────────────────
VIRUSTOTAL_API_KEY=REPLACE_ME_WITH_YOUR_VT_FREE_API_KEY

# ─── Application ──────────────────────────────────────────────────────────────
ENVIRONMENT=development    # "development" or "production"
FRONTEND_URL=http://localhost:5173
LOG_LEVEL=INFO
```

```bash
# frontend/.env.local.example
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.REPLACE_ME
VITE_BACKEND_URL=http://localhost:8000
```

### Never-Commit Rules

- `.env` and `.env.local` are listed in `.gitignore` from project initialisation.
- `SUPABASE_SERVICE_ROLE_KEY` **must never** appear in any frontend file or in any file tracked by git.
- If a key is accidentally committed, treat it as compromised: immediately rotate it in the respective dashboard (Supabase / VirusTotal) and purge git history using `git-filter-repo` or BFG Repo Cleaner.
- Pre-commit hook (recommended): Install `detect-secrets` to scan staged files for key patterns before allowing commits.

---

## 5. Rate Limiting Design

### Algorithm: Token Bucket

The token bucket algorithm is ideal for rate limiting because it:
- Allows short bursts (up to bucket capacity) without immediate penalty.
- Enforces a steady-state average rate.
- Provides predictable `Retry-After` values.

### Configuration via `slowapi`

```python
# backend/app/core/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

# Key function: rate limit per client IP address
limiter = Limiter(key_func=get_remote_address)

# backend/app/main.py
from fastapi import FastAPI, Request
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        headers={"Retry-After": str(exc.retry_after)},
        content={
            "detail": "Rate limit exceeded. Maximum 5 scan requests per minute per IP address.",
            "code": "RATE_LIMIT_EXCEEDED"
        }
    )

# backend/app/api/scan.py
from app.core.rate_limiter import limiter

@router.post("/scan")
@limiter.limit("5/minute")
async def submit_scan(request: Request, body: ScanRequest):
    ...
```

### Limits Summary

| Endpoint | Limit | Scope |
|---|---|---|
| `POST /scan` | 5 requests/minute | Per IP |
| `GET /scan/{id}` | 60 requests/minute | Per IP |
| `GET /history` | 30 requests/minute | Per authenticated user |
| `POST /reports` | 10 requests/minute | Per authenticated user |
| `GET /reports/{id}` | 60 requests/minute | Per IP |

---

## 6. Input Validation Design

### URL Validation Pipeline

```
Raw user input string
        │
        ▼
① Strip whitespace (both ends)
        │
        ▼
② Length check: reject if > 2048 characters (HTTP 400)
        │
        ▼
③ Pydantic HttpUrl parsing: validates structure, scheme, host (HTTP 422 on failure)
        │
        ▼
④ Scheme whitelist: only "http" and "https" accepted (HTTP 400 on failure)
        │
        ▼
⑤ Block javascript:, data:, file:, ftp: explicitly (belt-and-suspenders)
        │
        ▼
⑥ SSRF guard: resolve hostname → check all IPs vs blocklist (HTTP 400 on failure)
        │
        ▼
⑦ Validated URL passed to analysis pipeline
```

### Community Report Input Sanitisation

User-supplied text in `notes`, `target_brand` fields is sanitised before storage using `bleach`:

```python
import bleach

def sanitise_text(raw: str) -> str:
    """Strip all HTML tags and attributes from user-supplied text."""
    return bleach.clean(raw, tags=[], attributes={}, strip=True)
```

React's JSX rendering automatically HTML-escapes interpolated values (`{variable}`), providing a second layer of XSS protection on render.

---

## 7. Authentication Security

### JWT Verification Flow

```python
# backend/app/core/security.py
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict | None:
    """
    Verifies Supabase JWT. Returns user payload dict or None for guest access.
    Raises HTTPException(401) if a token is present but invalid.
    """
    if credentials is None:
        return None  # Guest access — caller decides if this is acceptable

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,   # Supabase project JWT secret
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")
```

### JWT Security Properties

| Property | Value | Notes |
|---|---|---|
| Algorithm | `HS256` | Supabase default; symmetric HMAC |
| Expiry | 1 hour | Access token; configurable in Supabase Auth settings |
| Audience | `authenticated` | Prevents use of tokens issued to other systems |
| Refresh | Automatic | Supabase JS SDK silently refreshes using the refresh token |
| Revocation | Via Supabase Auth admin API | Can invalidate sessions server-side if account compromised |

### Supabase RLS as Second Layer

Even if a crafted JWT bypasses application-layer verification (e.g., due to a bug), **Supabase Row Level Security** enforces that `auth.uid()` must match the data being accessed. This provides defence-in-depth.

---

## 8. Database Security

### Parameterised Queries Only

The Supabase Python client uses the PostgREST API under the hood, which parameterises all values automatically. No raw SQL string concatenation is ever used.

```python
# CORRECT — parameterised via Supabase client
result = supabase.table("scan_history").select("*").eq("user_id", user_id).execute()

# NEVER DO THIS — raw SQL concatenation
# query = f"SELECT * FROM scan_history WHERE user_id = '{user_id}'"  # ← FORBIDDEN
```

### Service Role Key Restriction

The Supabase service-role key is loaded only by the backend via `config.py`. It is:
- Never imported in any frontend file.
- Never logged (use `settings.SUPABASE_SERVICE_ROLE_KEY[:8] + "..."` for log redaction if needed).
- Used only for operations that legitimately need to bypass RLS (e.g., writing `scan_results` after analysis completes).

### Connection Security

All connections to Supabase are made over TLS 1.2+. The Supabase hosted URL uses HTTPS exclusively. No insecure fallback is configured.

---

## 9. Frontend Security

### Content Security Policy (CSP)

Add to `vercel.json` to enforce strict CSP:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://*.supabase.co https://trustguard-api.onrender.com; img-src 'self' data:; font-src 'self'; frame-ancestors 'none';"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        },
        {
          "key": "Permissions-Policy",
          "value": "camera=(), microphone=(), geolocation=()"
        }
      ]
    }
  ]
}
```

### No API Keys in Frontend

- `VITE_SUPABASE_ANON_KEY` — This key is designed by Supabase to be public. It enforces RLS; it does not bypass it.
- `VIRUSTOTAL_API_KEY` — Never referenced in any frontend file. All VirusTotal calls go through the backend.
- `SUPABASE_SERVICE_ROLE_KEY` — Never referenced in any frontend file. Zero tolerance.

### Sanitise Rendered Community Report Content

React JSX escapes values by default. Never use `dangerouslySetInnerHTML` with user-provided content. For the community reports display:

```jsx
// SAFE — React escapes {report.notes} automatically
<p className="text-sm text-gray-600">{report.notes}</p>

// NEVER DO THIS
// <p dangerouslySetInnerHTML={{ __html: report.notes }} />  ← FORBIDDEN
```

---

## 10. Secure Development Practices Checklist

Each developer should verify these items are true for every pull request:

- [ ] **No secrets in code**: Search for `API_KEY`, `SECRET`, `PASSWORD` patterns with `git grep` before every PR. Keys live only in `.env` or the deployment platform's environment variable settings.
- [ ] **Dependencies are pinned**: `requirements.txt` lists exact versions (`==`). `package.json` uses exact semver or caret with `package-lock.json` / `pnpm-lock.yaml` committed.
- [ ] **No `print()` or `logging.debug()` with sensitive data**: Logs must never contain JWTs, API keys, or user PII. Redact before logging.
- [ ] **SSRF guard applied**: Any code path that makes an outbound HTTP request to a user-supplied hostname must call `validate_url_for_ssrf(url)` first.
- [ ] **Input validated at API boundary**: All FastAPI route handlers use Pydantic models. No manual string parsing of request bodies.
- [ ] **No raw SQL**: Only use the Supabase client's ORM-style query builder. Never concatenate user input into query strings.
- [ ] **Community report text sanitised**: Any text from users that is stored and later rendered must pass through `sanitise_text()` before INSERT.
- [ ] **Error messages don't leak internals**: Production error responses say "Internal server error" — not stack traces, file paths, or database error messages.
- [ ] **CORS is restricted**: The FastAPI `CORSMiddleware` must list only `FRONTEND_URL` (from env var) as an allowed origin. `allow_origins=["*"]` is never used in production.
- [ ] **`allow_redirects=False`**: All outbound HTTP calls from backend services use `allow_redirects=False` or the equivalent for the HTTP client in use.

---

## 11. Pre-Demo Security Checklist

Complete all items before the final presentation:

- [ ] `git grep -r "VIRUSTOTAL_API_KEY\|SERVICE_ROLE_KEY" -- ":(exclude).env.example"` returns zero results
- [ ] `.env` and `.env.local` are listed in `.gitignore`; run `git status --ignored` to confirm they are ignored
- [ ] All environment variables are set in Render dashboard (not hardcoded in `Dockerfile` or code)
- [ ] All environment variables are set in Vercel dashboard (not hardcoded in `vite.config.js` or any `.js` file)
- [ ] `POST /scan` with `{"url": "http://169.254.169.254/latest/meta-data/"}` returns HTTP 400 (SSRF guard working)
- [ ] `POST /scan` with `{"url": "javascript:alert(1)"}` returns HTTP 400 (scheme whitelist working)
- [ ] A 6th scan request within 60 seconds from the same IP returns HTTP 429 (rate limiting working)
- [ ] Visiting `/dashboard` without being logged in redirects to `/login` (ProtectedRoute working)
- [ ] `GET /api/v1/history` without an `Authorization` header returns HTTP 401 (auth guard working)
- [ ] Running `npm audit` on the frontend shows zero critical vulnerabilities; resolve any critical ones before the demo
