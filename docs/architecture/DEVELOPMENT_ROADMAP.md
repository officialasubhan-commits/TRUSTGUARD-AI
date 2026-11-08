# TrustGuard AI — Development Roadmap

**Hackathon:** HackMatrix '26 | **Total Time Budget:** 48 Hours  
**Team:** 4 Developers (all beginner-to-intermediate level)

---

## Table of Contents

1. [48-Hour Sprint Schedule](#1-48-hour-sprint-schedule)
2. [Mandatory Features](#2-mandatory-features)
3. [Optional Features](#3-optional-features)
4. [Risk Register](#4-risk-register)
5. [Team Responsibility Matrix](#5-team-responsibility-matrix)
6. [Module Interface Contracts](#6-module-interface-contracts)
7. [Digital Trust Score Methodology](#7-digital-trust-score-methodology)
8. [Technical Dependencies and Integration Requirements](#8-technical-dependencies-and-integration-requirements)

---

## 1. 48-Hour Sprint Schedule

| Hours | Duration | Task | Owner | Deliverable |
|---|---|---|---|---|
| **H0 – H0.5** | 30 min | Project kickoff: read all architecture docs, set up GitHub repo, create feature branches, share Supabase + VirusTotal credentials | All | Shared repo access, all env vars distributed securely |
| **H0.5 – H2** | 1.5 hr | **Backend scaffolding**: FastAPI skeleton, CORS, pydantic config, JWT middleware, SSRF guard stub, Render account setup | Dev 1 | Running `GET /` on localhost:8000 |
| **H0.5 – H2** | 1.5 hr | **Frontend bootstrap** (parallel): Vite + React scaffold, Tailwind, React Router setup, Supabase JS client, login/register pages wired | Dev 3 | Running app on localhost:5173 with working auth |
| **H2 – H5** | 3 hr | **ML/AI service**: URL feature extractor, Random Forest training script, train model on phishing dataset, serialise to `model.pkl`, unit tests | Dev 2 | `ml_service.predict("https://...")` returning `MLResult` |
| **H2 – H5** | 3 hr | **Threat intelligence** (parallel): VirusTotal API wrapper, URLhaus lookup wrapper, async HTTP client with SSRF safety | Dev 4 | `virustotal.analyse("https://...")` returning `VTResult` |
| **H4 – H5** | 1 hr | **SSL/TLS checker**: socket-based cert retrieval, parse issuer/expiry, compute sub-score | Dev 4 | `ssl_service.analyse("https://...")` returning `SSLResult` |
| **H5 – H6** | 1 hr | **Pipeline assembly + scoring**: Wire `asyncio.gather` for all 4 services in `scan.py`, implement `scoring.py`, `crud.py` for DB writes | Dev 1 | Full `POST /scan` returning `scan_id`; `GET /scan/{id}` returning complete result |
| **H6 – H8** | 2 hr | **Scanner + Results pages**: `ScanForm.jsx`, `ScanResultPanel.jsx`, `TrustScoreBadge.jsx`, `RiskGauge.jsx`, polling hook | Dev 3 | Full end-to-end scan flow visible in browser |
| **H7 – H8** | 1 hr | **Dashboard + History page** (overlapping): `HistoryTable.jsx`, `Dashboard.jsx` with Recharts pie chart, `useHistory` hook | Dev 3 | Dashboard showing risk breakdown chart |
| **H8 – H9** | 1 hr | **Community reports module**: `ReportForm.jsx`, `POST /reports`, `GET /reports/{scan_id}`, `CommunityReports.jsx` page | Dev 3 + Dev 4 | Submit and view community reports end-to-end |
| **H9 – H10** | 1 hr | **Security hardening**: SSRF guard fully wired to pipeline, rate limiter `slowapi` integrated, CSP headers in `vercel.json`, input sanitisation audit | Dev 1 + Dev 4 | All 10 Pre-Demo Security Checklist items passing |
| **H10 – H11** | 1 hr | **Unit testing + integration tests**: `test_ml_service.py`, `test_ssl_service.py`, `test_url_features.py`, `test_scoring.py`, `test_scan.py` with mocked APIs | Dev 2 | `pytest` passes with ≥80% coverage on service modules |
| **H11 – H12** | 1 hr | **Deployment**: Backend to Render (Dockerfile), frontend to Vercel (auto-deploy from GitHub), set all env vars in dashboards, smoke test production URLs | Dev 1 + Dev 3 | Live production URLs accessible |
| **H12 – H13** | 1 hr | **UI polish**: Icons via `lucide-react`, Recharts line chart for history, mobile responsiveness, loading states, error boundaries | Dev 3 | Polished, demo-ready UI |
| **H13 – H14** | 1 hr | **Final QA + demo rehearsal**: End-to-end test with 5 real URLs (known phishing, known safe, SSL issues), fix any critical bugs, rehearse 3-minute demo script | All | Demo-ready, rehearsed presentation |
| **H14 – H48** | 34 hr | **Buffer**: Bug fixes, optional features (URL haus integration, PDF export, dark mode), presentation deck polish, rest | All | Presentation deck, any bonus features |

> [!TIP]
> Hours H0.5–H2 and H2–H5 are **parallel tracks**. Dev 1 and Dev 3 work simultaneously; Dev 2 and Dev 4 work simultaneously. Use separate feature branches to avoid merge conflicts.

---

## 2. Mandatory Features

These features **must** be complete and working before the demo. If time is short, prioritise in this order:

1. ✅ **URL submission and validation** — `POST /scan` with SSRF guard
2. ✅ **VirusTotal integration** — At least VT result display (most recognisable to judges)
3. ✅ **ML phishing predictor** — Pre-trained model loaded and scoring
4. ✅ **Digital Trust Score** — Single 0–100 score with risk category label
5. ✅ **Scan result persistence** — Supabase DB writes and reads working
6. ✅ **Frontend Scanner page** — URL input → loading state → results display
7. ✅ **User authentication** — Supabase email/password login and register
8. ✅ **Guest scan support** — Scan without creating an account
9. ✅ **Scan History page** — Authenticated users can view past scans
10. ✅ **Production deployment** — Live URLs for both frontend and backend

---

## 3. Optional Features

Implement these in the **H14–H48 buffer** only after all mandatory features are complete and tested:

- 🌟 **URLhaus integration** — Secondary threat feed, strengthens scoring
- 🌟 **Community threat reports** — Submit and browse annotations (mostly done in H8–H9 but polish here)
- 🌟 **Dashboard charts** — Recharts pie chart (risk category distribution) and line chart (scans over time)
- 🌟 **Score breakdown drill-down** — Collapsible cards for each sub-score dimension on the report page
- 🌟 **Dark mode toggle** — Tailwind `dark:` classes, persisted to `localStorage`
- 🌟 **Export report as PDF** — Use `jsPDF` or `react-pdf` to generate a downloadable report
- 🌟 **Mobile-optimised scan form** — Dedicated layout for small screens with simplified results view
- 🌟 **Admin panel** — View and moderate community reports (requires Supabase admin role check)

---

## 4. Risk Register

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| **VirusTotal free tier rate limit hit (4 req/min)** | High — scan pipeline stalls for all users | High | Cache VT results by URL hash in DB; return cached result if scanned within last 24 hours; display "Using cached result" notice |
| **Render free tier cold start (up to 50s)** | Medium — first scan after inactivity times out | High | Add a frontend "wake-up" ping on app load; show "Service starting, please wait…" banner; submit backend 30s before demo |
| **ML model not trained / poor accuracy** | High — core feature non-functional | Medium | Pre-download a public phishing dataset (PhiUSIIL, ISCX-URL-2016) the night before; have `trainer.py` ready; fallback: use URL heuristics only |
| **Supabase project quota exceeded** | High — DB writes fail | Low | Free tier gives 500MB storage and 2GB bandwidth; well within hackathon scale; monitor in Supabase dashboard |
| **Dev 1 blocked on FastAPI setup** | High — no backend for others to integrate against | Medium | Mock backend: Dev 3 uses `json-server` to simulate responses while Dev 1 finishes; switch to real backend at H5 |
| **API key not working (VirusTotal)** | High — VT integration fails | Low | Register backup VT account before hackathon; store both keys; can register on the day with a temporary email |
| **CORS errors between frontend and backend** | Medium — frontend cannot call backend | Medium | Backend CORSMiddleware is set up in H0.5–H2; Vercel URL added to `FRONTEND_URL` env var before deployment |
| **Merge conflicts in `main` branch** | Low — lost work, delays | Medium | Strict feature branch policy; PRs reviewed by one other dev; merge only after milestone is verified on branch |
| **Demo environment different from dev** | Medium — works locally, fails live | Medium | Smoke test production URLs at H11–H12 with 5 real URLs; fix deployment issues before H13 |

---

## 5. Team Responsibility Matrix

---

### Developer 1 — Backend & API Lead

**Files Owned:**
```
backend/app/api/           (all files)
backend/app/core/          (all files)
backend/app/db/            (all files)
backend/app/main.py
backend/Dockerfile
backend/requirements.txt
backend/.env.example
```

**Responsibilities:**
- FastAPI application initialisation, middleware, and lifespan events (model pre-loading at startup)
- JWT verification middleware (`app/core/security.py`) — wires Supabase JWT verification
- SSRF guard implementation and integration (`validate_url_for_ssrf()` called in `scan.py` before analysis)
- `asyncio.gather` pipeline assembly — fans out to all 4 services, collects results
- Rate limiter integration (`slowapi`, `rate_limiter.py`)
- CRUD helpers (`app/db/crud.py`) — all parameterised DB read/write operations
- CORS configuration — restricts to `FRONTEND_URL` env var in production
- Render deployment — Dockerfile, environment variables, service configuration
- API contract publishing — keeps [API_SPECIFICATION.md](./API_SPECIFICATION.md) up to date as the single source of truth

**Interface Contracts Published:**
- `POST /api/v1/scan` → returns `ScanAcceptedResponse`
- `GET /api/v1/scan/{id}` → returns `ScanResponse` (with `result: ScanResultDetail | null`)
- `GET /api/v1/history` → returns `HistoryResponse`

**Consumes:**
- `MLResult` from Dev 2's `ml_service.predict()`
- `VTResult`, `SSLResult`, `URLResult`, `TrustScore` from Dev 4's service modules

---

### Developer 2 — AI/ML Engineer

**Files Owned:**
```
backend/app/services/ml_service.py
backend/app/ml/model.pkl
backend/app/ml/feature_names.json
backend/app/ml/trainer.py
backend/tests/test_ml_service.py
```

**Responsibilities:**
- **Feature engineering**: Extract 20+ lexical and structural features from a URL string without making any network calls (pure string analysis)
- **Model training**: Run `trainer.py` on a phishing URL dataset to produce `model.pkl`; commit trained model to repo
- **Inference module**: Load `model.pkl` at application startup (via FastAPI lifespan); expose `async predict(url: str) -> MLResult`
- **Unit tests**: `test_ml_service.py` tests feature extraction logic and model output format with mocked inputs; no live API calls in tests
- **Feature list documentation**: Maintain `feature_names.json` with the exact ordered column list the model was trained on

**Interface Contract Exposed:**

```python
# Exact function signature that Dev 1 calls in the pipeline
async def predict(url: str) -> MLResult:
    """
    Extracts URL features and returns phishing prediction.
    Must never raise an exception — catch all errors and return MLResult(available=False).
    Must complete within 500ms (no network calls).
    """
    ...
```

**URL Features to Extract (minimum set):**
- `url_length`: Total length of the URL string
- `hostname_length`: Length of the hostname component
- `num_dots`: Number of dots in hostname
- `num_subdomains`: Number of subdomain levels
- `has_ip`: Boolean — hostname is an IP literal
- `has_at_sign`: Boolean — URL contains `@`
- `has_double_slash`: Boolean — path contains `//`
- `has_dash`: Boolean — hostname contains `-`
- `num_query_params`: Number of query parameters
- `path_depth`: Number of `/` segments in path
- `is_https`: Boolean — scheme is https
- `tld`: Top-level domain extracted from hostname
- `entropy`: Shannon entropy of the full URL (high entropy = obfuscated)
- `num_digits`: Count of digit characters in hostname
- `has_suspicious_words`: Boolean — hostname/path contains `login`, `secure`, `account`, `update`, `verify`, `bank`, `paypal` etc.

---

### Developer 3 — Frontend Engineer

**Files Owned:**
```
frontend/           (entire directory)
```

**Responsibilities:**
- React component development for all 9 pages and all shared/feature components
- Supabase Auth integration (`useAuth.js` hook wrapping `@supabase/supabase-js`)
- Axios `backendClient.js` with automatic `Authorization: Bearer` header injection from Supabase session
- Polling logic implementation (`useScan.js` hook — 2-second poll, 60-second timeout)
- Tailwind CSS styling — consistent design language across all pages
- Recharts visualisations — `RiskGauge` (radial bar) and `Dashboard` charts (pie, line)
- `lucide-react` icons — visual polish without custom SVG work
- Vercel deployment — connect GitHub repo, set environment variables, verify production URL
- Mobile responsiveness — all pages usable on 375px+ screen width

**Interface Contracts Consumed:**
- `POST /api/v1/scan` → `ScanAcceptedResponse` (get `scan_id`, start polling)
- `GET /api/v1/scan/{id}` → `ScanResponse` (render results when `status === "complete"`)
- `GET /api/v1/history` → `HistoryResponse` (render `HistoryTable`)
- `POST /api/v1/reports` → `ReportAcceptedResponse`
- `GET /api/v1/reports/{scan_id}` → `ReportsResponse`

**Key Implementation Notes:**
- Use React Context (`AuthContext`) for global auth state — do not prop-drill `user` through every component.
- `ProtectedRoute.jsx` checks `AuthContext.user`; redirects to `/login` if null.
- The `backendClient.js` Axios interceptor reads the current session from `supabase.auth.getSession()` on every request to ensure fresh tokens.

---

### Developer 4 — Threat Intelligence & Integration

**Files Owned:**
```
backend/app/services/virustotal.py
backend/app/services/urlhaus.py
backend/app/services/ssl_service.py
backend/app/services/url_features.py
backend/app/services/scoring.py
backend/tests/test_ssl_service.py
backend/tests/test_url_features.py
backend/tests/test_scoring.py
```

**Also responsible for:**
- Supabase project setup (DDL, RLS policies, indexes, auth trigger) — follow [DATABASE_DESIGN.md](./DATABASE_DESIGN.md) exactly
- `app/models/scan.py` and `app/models/report.py` Pydantic model definitions

**Responsibilities:**
- **VirusTotal wrapper**: `async analyse(url: str) -> VTResult`. Submit URL to VT API v3 (`/urls` endpoint), poll until analysis complete, parse `last_analysis_stats` and per-engine results.
- **URLhaus wrapper**: `async lookup(url: str) -> URLhausResult`. POST to `https://urlhaus-api.abuse.ch/v1/url/` with `url=` parameter. No API key required.
- **SSL/TLS checker**: `async analyse(url: str) -> SSLResult`. Open a TLS socket to the hostname on port 443, extract and parse the DER certificate, check validity window, extract issuer CN/O.
- **URL features extractor**: `async analyse(url: str) -> URLResult`. Coordinate-free heuristic analysis of URL structure. See heuristic flag list in Section 7.
- **Scoring engine**: `calculate_trust_score(vt, ml, ssl, url_feat) -> TrustScore`. Weighted aggregation. See Section 7 for the full methodology.
- **Unit tests**: Each service has a test file; external API calls are mocked with `unittest.mock.patch` or `pytest-httpx`.

**Interface Contracts Exposed:**

```python
# Every service function MUST follow this pattern:
# - async def analyse(url: str) -> ServiceResult
# - catch ALL exceptions internally, return available=False on failure
# - never raise exceptions into the pipeline

async def analyse(url: str) -> VTResult: ...      # virustotal.py
async def lookup(url: str) -> URLhausResult: ...  # urlhaus.py
async def analyse(url: str) -> SSLResult: ...     # ssl_service.py
async def analyse(url: str) -> URLResult: ...     # url_features.py

def calculate_trust_score(
    vt: VTResult,
    ml: MLResult,
    ssl: SSLResult,
    url_feat: URLResult
) -> TrustScore: ...                               # scoring.py
```

---

## 6. Module Interface Contracts

Formal type definitions for all cross-developer integration points. All developers must use these exact types when calling or returning from service modules.

```python
# backend/app/services/__init__.py
# Or define in backend/app/models/results.py and import everywhere

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class MLResult:
    """Output of ml_service.predict(). Owner: Dev 2."""
    probability: float          # 0.0 (benign) to 1.0 (phishing)
    label: str                  # "phishing" or "benign"
    score: int                  # 0-100; 100=fully benign, 0=confirmed phishing
    features: Dict[str, Any]   # Feature dict used for this prediction
    available: bool             # False if model failed to run; score must be ignored

@dataclass
class VTResult:
    """Output of virustotal.analyse(). Owner: Dev 4."""
    malicious: int              # Count of engines flagging as malicious
    total: int                  # Total engines that responded
    score: int                  # 0-100; 100=all clean, 0=all malicious
    engines: Dict[str, str]    # engine_name -> verdict (e.g. "malware", "phishing", "clean")
    available: bool             # False if VT API call failed or timed out

@dataclass
class SSLResult:
    """Output of ssl_service.analyse(). Owner: Dev 4."""
    valid: bool                          # True if cert is valid and not expired
    issuer: Optional[str]               # Issuer Organisation (e.g. "Let's Encrypt")
    expiry: Optional[datetime]          # Certificate expiry datetime (UTC)
    days_remaining: Optional[int]       # Days until expiry; negative = already expired
    score: int                          # 0-100; 100=perfect cert, 0=no SSL or expired
    raw: Optional[Dict[str, Any]]       # Full parsed cert fields
    available: bool                     # False if SSL handshake failed

@dataclass
class URLResult:
    """Output of url_features.analyse(). Owner: Dev 4."""
    score: int                          # 0-100; 100=no flags, 0=maximum flags
    flags: List[Dict[str, str]]        # [{"flag": "...", "description": "..."}]
    features: Dict[str, Any]           # Raw feature values (for ML cross-reference)
    available: bool                     # Always True (pure string analysis, cannot fail)

@dataclass
class TrustScore:
    """Output of scoring.calculate_trust_score(). Owner: Dev 4."""
    final_score: int                   # 0-100 weighted composite
    risk_category: str                 # "SAFE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "UNKNOWN"
    vt_contribution: float            # VT sub-score × 0.4
    ml_contribution: float            # ML sub-score × 0.3
    ssl_contribution: float           # SSL sub-score × 0.15
    url_contribution: float           # URL sub-score × 0.15
    explanations: List[str]           # Human-readable reasons for deductions
    score_breakdown: Dict[str, Any]   # Full breakdown dict for API serialisation
```

---

## 7. Digital Trust Score Methodology

### 7.1 Scoring Formula

$$
\text{TrustScore} = (VT_{score} \times 0.40) + (ML_{score} \times 0.30) + (SSL_{score} \times 0.15) + (URL_{score} \times 0.15)
$$

All sub-scores range from **0 to 100** (100 = fully safe). The final score is rounded to the nearest integer.

### 7.2 Component Score Calculation Rules

#### VirusTotal Sub-Score (`VT_score`)

| Condition | Score |
|---|---|
| VT result unavailable | Service returns `available=False`; this dimension contributes `UNKNOWN` |
| 0 engines flagged | 100 |
| 1 engine flagged | 80 |
| 2–3 engines flagged | 60 |
| 4–9 engines flagged | 30 |
| 10–24 engines flagged | 10 |
| 25+ engines flagged | 0 |

Formula when available: `max(0, 100 - (malicious / total) * 100 * 2.5)` (capped at 0).

#### ML Sub-Score (`ML_score`)

| Phishing Probability | Score |
|---|---|
| 0.0 – 0.15 | 100 |
| 0.15 – 0.35 | 80 |
| 0.35 – 0.55 | 50 |
| 0.55 – 0.75 | 25 |
| 0.75 – 1.0 | 0 |

Formula: `ML_score = int(max(0, (1 - probability) * 100))`

#### SSL Sub-Score (`SSL_score`)

| Condition | Score |
|---|---|
| SSL unavailable or no HTTPS | 20 |
| Certificate expired | 10 |
| Certificate valid, ≤7 days remaining | 50 |
| Certificate valid, 8–30 days remaining | 70 |
| Certificate valid, 31–90 days remaining | 85 |
| Certificate valid, >90 days remaining | 100 |
| Issuer is a known free CA (Let's Encrypt) | No deduction (free CAs are legitimate) |
| Self-signed certificate | Deduct 30 points from base |

#### URL Heuristics Sub-Score (`URL_score`)

Starts at 100; each triggered flag deducts points:

| Flag | Deduction | Description |
|---|---|---|
| IP literal hostname | -30 | Hostname is a raw IP address (e.g., `http://1.2.3.4/`) |
| Excessive subdomains (≥4) | -20 | 4 or more subdomain levels |
| URL length > 75 chars | -10 | Unusually long URL |
| URL length > 150 chars | -20 | Extremely long URL (cumulative) |
| Contains `@` sign | -25 | Often used to confuse hostname parsing |
| Suspicious keywords in hostname | -20 | `login`, `secure`, `account`, `verify`, `bank`, `paypal`, `update` |
| Homograph characters detected | -25 | Non-ASCII lookalikes in hostname |
| Suspicious TLD | -15 | `.xyz`, `.top`, `.click`, `.gq`, `.tk`, `.ml` |
| Redirect parameter in query | -10 | Query contains `redirect=`, `url=`, `next=`, `goto=` |
| Path depth > 5 levels | -10 | Unusually deep path |
| Double slash in path | -10 | `//` outside of scheme part |
| Punycode hostname | -15 | `xn--` prefix (potential homograph attack) |

Minimum score: 0.

### 7.3 Risk Category Thresholds

| Score Range | Category | Interpretation |
|---|---|---|
| **80 – 100** | 🟢 `SAFE` | Low risk. No significant threat indicators detected. |
| **60 – 79** | 🟡 `LOW` | Minor concerns. Likely safe but verify before entering credentials. |
| **40 – 59** | 🟠 `MEDIUM` | Notable red flags. Use with caution. Do not enter sensitive data. |
| **20 – 39** | 🔴 `HIGH` | Multiple threat indicators. Strongly advised to avoid this URL. |
| **0 – 19** | ⛔ `CRITICAL` | Confirmed malicious or severe risk indicators. Do not visit. |
| **N/A** | ⚪ `UNKNOWN` | Critical data sources were unavailable. Result is inconclusive. |

### 7.4 Rules for Missing Data

> [!WARNING]
> **`UNKNOWN` ≠ `SAFE`**. If the VirusTotal API is unreachable, the URL is not thereby safe — it is unverified. The scoring engine must handle missing data conservatively.

- If **all** services return `available=False` → category is `UNKNOWN` regardless of computed score.
- If **VT** returns `available=False` but others are available → compute partial score from ML + SSL + URL only; normalise weights to sum to 1.0; note data gap in `explanations`.
- If **ML** returns `available=False` → distribute ML weight (0.30) equally between VT (now 0.55) and URL (now 0.30) + SSL stays 0.15.
- Partial scores are always clearly disclosed in the `explanations` list.

### 7.5 Score Transparency Requirements

Every point deduction **must** be recorded in `TrustScore.explanations` as a human-readable string. Examples:

- `"12/72 VirusTotal engines flagged this URL as malicious (Kaspersky: malware, Google Safebrowsing: phishing)"`
- `"ML model predicts 91% probability of phishing based on URL structure"`
- `"URL contains excessive subdomain nesting (5 levels detected)"`
- `"SSL certificate expires in 6 days (issuer: Let's Encrypt)"`
- `"VirusTotal data unavailable due to API timeout; this dimension was excluded from scoring"`

### 7.6 Example Score Calculation Walkthrough

**URL under analysis:** `http://paypa1-secure-login.tk/account/update?redirect=evil.com`

| Dimension | Raw Value | Sub-Score | Weight | Contribution |
|---|---|---|---|---|
| VirusTotal | 8/68 engines malicious | 30 | 0.40 | 12.0 |
| ML Model | probability = 0.87 | 13 | 0.30 | 3.9 |
| SSL | No HTTPS (http://) | 20 | 0.15 | 3.0 |
| URL Heuristics | Flags: suspicious TLD (-15), suspicious keyword `secure` (-20), redirect param (-10), URL length > 75 (-10) → 100-55=45 | 45 | 0.15 | 6.75 |
| **Final Score** | | | | **25.65 → 26** |

**Risk Category:** 🔴 `HIGH`

**Explanations:**
1. "8/68 VirusTotal engines flagged this URL as malicious"
2. "ML model predicts 87% phishing probability"
3. "URL uses HTTP without SSL/TLS — no encrypted connection"
4. "Suspicious TLD detected: .tk is commonly used in phishing campaigns"
5. "Hostname contains deceptive keyword: 'secure'"
6. "URL contains a redirect parameter (?redirect=) which may chain to a malicious destination"

---

## 8. Technical Dependencies and Integration Requirements

### Python Packages (`backend/requirements.txt`)

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.1
pydantic-settings==2.2.1
supabase==2.5.0
scikit-learn==1.4.2
pandas==2.2.2
numpy==1.26.4
python-dotenv==1.0.1
aiohttp==3.9.5
cryptography==42.0.7
slowapi==0.1.9
bleach==6.1.0
PyJWT==2.8.0
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.6
pytest-httpx==0.30.0
```

### Node Packages (`frontend/package.json` dependencies)

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.1",
    "axios": "^1.7.2",
    "@supabase/supabase-js": "^2.43.4",
    "recharts": "^2.12.7",
    "lucide-react": "^0.379.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.2.11",
    "tailwindcss": "^3.4.3",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38"
  }
}
```

### External Accounts Required

| Service | Purpose | Sign-Up URL | Notes |
|---|---|---|---|
| **VirusTotal** | URL threat intelligence API | [virustotal.com](https://www.virustotal.com) | Free account gives 4 req/min; API key under account settings |
| **Supabase** | Database, Auth, RLS | [supabase.com](https://supabase.com) | Free tier; 1 project; 500MB storage |
| **Render** | Backend hosting | [render.com](https://render.com) | Free tier; cold starts after 15 min inactivity |
| **Vercel** | Frontend hosting | [vercel.com](https://vercel.com) | Free tier; unlimited static deploys; GitHub integration |
| **GitHub** | Source control, CI/CD | [github.com](https://github.com) | Private repo; connect to both Render and Vercel for auto-deploy |

> [!IMPORTANT]
> Create all accounts and collect API keys **before** the hackathon starts. VirusTotal email verification can take several minutes. Supabase project creation takes ~2 minutes.

### Git Workflow

**Branching Strategy:** GitHub Flow (simplified)

```
main (always deployable)
  ├── feature/dev1-backend-scaffold
  ├── feature/dev2-ml-service
  ├── feature/dev3-frontend-scanner
  ├── feature/dev4-virustotal
  ├── feature/dev4-ssl-service
  └── feature/dev4-scoring
```

**Branch Naming Convention:** `feature/{owner-shortname}-{feature-name}`  
Examples: `feature/dev1-rate-limiter`, `feature/dev3-history-page`, `feature/dev4-scoring-engine`

**PR Rules:**
- One PR per feature / milestone.
- PR must be reviewed and approved by at least one other developer before merge.
- All CI checks (pytest, `npm run build`) must pass.
- Merge directly to `main` — no long-lived `develop` branch during hackathon.
- Delete the feature branch after merge.

**Commit Message Format:**
```
feat: add SSRF guard to scan endpoint (Dev 1)
fix: handle VT API timeout gracefully (Dev 4)
test: add ML feature extraction unit tests (Dev 2)
docs: update API spec for /reports endpoint (Dev 1)
```

**Protected Files (never edit without team agreement):**
- `docs/architecture/*.md` — Architecture is locked after H1; changes require team consensus
- `backend/app/ml/model.pkl` — Only Dev 2 replaces this; notify team before updating
- `backend/app/services/__init__.py` — Interface contracts; any change affects all integrations
