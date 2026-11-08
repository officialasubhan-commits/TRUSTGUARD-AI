# TrustGuard AI — API Specification

**Version:** `v1`  
**Base URL (Production):** `https://trustguard-api.onrender.com/api/v1`  
**Base URL (Development):** `http://localhost:8000/api/v1`  
**OpenAPI Docs (auto-generated):** `{BASE_URL}/docs` (Swagger UI), `{BASE_URL}/redoc`

---

## Table of Contents

1. [Authentication Overview](#1-authentication-overview)
2. [Base URL & Conventions](#2-base-url--conventions)
3. [Endpoint Summary](#3-endpoint-summary)
4. [Endpoint Specifications](#4-endpoint-specifications)
   - [POST /scan](#41-post-scan)
   - [GET /scan/{scan_id}](#42-get-scanscan_id)
   - [GET /history](#43-get-history)
   - [POST /auth/register](#44-post-authregister)
   - [POST /reports](#45-post-reports)
   - [GET /reports/{scan_id}](#46-get-reportsscan_id)
5. [Complete Pydantic Schema Reference](#5-complete-pydantic-schema-reference)
6. [Async Polling Flow](#6-async-polling-flow)
7. [Error Handling Conventions](#7-error-handling-conventions)
8. [API Versioning Strategy](#8-api-versioning-strategy)

---

## 1. Authentication Overview

### Supabase JWT Bearer Tokens
TrustGuard AI uses **Supabase-issued JWTs** as the authentication mechanism. After a user signs in via the Supabase Auth SDK on the frontend, Supabase returns a short-lived access token (default: 1 hour expiry) and a refresh token.

The frontend **must** include this token in the `Authorization` header for all authenticated endpoints:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

The FastAPI backend verifies this JWT using Supabase's public key (fetched from the JWKS endpoint at startup). The `sub` claim in the JWT payload is the user's UUID, matching `users.id` in the database.

### Guest Access Pattern
Endpoints marked **Optional Auth** accept requests without an `Authorization` header. In this case:
- The backend treats the request as a guest scan.
- `scan_history.user_id` is set to `NULL`.
- `scan_history.is_guest` is set to `TRUE`.
- The returned `scan_id` is the only access credential for the scan result.

### Token Refresh
Token refresh is handled automatically by the Supabase JS SDK (`@supabase/supabase-js`). The frontend does not need to manually refresh tokens.

---

## 2. Base URL & Conventions

| Property | Value |
|---|---|
| **API Version Prefix** | `/api/v1` |
| **Content-Type** | `application/json` |
| **Date Format** | ISO 8601 UTC (`2026-11-07T12:00:00Z`) |
| **UUID Format** | RFC 4122 (e.g., `550e8400-e29b-41d4-a716-446655440000`) |
| **Score Range** | Integer 0–100 (0 = most dangerous, 100 = safest) |

---

## 3. Endpoint Summary

| # | Method | Path | Auth | Rate Limit | Description |
|---|---|---|---|---|---|
| 1 | `POST` | `/scan` | Optional | 5/min per IP | Submit a URL for analysis |
| 2 | `GET` | `/scan/{scan_id}` | Optional | 60/min per IP | Poll for scan status and results |
| 3 | `GET` | `/history` | Required | 30/min per user | List authenticated user's scan history |
| 4 | `POST` | `/auth/register` | None | 3/min per IP | Supabase-delegated registration (documented here for reference) |
| 5 | `POST` | `/reports` | Required | 10/min per user | Submit a community threat report |
| 6 | `GET` | `/reports/{scan_id}` | None | 60/min per IP | Retrieve community reports for a scan |

---

## 4. Endpoint Specifications

---

### 4.1 POST /scan

**Submit a URL for threat analysis.**

| Property | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/v1/scan` |
| **Authentication** | Optional (guest allowed) |
| **Rate Limit** | **5 requests per minute per IP** (enforced by token-bucket; exceeding returns 429) |
| **Content-Type** | `application/json` |

#### Request Body

```json
{
  "url": "https://suspicious-example.com/login?redirect=evil.com",
  "guest": false
}
```

#### Pydantic Model

```python
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class ScanRequest(BaseModel):
    url: HttpUrl = Field(
        ...,
        description="The URL to analyse. Must be http or https scheme.",
        max_length=2048
    )
    guest: bool = Field(
        default=False,
        description="Set to true if the user is not authenticated."
    )
```

#### Success Response — `202 Accepted`

```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "submitted_at": "2026-11-07T12:00:00Z",
  "message": "Scan accepted. Poll GET /api/v1/scan/550e8400-e29b-41d4-a716-446655440000 for results."
}
```

#### Error Responses

| HTTP Code | Condition |
|---|---|
| `400 Bad Request` | Malformed URL, unsupported scheme (javascript:, data:), URL exceeds 2048 characters |
| `400 Bad Request` | URL resolves to a private/loopback IP (SSRF guard triggered) |
| `401 Unauthorized` | `guest: false` supplied but no valid JWT in header |
| `422 Unprocessable Entity` | Request body fails Pydantic validation (missing field, wrong type) |
| `429 Too Many Requests` | Rate limit exceeded for this IP |
| `500 Internal Server Error` | Database write failure |

#### Validation Rules

- `url` must have scheme `http` or `https`. Any other scheme is rejected with 400.
- `url` must not exceed 2048 characters.
- The hostname must resolve to a public IP address. Private ranges (RFC 1918), loopback, link-local, and multicast are blocked.
- If `guest: false`, a valid JWT must be present in the `Authorization` header.
- Whitespace is stripped from the `url` field before validation.

#### Special Notes

> The endpoint returns `202 Accepted` immediately. Analysis runs asynchronously. The client must poll `GET /api/v1/scan/{scan_id}` to retrieve results. See [Section 6 — Async Polling Flow](#6-async-polling-flow) for the full polling protocol.

---

### 4.2 GET /scan/{scan_id}

**Poll for scan status and retrieve the full result when complete.**

| Property | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/v1/scan/{scan_id}` |
| **Authentication** | Optional (guest scans accessible via scan_id only) |
| **Rate Limit** | 60 requests per minute per IP |

#### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `scan_id` | UUID | The `scan_id` returned by `POST /scan` |

#### Success Response — `200 OK` (pending)

```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://suspicious-example.com/login",
  "status": "pending",
  "submitted_at": "2026-11-07T12:00:00Z",
  "completed_at": null,
  "result": null
}
```

#### Success Response — `200 OK` (complete)

```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://suspicious-example.com/login",
  "status": "complete",
  "submitted_at": "2026-11-07T12:00:00Z",
  "completed_at": "2026-11-07T12:00:07Z",
  "result": {
    "trust_score": 23,
    "risk_category": "HIGH",
    "vt": {
      "malicious": 12,
      "total": 72,
      "score": 20,
      "engines": {
        "Kaspersky": "malware",
        "Google Safebrowsing": "phishing"
      }
    },
    "ml": {
      "probability": 0.91,
      "label": "phishing",
      "score": 9,
      "features": {
        "url_length": 54,
        "num_subdomains": 2,
        "has_ip": false,
        "has_at_sign": false,
        "entropy": 4.21
      }
    },
    "ssl": {
      "valid": true,
      "issuer": "Let's Encrypt",
      "expiry": "2027-01-15T00:00:00Z",
      "days_remaining": 69,
      "score": 75
    },
    "url_heuristics": {
      "score": 30,
      "flags": [
        {"flag": "excessive_subdomains", "description": "URL has 4+ subdomain levels"},
        {"flag": "query_redirect", "description": "URL contains a redirect parameter"}
      ]
    },
    "score_breakdown": {
      "vt_weight": 0.4,
      "ml_weight": 0.3,
      "ssl_weight": 0.15,
      "url_weight": 0.15,
      "vt_contribution": 8.0,
      "ml_contribution": 2.7,
      "ssl_contribution": 11.25,
      "url_contribution": 4.5,
      "final_score": 23,
      "explanations": [
        "12/72 VirusTotal engines flagged this URL as malicious",
        "ML model predicts 91% phishing probability",
        "URL has suspicious redirect parameter"
      ]
    }
  }
}
```

#### Error Responses

| HTTP Code | Condition |
|---|---|
| `404 Not Found` | No scan with the given `scan_id` exists |
| `403 Forbidden` | Authenticated user requesting another user's non-guest scan |
| `422 Unprocessable Entity` | `scan_id` is not a valid UUID |

#### Validation Rules

- `scan_id` must be a valid UUID v4.
- For authenticated requests: the scan must belong to the requesting user, OR be a guest scan.
- For unauthenticated requests: only guest scans are accessible.

---

### 4.3 GET /history

**Retrieve the authenticated user's scan history, paginated and sorted by most recent.**

| Property | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/v1/history` |
| **Authentication** | **Required** |
| **Rate Limit** | 30 requests per minute per user |

#### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number (1-indexed) |
| `limit` | integer | `20` | Records per page (max 100) |
| `risk_category` | string | (none) | Filter by: `SAFE`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, `UNKNOWN` |

#### Success Response — `200 OK`

```json
{
  "total": 47,
  "page": 1,
  "limit": 20,
  "pages": 3,
  "items": [
    {
      "scan_id": "550e8400-e29b-41d4-a716-446655440000",
      "url": "https://suspicious-example.com/login",
      "status": "complete",
      "trust_score": 23,
      "risk_category": "HIGH",
      "submitted_at": "2026-11-07T12:00:00Z",
      "completed_at": "2026-11-07T12:00:07Z"
    }
  ]
}
```

#### Error Responses

| HTTP Code | Condition |
|---|---|
| `401 Unauthorized` | Missing or invalid JWT |
| `400 Bad Request` | `limit` exceeds 100 or is less than 1 |

#### Validation Rules

- JWT must be present and valid.
- `page` must be ≥ 1.
- `limit` must be between 1 and 100.
- `risk_category` must be one of the six valid categories if provided.

---

### 4.4 POST /auth/register

**Create a new user account.**

> [!NOTE]
> TrustGuard AI delegates registration entirely to **Supabase Auth**. The frontend calls the Supabase JS SDK directly — this endpoint does **not** exist as a FastAPI route. It is documented here to describe the complete authentication flow for team reference.

#### Registration Flow

1. **Frontend** calls `supabase.auth.signUp({ email, password })` using the Supabase JS SDK.
2. **Supabase Auth** validates the email and password strength, creates a row in `auth.users`, and sends a confirmation email.
3. On email confirmation, a **database trigger** in Supabase automatically inserts a corresponding row into `public.users` (synchronised via a `AFTER INSERT ON auth.users` trigger).
4. **Supabase Auth** returns a session object containing `access_token` (JWT) and `refresh_token`.
5. **Frontend** stores the session using the Supabase SDK's built-in session management (uses `localStorage`).
6. All subsequent API calls to FastAPI include the `access_token` as a Bearer token.

#### Database Trigger for User Sync

```sql
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, created_at)
  VALUES (NEW.id, NEW.email, NOW())
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

#### Validation Rules (enforced by Supabase Auth)
- Email must be a valid RFC 5322 address.
- Password minimum length: 8 characters.
- Duplicate email addresses return an error from Supabase.

---

### 4.5 POST /reports

**Submit a community threat annotation for a completed scan.**

| Property | Value |
|---|---|
| **Method** | `POST` |
| **Path** | `/api/v1/reports` |
| **Authentication** | **Required** |
| **Rate Limit** | 10 requests per minute per user |

#### Request Body

```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "threat_type": "phishing",
  "target_brand": "PayPal",
  "attack_vector": "email",
  "notes": "Received in a fake PayPal invoice email. Credential harvesting page mimicking PayPal login."
}
```

#### Pydantic Model

```python
from pydantic import BaseModel, Field, UUID4
from typing import Optional
from enum import Enum

class ThreatType(str, Enum):
    phishing = "phishing"
    malware = "malware"
    scam = "scam"
    spam = "spam"
    safe = "safe"
    other = "other"

class AttackVector(str, Enum):
    email = "email"
    sms = "sms"
    social_media = "social_media"
    ad = "ad"
    other = "other"

class ReportRequest(BaseModel):
    scan_id: UUID4 = Field(..., description="UUID of the completed scan to annotate")
    threat_type: ThreatType = Field(..., description="Category of threat")
    target_brand: Optional[str] = Field(None, max_length=100)
    attack_vector: Optional[AttackVector] = None
    notes: Optional[str] = Field(None, max_length=1000)
```

#### Success Response — `201 Created`

```json
{
  "report_id": "aabbccdd-1234-5678-abcd-ef0123456789",
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "threat_type": "phishing",
  "submitted_at": "2026-11-07T12:05:00Z",
  "message": "Thank you for your report. It will be visible to the community immediately."
}
```

#### Error Responses

| HTTP Code | Condition |
|---|---|
| `401 Unauthorized` | Missing or invalid JWT |
| `404 Not Found` | Referenced `scan_id` does not exist |
| `400 Bad Request` | `scan_id` references a scan that is not `complete` |
| `422 Unprocessable Entity` | Invalid `threat_type` or `attack_vector` enum value |

#### Validation Rules

- JWT is required. Guest users cannot submit community reports.
- `scan_id` must reference an existing, completed scan.
- `threat_type` must be one of the six enum values.
- `notes` must not exceed 1000 characters.
- `target_brand` must not exceed 100 characters.
- HTML/script tags in `notes` and `target_brand` are sanitised server-side before storage.

---

### 4.6 GET /reports/{scan_id}

**Retrieve all community threat reports for a specific scan.**

| Property | Value |
|---|---|
| **Method** | `GET` |
| **Path** | `/api/v1/reports/{scan_id}` |
| **Authentication** | None (public endpoint) |
| **Rate Limit** | 60 requests per minute per IP |

#### Path Parameters

| Parameter | Type | Description |
|---|---|---|
| `scan_id` | UUID | Scan to retrieve community reports for |

#### Success Response — `200 OK`

```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://suspicious-example.com/login",
  "total_reports": 3,
  "reports": [
    {
      "report_id": "aabbccdd-1234-5678-abcd-ef0123456789",
      "threat_type": "phishing",
      "target_brand": "PayPal",
      "attack_vector": "email",
      "notes": "Received in a fake PayPal invoice email.",
      "upvotes": 7,
      "submitted_at": "2026-11-07T12:05:00Z"
    }
  ]
}
```

> [!NOTE]
> `user_id` and reporter identity are **never** included in the public response to protect reporter privacy.

#### Error Responses

| HTTP Code | Condition |
|---|---|
| `404 Not Found` | No scan with the given `scan_id` exists |
| `422 Unprocessable Entity` | `scan_id` is not a valid UUID |

---

## 5. Complete Pydantic Schema Reference

```python
# backend/app/models/scan.py and backend/app/models/report.py
# Full schema reference for all request and response models

from pydantic import BaseModel, HttpUrl, Field, UUID4
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

# ─── Enums ────────────────────────────────────────────────────────────────────

class ScanStatus(str, Enum):
    pending    = "pending"
    processing = "processing"
    complete   = "complete"
    error      = "error"

class RiskCategory(str, Enum):
    SAFE     = "SAFE"
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN  = "UNKNOWN"

class ThreatType(str, Enum):
    phishing = "phishing"
    malware  = "malware"
    scam     = "scam"
    spam     = "spam"
    safe     = "safe"
    other    = "other"

class AttackVector(str, Enum):
    email        = "email"
    sms          = "sms"
    social_media = "social_media"
    ad           = "ad"
    other        = "other"

# ─── Service Result Dataclasses (internal, not exposed in API) ─────────────────

@dataclass
class VTResult:
    malicious: int
    total: int
    score: int           # 0-100
    engines: Dict[str, str]
    available: bool      # False if API call failed

@dataclass
class MLResult:
    probability: float   # 0.0 - 1.0
    label: str           # "phishing" or "benign"
    score: int           # 0-100 (100 = benign, 0 = phishing)
    features: Dict[str, Any]
    available: bool

@dataclass
class SSLResult:
    valid: bool
    issuer: Optional[str]
    expiry: Optional[datetime]
    days_remaining: Optional[int]
    score: int           # 0-100
    raw: Optional[Dict]
    available: bool

@dataclass
class URLResult:
    score: int           # 0-100
    flags: List[Dict[str, str]]  # [{"flag": "...", "description": "..."}]
    features: Dict[str, Any]
    available: bool

@dataclass
class TrustScore:
    final_score: int
    risk_category: RiskCategory
    vt_contribution: float
    ml_contribution: float
    ssl_contribution: float
    url_contribution: float
    explanations: List[str]
    score_breakdown: Dict[str, Any]

# ─── API Request Models ────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    url: HttpUrl = Field(..., max_length=2048)
    guest: bool = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "guest": False
            }
        }

class ReportRequest(BaseModel):
    scan_id: UUID4
    threat_type: ThreatType
    target_brand: Optional[str] = Field(None, max_length=100)
    attack_vector: Optional[AttackVector] = None
    notes: Optional[str] = Field(None, max_length=1000)

# ─── API Response Models ───────────────────────────────────────────────────────

class ScanAcceptedResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    submitted_at: datetime
    message: str

class VTResponse(BaseModel):
    malicious: int
    total: int
    score: int
    engines: Dict[str, str]

class MLResponse(BaseModel):
    probability: float
    label: str
    score: int
    features: Dict[str, Any]

class SSLResponse(BaseModel):
    valid: bool
    issuer: Optional[str]
    expiry: Optional[datetime]
    days_remaining: Optional[int]
    score: int

class URLHeuristicsResponse(BaseModel):
    score: int
    flags: List[Dict[str, str]]

class ScoreBreakdown(BaseModel):
    vt_weight: float
    ml_weight: float
    ssl_weight: float
    url_weight: float
    vt_contribution: float
    ml_contribution: float
    ssl_contribution: float
    url_contribution: float
    final_score: int
    explanations: List[str]

class ScanResultDetail(BaseModel):
    trust_score: int
    risk_category: RiskCategory
    vt: Optional[VTResponse]
    ml: Optional[MLResponse]
    ssl: Optional[SSLResponse]
    url_heuristics: Optional[URLHeuristicsResponse]
    score_breakdown: ScoreBreakdown

class ScanResponse(BaseModel):
    scan_id: str
    url: str
    status: ScanStatus
    submitted_at: datetime
    completed_at: Optional[datetime]
    result: Optional[ScanResultDetail]

class HistoryItem(BaseModel):
    scan_id: str
    url: str
    status: ScanStatus
    trust_score: Optional[int]
    risk_category: Optional[RiskCategory]
    submitted_at: datetime
    completed_at: Optional[datetime]

class HistoryResponse(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    items: List[HistoryItem]

class CommunityReport(BaseModel):
    report_id: str
    threat_type: ThreatType
    target_brand: Optional[str]
    attack_vector: Optional[AttackVector]
    notes: Optional[str]
    upvotes: int
    submitted_at: datetime

class ReportsResponse(BaseModel):
    scan_id: str
    url: str
    total_reports: int
    reports: List[CommunityReport]

class ReportAcceptedResponse(BaseModel):
    report_id: str
    scan_id: str
    threat_type: ThreatType
    submitted_at: datetime
    message: str

class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None
```

---

## 6. Async Polling Flow

Because URL analysis takes 3–8 seconds (dominated by VirusTotal's response time), the API uses an **async submit-then-poll** pattern rather than a synchronous long-poll.

```
Client                              Server
  │                                   │
  │  POST /api/v1/scan                │
  │  {"url": "https://..."}           │
  │──────────────────────────────────>│
  │                                   │  1. Validate URL
  │                                   │  2. INSERT scan_history (status=pending)
  │                                   │  3. Dispatch asyncio task
  │  202 Accepted                     │
  │  {"scan_id": "uuid", "status":    │
  │   "pending"}                      │
  │<──────────────────────────────────│
  │                                   │
  │  GET /api/v1/scan/{uuid}          │  (poll #1, ~0s)
  │──────────────────────────────────>│
  │  200 {"status": "pending",        │  asyncio still running
  │       "result": null}             │
  │<──────────────────────────────────│
  │                                   │
  │  [wait 2 seconds]                 │  asyncio.gather runs:
  │                                   │   - VirusTotal API call
  │                                   │   - ML.predict()
  │                                   │   - SSL check
  │                                   │   - URL heuristics
  │                                   │   → scoring engine
  │                                   │   → INSERT scan_results
  │                                   │   → UPDATE scan_history status=complete
  │                                   │
  │  GET /api/v1/scan/{uuid}          │  (poll #2, ~2s)
  │──────────────────────────────────>│
  │  200 {"status": "complete",       │
  │       "result": { trust_score,    │
  │       risk_category, ... }}       │
  │<──────────────────────────────────│
  │  [stop polling]                   │
```

### Frontend Polling Implementation

```javascript
// hooks/useScan.js
const pollScanResult = async (scanId) => {
  const MAX_POLLS = 30;        // 30 polls × 2s = 60s timeout
  const POLL_INTERVAL_MS = 2000;

  for (let i = 0; i < MAX_POLLS; i++) {
    const response = await backendClient.get(`/scan/${scanId}`);
    if (response.data.status === 'complete') {
      return response.data;
    }
    if (response.data.status === 'error') {
      throw new Error(response.data.error_message || 'Scan failed');
    }
    await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
  }
  throw new Error('Scan timed out after 60 seconds');
};
```

---

## 7. Error Handling Conventions

All error responses follow a consistent JSON structure:

```json
{
  "detail": "Human-readable error message",
  "code": "OPTIONAL_MACHINE_READABLE_CODE"
}
```

| HTTP Code | Meaning | Common Causes |
|---|---|---|
| `400 Bad Request` | Client-supplied data is invalid | Malformed URL, scheme not http/https, URL > 2048 chars, SSRF guard blocked IP |
| `401 Unauthorized` | Authentication required or token invalid | Missing Bearer token, expired JWT, malformed JWT |
| `403 Forbidden` | Authenticated but not authorised | Requesting another user's private scan |
| `404 Not Found` | Resource does not exist | Invalid `scan_id`, scan belongs to another user |
| `422 Unprocessable Entity` | Pydantic validation failed | Wrong field type, missing required field, enum value not in set |
| `429 Too Many Requests` | Rate limit exceeded | More than 5 scan requests/minute from same IP |
| `500 Internal Server Error` | Server-side failure | Database unreachable, unhandled exception |
| `503 Service Unavailable` | External dependency down | VirusTotal API down (partial results still returned) |

### Rate Limit Response Headers

```
HTTP/1.1 429 Too Many Requests
Retry-After: 47
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699358447

{
  "detail": "Rate limit exceeded. Maximum 5 scan requests per minute per IP address.",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

---

## 8. API Versioning Strategy

TrustGuard AI uses **URI path versioning** (`/api/v1/`). This was chosen for:
- **Simplicity**: No custom headers or content negotiation required.
- **Cacheability**: Version is part of the URL, making it CDN-friendly.
- **Discoverability**: New developers immediately know which version they are calling.

### Rules

1. All endpoints are prefixed with `/api/v1/`.
2. **Backward-incompatible changes** (removing a field, changing a type) require a new version prefix (`/api/v2/`).
3. **Backward-compatible additions** (new optional response fields, new optional query params) are made in-place without a version bump.
4. During the hackathon, only `v1` is maintained. The versioning structure ensures a future `v2` can coexist without breaking existing clients.

### FastAPI Router Registration

```python
# app/main.py
from fastapi import FastAPI
from app.api import scan, history, reports

app = FastAPI(title="TrustGuard AI API", version="1.0.0")

app.include_router(scan.router,    prefix="/api/v1", tags=["Scan"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])
```
