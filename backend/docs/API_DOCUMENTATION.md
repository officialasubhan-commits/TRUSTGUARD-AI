# TrustGuard AI — Complete REST API Documentation

**API Version:** `v1` (`0.1.0`)  
**Base URL:** `http://localhost:8000/api/v1` (Production: configurable via `HOST`, `PORT`, and reverse proxy)  
**OpenAPI Interactive UI:** `http://localhost:8000/docs` (Swagger UI)  
**ReDoc Reference:** `http://localhost:8000/redoc`  
**OpenAPI Specification:** `http://localhost:8000/openapi.json`

---

## 1. Authentication & Session Management

TrustGuard AI implements a dual-mode access model:
1. **Authenticated Users:** Access protected endpoints by including a valid Supabase-issued or verified JWT in the `Authorization` HTTP header:
   ```http
   Authorization: Bearer <your_jwt_access_token>
   ```
2. **Anonymous Guests:** Endpoints such as `POST /api/v1/scan` and `GET /api/v1/community/reports` permit guest access without tokens. Guest scans are isolated and never leak into authenticated histories.

### Role-Based Access Control (RBAC)
- **`user` / `authenticated`:** Regular user permissions (submit scans, view own history, submit community threat reports, upvote approved reports).
- **`admin`:** Full administrative control (moderate community reports, inspect all lifecycle states, review audit trails). Validated server-side via `app_metadata.role == "admin"`.

---

## 2. Standardized Response & Error Envelopes

### Success Envelope
Endpoints return structured JSON objects matching Pydantic schemas. Paginated endpoints use a standard wrapper:
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

### Standardized Error Envelope
All application exceptions and validation errors return a uniform, safe envelope. Python tracebacks and internal database credentials are NEVER exposed:
```json
{
  "error": {
    "code": "INVALID_URL",
    "message": "URL scheme 'ftp' is not allowed for security reasons. Only HTTP and HTTPS are supported."
  }
}
```

### Error Code Reference
| HTTP Status | Error Code | Description |
| :--- | :--- | :--- |
| `401` | `UNAUTHORIZED` | Missing or unauthenticated Bearer token. |
| `401` | `TOKEN_EXPIRED` | JWT access token expiration timestamp has elapsed. |
| `401` | `INVALID_TOKEN` | Malformed, tampered, or invalid JWT signature. |
| `401` | `INVALID_CREDENTIALS` | Invalid email or password provided during sign-in. |
| `403` | `FORBIDDEN` | Access denied (e.g. non-admin accessing admin queue). |
| `404` | `NOT_FOUND` | Resource not found (also used for unapproved reports to prevent ID enumeration). |
| `404` | `SCAN_NOT_FOUND` | Scan record does not exist or belongs to another user. |
| `409` | `CONFLICT` | Duplicate submission (e.g., user re-reporting the same URL). |
| `409` | `USER_ALREADY_EXISTS` | Email address is already registered. |
| `422` | `INVALID_URL` | Malformed URL syntax, invalid characters, or unsupported scheme. |
| `422` | `SSRF_BLOCKED` | URL resolves to private, loopback, or cloud metadata IP (`169.254.169.254`). |
| `422` | `VALIDATION_ERROR` | Request body failed Pydantic schema validation. |
| `429` | `RATE_LIMIT_EXCEEDED` | Request frequency exceeds configured limit. |
| `502` | `EXTERNAL_SERVICE_ERROR`| Upstream API encountered unexpected protocol failure. |
| `503` | `DATABASE_ERROR` | Database connection or persistence error. |

---

## 3. Complete API Endpoint Inventory

```text
Health & System
├── GET    /                                  # Root API metadata & docs link
├── GET    /health                            # Root health & database check
└── GET    /api/v1/health                     # API v1 health status

Authentication & Profile (/api/v1/auth & /api/v1/users)
├── POST   /api/v1/auth/register              # Register new user account
├── POST   /api/v1/auth/login                 # Authenticate with credentials
├── POST   /api/v1/auth/logout                # Terminate active session
├── POST   /api/v1/auth/refresh               # Refresh expired access token
├── POST   /api/v1/auth/forgot-password       # Request password reset email
├── POST   /api/v1/auth/reset-password        # Update account password
├── GET    /api/v1/auth/me                    # Get current token claims & identity
├── GET    /api/v1/users/me                   # Retrieve user database profile
└── PATCH  /api/v1/users/me                   # Update user full name or avatar

Website Scanning Engine (/api/v1/scan)
├── POST   /api/v1/scan                       # Submit URL for multi-layer security scan
├── GET    /api/v1/scan/{scan_id}             # Retrieve scan status and analysis results
└── GET    /api/v1/scan/status                # Engine readiness status

Scan History & Reporting (/api/v1/scans)
├── GET    /api/v1/scans                      # Server-side paginated & filtered scan history
├── GET    /api/v1/scans/{scan_id}            # Comprehensive security report
├── DELETE /api/v1/scans/{scan_id}            # Securely delete user scan record
├── GET    /api/v1/scans/statistics           # Aggregated user scan statistics
└── GET    /api/v1/scans/{scan_id}/export     # Sanitized export-ready security report

Community Threat Reporting (/api/v1/community)
├── POST   /api/v1/community/reports          # Authenticated threat submission
├── GET    /api/v1/community/reports          # Public verified threat reports (sanitized)
├── GET    /api/v1/community/my-reports       # Submitter's personal submission history
├── GET    /api/v1/community/reports/{id}     # Detailed report view with privacy boundaries
└── POST   /api/v1/community/reports/{id}/upvote # Upvote approved community report

Administrative Moderation (/api/v1/admin)
├── GET    /api/v1/admin/community/reports    # Moderation queue across all lifecycle states
└── PATCH  /api/v1/admin/community/reports/{id} # Moderate report lifecycle & verification
```

---

## 4. Endpoint Specifications & Examples

### A. Health & System

#### `GET /health`
- **Auth:** None (Public)
- **Response `200 OK`:**
```json
{
  "app_name": "TrustGuard AI",
  "app_version": "0.1.0",
  "status": "healthy",
  "environment": "development",
  "database": "decoupled_mock"
}
```

---

### B. Authentication

#### `POST /api/v1/auth/register`
- **Request Body:**
```json
{
  "email": "analyst@security.org",
  "full_name": "Alice Analyst",
  "password": "StrongPassword123!",
  "confirm_password": "StrongPassword123!"
}
```
- **Response `201 Created`:**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "refresh_...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "8c8d260b-0930-4c4e-9591-166aab971d29",
    "email": "analyst@security.org",
    "full_name": "Alice Analyst",
    "avatar_url": null,
    "role": "user",
    "created_at": "2026-11-07T12:00:00Z"
  }
}
```

#### `POST /api/v1/auth/login`
- **Request Body:**
```json
{
  "email": "analyst@security.org",
  "password": "StrongPassword123!"
}
```
- **Response `200 OK`:** Returns access token, refresh token, and user profile.

---

### C. Website Scanning Engine

#### `POST /api/v1/scan`
- **Auth:** Optional (Guests and Authenticated users)
- **Request Body:**
```json
{
  "url": "https://secure-chase-update.com/login"
}
```
- **Response `201 Created`:**
```json
{
  "success": true,
  "scan_id": "9cf6b8c8-dbf6-43d1-a8a7-bdde8b15dbc7",
  "original_url": "https://secure-chase-update.com/login",
  "normalized_url": "https://secure-chase-update.com/login",
  "validation_status": "VALID",
  "is_guest": false,
  "preliminary_analysis": {
    "risk_level": "MODERATE_CONCERN",
    "indicators": [
      {
        "name": "SUSPICIOUS_KEYWORDS",
        "description": "URL contains security-sensitive action keywords: login",
        "severity": "medium",
        "evidence": "login",
        "reason": "Keywords related to authentication are prevalent in phishing URLs."
      }
    ],
    "features": {
      "url_length": 38,
      "hostname_length": 23,
      "path_length": 6,
      "path_depth": 1,
      "dot_count": 1,
      "hyphen_count": 2,
      "digit_count": 0,
      "uses_https": true,
      "is_ip_address": false,
      "is_shortened": false,
      "contains_suspicious_keywords": true,
      "suspicious_keywords": ["login"]
    }
  },
  "ml_prediction": {
    "prediction": "PHISHING",
    "phishing_probability": 0.98,
    "ml_subscore": 2,
    "confidence": "HIGH",
    "model_version": "rf-v1.0.0",
    "model_status": "ACTIVE"
  },
  "ssl_analysis": {
    "status": "VALID",
    "https_enabled": true,
    "hostname": "secure-chase-update.com",
    "days_remaining": 85,
    "hostname_verified": true,
    "certificate_trusted": true,
    "tls_version": "TLSv1.3",
    "ssl_subscore": 100
  },
  "trust_assessment": {
    "digital_trust_score": 20,
    "risk_score": 80,
    "risk_level": "CRITICAL",
    "risk_label": "CRITICAL RISK",
    "assessment_status": "COMPLETE",
    "assessment_coverage": 1.0,
    "coverage_percentage": 100,
    "scoring_version": "v1.0.0",
    "high_severity_override": true,
    "override_reason": "High-confidence machine learning phishing detection (98.0%).",
    "recommendations": [
      "Do NOT submit login credentials, passwords, or personal identity details on this website.",
      "Close the browser tab immediately."
    ]
  },
  "digital_trust_score": 20,
  "risk_level": "CRITICAL",
  "message": "URL accepted and complete multi-layer security analysis conducted.",
  "submitted_at": "2026-11-07T12:00:00Z"
}
```

---

### D. Scan History & Security Reporting

#### `GET /api/v1/scans`
- **Auth:** Bearer Token (Authenticated user)
- **Query Parameters:**
  - `page`: Page index (default: `1`, minimum: `1`)
  - `page_size`: Results per page (default: `10`, range: `1-100`)
  - `query`: Keyword search against domain or URL
  - `risk_level`: Filter by risk category (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `MINIMAL`, `UNKNOWN`)
  - `date_range`: Filter by timeframe (`today`, `last_7_days`, `last_30_days`, `all`)
  - `sort_by`: Sort property (`created_at`, `trust_score`, `domain`)
  - `sort_order`: Sort direction (`desc`, `asc`)
- **Response `200 OK`:**
```json
{
  "items": [
    {
      "scan_id": "9cf6b8c8-dbf6-43d1-a8a7-bdde8b15dbc7",
      "original_url": "https://secure-chase-update.com/login",
      "domain": "secure-chase-update.com",
      "scan_status": "complete",
      "digital_trust_score": 20,
      "risk_score": 80,
      "risk_level": "CRITICAL",
      "assessment_status": "COMPLETE",
      "submitted_at": "2026-11-07T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

#### `GET /api/v1/scans/statistics`
- **Auth:** Bearer Token
- **Response `200 OK`:**
```json
{
  "total_scans": 12,
  "completed_scans": 12,
  "failed_scans": 0,
  "average_trust_score": 68.4,
  "risk_distribution": {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
    "MINIMAL": 2,
    "UNKNOWN": 0
  },
  "unique_domains_scanned": 8
}
```

---

### E. Community Threat Reporting

#### `POST /api/v1/community/reports`
- **Auth:** Bearer Token
- **Request Body:**
```json
{
  "submitted_url": "https://malicious-crypto-drain.io",
  "category": "FRAUD_OR_SCAM",
  "target_brand": "Ethereum Foundation",
  "attack_vector": "social_media",
  "description": "Fake airdrop claiming 2 ETH giveaway prompting wallet signatures."
}
```
- **Response `201 Created`:**
```json
{
  "id": "3c753367-993b-45ea-849c-bf48506f4702",
  "submitted_url": "https://malicious-crypto-drain.io",
  "normalized_url": "https://malicious-crypto-drain.io/",
  "domain": "malicious-crypto-drain.io",
  "category": "FRAUD_OR_SCAM",
  "report_reason": "FRAUD_OR_SCAM",
  "moderation_status": "PENDING",
  "verification_status": "UNVERIFIED",
  "upvotes": 0,
  "created_at": "2026-11-07T12:00:00Z"
}
```

#### `GET /api/v1/community/reports`
- **Auth:** None (Public)
- **Query Parameters:** `category`, `domain`, `search`, `page`, `page_size`
- **Privacy Guarantee:** Excludes submitter identities, emails, moderator IDs, and internal moderation notes.

---

### F. Administrative Moderation

#### `GET /api/v1/admin/community/reports`
- **Auth:** Bearer Token (`role == "admin"`)
- **Query Parameters:** `moderation_status` (`PENDING`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `DUPLICATE`)
- **Response `200 OK`:** Full administrative report list with reviewer IDs and audit history.

#### `PATCH /api/v1/admin/community/reports/{report_id}`
- **Auth:** Bearer Token (`role == "admin"`)
- **Request Body:**
```json
{
  "moderation_status": "APPROVED",
  "verification_status": "ADMIN_VERIFIED",
  "moderation_notes": "Analyst detonation confirmed weaponized drainer contract."
}
```

---

## 5. Rate Limiting Rules
- `POST /api/v1/scan`: `5 requests / minute` per IP address.
- Global API limit: `60 requests / minute` per client.
- VirusTotal live lookups: Strictly cached with 1-hour in-memory TTL to adhere to free-tier thresholds (4 req/min).

---

## 6. Frontend Integration Guidelines

1. **API Base URL Configuration:** Point frontend clients (Axios / Fetch) to `VITE_API_BASE_URL=http://localhost:8000/api/v1`.
2. **CORS Origins:** Default allows `http://localhost:5173` (Vite) and `http://localhost:3000`. Configurable in backend `.env` via `FRONTEND_URL`.
3. **Authentication Token Persistence:** Store `access_token` in memory or secure storage; refresh using `POST /api/v1/auth/refresh` before `expires_in` (3600s) elapses.
4. **Guest Scan Flow:** Omit `Authorization` header when scanning without signing in. Provide a "Sign Up to Save to History" call to action.

