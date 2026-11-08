# TrustGuard AI

> **Scan Smart. Browse Safe. Trust Digitally.**

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React Version](https://img.shields.io/badge/react-18.3%2B-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/typescript-5.5%2B-3178C6.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/vite-5.4%2B-646CFF.svg)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/tailwindcss-3.4%2B-38B2AC.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Project Overview
**TrustGuard AI** is an advanced, AI-powered web threat detection and digital trust intelligence platform. Designed to combat sophisticated social engineering, brand impersonation, deceptive homoglyph attacks, credential harvesters, and malicious web resources, TrustGuard AI combines real-time multi-vendor threat telemetry, machine-learning classification, SSL/TLS cryptographic inspection, and structural URL heuristics into an explainable, transparent Digital Trust Score (0–100).

---

## 2. Problem Statement
Every day, millions of users and enterprise employees interact with hyperlinks distributed through email, messaging platforms, social media, and search engines. Modern threat actors easily circumvent legacy security filters through:
1. **Deceptive Homoglyph & Obfuscation Attacks:** Registering lookalike domains using Punycode or character substitution (e.g., Cyrillic characters mimicking Latin letters).
2. **Valid Cryptographic Disguises:** Procuring automated, free SSL/TLS certificates (e.g., Let's Encrypt) to project an illusion of legitimacy with the browser padlock icon.
3. **Inconclusive & Lagging Threat Feeds:** Traditional blacklists frequently experience latency before flagging newly weaponized zero-day attack infrastructure.
4. **Opaque verdicts:** Legacy web security scanners output binary ("Safe" or "Unsafe") decisions without articulating *why* a website is hazardous or what specific risk vectors were uncovered.

---

## 3. Proposed Solution
TrustGuard AI transforms web threat analysis from opaque guesswork into an explainable, multi-layered digital audit pipeline:
- **Lexical & Structural Analysis:** 23 algorithmic feature extractors scrutinizing URL length, entropy, suspicious top-level domains (TLDs), IP-based hostnames, and userinfo `@` obfuscations.
- **Machine Learning Inference:** A pre-trained Random Forest model evaluating non-linear feature combinations to predict phishing probability with probabilistic confidence.
- **Multi-Vendor Intelligence:** Live consensus lookups against VirusTotal v3's network of 70+ security vendors.
- **Cryptographic Transport Verification:** Direct socket-level SSL/TLS certificate inspection checking certificate validity, issuer trust, cipher strength, and DNS SSRF protections.
- **Collaborative Community Layer:** Citizen-driven threat submissions with cryptographic file integrity checks, upvoting, and administrative moderation.

---

## 4. Core Features
- **Deep Multi-Engine URL Scanner:** Instant URL evaluation backed by parallel analysis workers.
- **Dynamic Digital Trust Score (0–100):** Weighted composite risk index with four risk tiers:
  - `90–100`: High Trust / Verified Safe
  - `70–89`: Moderate Trust / Minor Warnings
  - `50–69`: Low Trust / Caution Required
  - `0–49`: Critical Threat / High Risk
- **Detailed Explainable Security Reports:** Interactive breakdowns of domain age, SSL cipher suites, certificate issuer details, ML prediction factors, and raw JSON export.
- **Dual Authentication System:**
  - Standard user login & registration via email/password and Google OAuth.
  - Dedicated administrator authentication with Argon2id cryptographic password hashing at `/admin/login`.
- **User Dashboard & Scan History:** Searchable personal scanning audit trail with CSV export and threat digest preferences.
- **Collaborative Community Threat Reporting:** Report suspicious URLs with screenshots, evidentiary attachments, and community consensus upvoting.
- **Full-Featured Administrator Panel:**
  - Real-time operational metrics and Recharts telemetry graphs (7, 30, and 90-day intervals).
  - User account moderation (suspend/restore with mandatory audit reasons).
  - Moderation queue with batch/bulk action support and evidence quarantine tools.
  - System health probes for infrastructure, databases, and third-party APIs.
  - Website Maintenance Mode with HTTP 503 gateway enforcement and visitor announcements.
  - Cryptographically timestamped, immutable administrative audit logging.
- **Monochromatic UI Design System:** Premium dark aesthetic (`#080808` canvas, `#111111` containers, Geist monospace typography, geometric pixel animations).

---

## 5. Technology Stack

### Frontend
- **Framework:** React 18 with TypeScript 5.5
- **Build Tool:** Vite 5
- **Styling:** Tailwind CSS with custom monochromatic design tokens
- **Icons & Visuals:** Lucide React & Framer Motion
- **Data Visualization:** Recharts
- **HTTP Client:** Axios with centralized interceptors and error handlers

### Backend
- **Framework:** FastAPI 0.110+ (Python 3.11 ASGI)
- **Application Server:** Uvicorn
- **Data Validation & Settings:** Pydantic v2 & Pydantic Settings
- **Machine Learning Runtime:** Scikit-learn & Joblib
- **Asynchronous HTTP Client:** HTTPX
- **Security & Cryptography:** Argon2id (`argon2-cffi`), PyJWT, Cryptography

### Database & Cloud Services
- **Database:** PostgreSQL on Supabase with Row Level Security (RLS)
- **User Identity:** Supabase Auth with Google OAuth
- **Threat Intelligence:** VirusTotal API v3

---

## 6. System Architecture

flowchart TD
    subgraph Client ["Frontend Client (React + Vite)"]
        UserBrowser["Public User Browser"]
        AdminBrowser["Admin Console"]
    end

    subgraph Gateway ["FastAPI HTTP Gateway (/api/v1)"]
        MaintMiddleware{"Maintenance Active?"}
        503Err["HTTP 503 Service Unavailable"]
        PublicRouter["Public & User Endpoints"]
        AdminRouter["Protected Admin Endpoints (/admin/*)"]
    end

    subgraph SecurityPipeline ["Parallel Security Analysis Pipeline"]
        direction TB
        URLHeuristics["URL Lexical Analyzer (23 Features)"]
        MLEngine["Random Forest Classifier (Joblib)"]
        SSLEngine["SSL/TLS Socket & SSRF Inspector"]
        VTEngine["VirusTotal v3 Intelligence Feed"]
    end

    subgraph DecisionEngine ["Risk Scoring Engine"]
        Scorer["Composite Risk & Trust Calculator"]
        Rules["High-Severity Security Overrides"]
    end

    subgraph DataStore ["Persistence & External Services"]
        DB[(Supabase PostgreSQL)]
        VT["VirusTotal API v3"]
        GoogleOAuth["Google Cloud Identity"]
    end

    UserBrowser -->|HTTP Requests| MaintMiddleware
    MaintMiddleware -->|Maintenance Enabled & Non-Admin| 503Err
    MaintMiddleware -->|Normal Traffic| PublicRouter
    AdminBrowser -->|Bearer Token (type: admin_session)| AdminRouter

    PublicRouter --> SecurityPipeline
    SecurityPipeline --> DecisionEngine
    DecisionEngine --> DB
    VTEngine --> VT
    PublicRouter --> GoogleOAuth

---

## 7. How URL Scanning Works
1. **Submission & Normalization:** The user submits a target URL. The backend validates syntax according to RFC 3986, normalizes protocols, extracts hostnames, and performs canonical domain parsing.
2. **SSRF Guard:** The engine resolves DNS records and checks destination IP addresses against RFC 1918 private networks, loopback (`127.0.0.0/8`, `::1`), link-local, and cloud metadata (`169.254.169.254`). Unsafe targets trigger an immediate abort with Trust Score 0.
3. **Concurrent Parallel Analysis:** Three background worker pipelines execute simultaneously:
   - Feature extraction and lexical calculation.
   - SSL/TLS socket handshake, certificate chain extraction, and expiration verification.
   - VirusTotal URL/domain lookup with in-memory caching.
4. **Machine Learning Inference:** Extracted numerical feature vectors are evaluated by the Random Forest model.
5. **Weighted Scoring & Override Evaluation:** Dynamic weights calculate the raw risk score. Any critical override (e.g., active malware confirmed by VirusTotal or high-confidence phishing) overrides the weighted average.
6. **Persistence & Return:** The completed security audit report is written to the database (if user is authenticated) and returned to the client.

---

## 8. Machine Learning Phishing Detection
- **Model Type:** Supervised Random Forest Classifier serialized via `joblib`.
- **Feature Vector:** 23 numerical and structural URL attributes:
  - Structural lengths: URL length, domain length, path length, query length.
  - Character frequencies: Count of dots, hyphens, underscores, slashes, question marks, equals, at symbols (`@`), percent signs, and digits.
  - Heuristic markers: Presence of IP address in host, sensitive keywords (`login`, `verify`, `banking`, `secure`, `account`), sub-domain depth, and character entropy.
- **Safety Policy:** If the ML model artifact is unavailable, the pipeline falls back gracefully to `prediction: "UNKNOWN"` and redistributes weights. An unavailable model never fabricates a safe score.

---

## 9. VirusTotal Threat Intelligence Integration
- Communicates directly with the official VirusTotal v3 REST API (`https://www.virustotal.com/api/v3`).
- Aggregates verdicts across 70+ commercial antivirus and security vendors.
- **Quota & Error Handling:** Caches responses with a 3600-second TTL to respect free-tier rate limits. If the API key is not configured or limits are reached, the system marks the feed as `API_UNAVAILABLE` and dynamically redistributes weights without assuming the URL is safe.

---

## 10. SSL/TLS Cryptographic Analysis
- Initiates an asynchronous direct TLS handshake using Python's native `ssl` and `socket` modules.
- **Extracted Attributes:** Protocol version (TLS 1.2, TLS 1.3), cipher suite, certificate validity window, issuer common name, Subject Alternative Names (SAN), and remaining days until expiration.
- **Risk Penalties:** Deducts trust points for self-signed certificates, expired certificates, mismatching hostnames, weak cipher suites, or lack of HTTPS encryption.

---

## 11. Digital Trust Score Formula
The **Trust Score ($T$)** ranges from **0 to 100**, where $100$ indicates pristine trust and $0$ indicates a confirmed threat.

$$T = 100 - R_{\text{final}}$$

Where raw composite risk $R_{\text{raw}}$ is determined by weighted sub-scores:

$$R_{\text{raw}} = w_{\text{vt}} \cdot R_{\text{vt}} + w_{\text{ml}} \cdot R_{\text{ml}} + w_{\text{ssl}} \cdot R_{\text{ssl}} + w_{\text{lex}} \cdot R_{\text{lex}}$$

Default weights when all engines are active:
- **VirusTotal Telemetry ($w_{\text{vt}}$):** $0.40$
- **Machine Learning Classifier ($w_{\text{ml}}$):** $0.30$
- **SSL/TLS Security ($w_{\text{ssl}}$):** $0.15$
- **URL Lexical Heuristics ($w_{\text{lex}}$):** $0.15$

**High-Severity Override Rules:**
- Confirmed malicious on VirusTotal ($\ge 3$ engines): Minimum risk forced to $\ge 85.0$.
- High-confidence ML phishing ($\ge 85\%$ probability): Minimum risk forced to $\ge 75.0$.
- Blocked SSRF destination: Risk forced to $100.0$ ($T = 0$).
- Raw IP combined with `@` sign obfuscation: Minimum risk forced to $\ge 80.0$.

---

## 12. User Authentication & Authorization
- **Standard Authentication:** Managed via Supabase Auth with JWT verification on the FastAPI backend.
- **Google OAuth:** One-click social login using standard OAuth2 authorization code flow with dynamic redirect resolution (`/auth/callback`).
- **Session Continuity:** Sessions survive page refreshes through secure token persistence in `localStorage`.
- **Role Isolation:** Standard users are assigned `role: "user"`. They cannot access `/admin/*` routes or administrative APIs.

---

## 13. Community Threat Reporting
- Authenticated users can submit suspicious domains with:
  - Threat category (Phishing, Malware, Scam, Fake Shop, Suspicious).
  - Target brand impersonated and attack vector (Email, SMS, Social Media, Ad).
  - Detailed description and evidentiary attachments (PNG, JPG, WebP, PDF, TXT).
- **Consensus & Transparency:** Community members can confirm or upvote reports.
- **Moderation Separation:** Community reports do not automatically classify a URL as malicious; all reports pass through administrative review.

---

## 14. Admin Panel & Threat Moderation
- **Dedicated Route:** Accessible strictly at `/admin/login`.
- **Authentication Isolation:** Dedicated administrator credentials hashed with Argon2id. Tokens carry `type: "admin_session"`.
- **Capabilities:**
  - Full user management (inspect scan history, suspend, restore).
  - Community moderation desk (approve, reject, flag duplicates, bulk moderation).
  - Evidence viewer with SHA-256 hash validation and file quarantine.
  - Threat intelligence feed management.
  - Real-time system diagnostics and latency probes.
  - Immutable audit logs with structured JSON inspection.

---

## 15. Website Maintenance Mode
- Persistent platform availability switch controlled by administrators in `/admin/maintenance`.
- Configuration stored in PostgreSQL `system_settings` table.
- **Gateway Interception:** When active, `maintenance_mode_middleware` blocks public API endpoints with HTTP 503 `{"maintenance": true, ...}`.
- **Admin Exemption:** Routes under `/api/v1/admin/*`, `/api/v1/health`, and `/api/v1/maintenance/status` bypass the block.
- **Client Overlay:** Public visitors see a full-screen maintenance overlay while administrators work uninterrupted.

---

## 16. Security Considerations
- **No Hardcoded Secrets:** All credentials, keys, and tokens are read through environment variables.
- **Strict CORS Policy:** Whitelists approved frontend origins only.
- **Anti-Brute Force:** Admin login gateway enforces a 15-minute account lockout after 5 consecutive failed attempts.
- **Input Sanitization:** URL parameters are normalized and sanitized; SQL queries use parameterized queries and Supabase PostgREST client.
- **File Quarantine:** Evidence attachments are never executed and cannot be directly browsed as executable scripts.

---

## 17. Installation & Local Development Setup

### Prerequisites
- **Python:** Version 3.11 or higher
- **Node.js:** Version 18.x or 20.x
- **Package Managers:** `pip` and `npm`
- **Git**

### Step 1: Clone Repository
```bash
git clone https://github.com/officialasubhan-commits/TRUSTGUARD-AI.git
cd TRUSTGUARD-AI
```

### Step 2: Backend Setup
```bash
cd backend
python -m venv .venv

# Activate virtual environment:
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies:
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment variables:
cp .env.example .env
```

Edit `backend/.env` with your development values:
```env
APP_NAME="TrustGuard AI"
APP_ENV=development
APP_DEBUG=true
PORT=8000
FRONTEND_URL="http://localhost:5173,http://localhost:3000"
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
VIRUSTOTAL_API_KEY=your-virustotal-api-key
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### Step 3: Provision Local Admin Account
```bash
python scripts/create_admin.py --username admin --password "TrustGuard@Admin2026!" --role super_admin --email admin@trustguard.ai --full-name "Principal Admin"
```

### Step 4: Run Backend Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API docs available at: `http://localhost:8000/docs`

### Step 5: Frontend Setup
Open a separate terminal:
```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

### Step 6: Run Frontend Server
```bash
npm run dev
```
Frontend application opens at: `http://localhost:5173`

---

## 18. Supabase & Database Configuration
1. Create a project on [Supabase](https://supabase.com).
2. Navigate to **SQL Editor** and execute the migration files sequentially from `backend/migrations/`:
   - `000_full_schema.sql`
   - `001_initial_schema.sql`
   - `002_row_level_security.sql`
   - `003_scan_history_enhancements.sql`
   - `004_community_reporting_enhancements.sql`
   - `005_community_confirmations_and_integrity.sql`
   - `006_email_preferences.sql`
   - `007_admin_panel_schema.sql`
3. Verify that Row Level Security (RLS) is enabled across all tables.

---

## 19. Google OAuth Setup
1. Open [Google Cloud Console](https://console.cloud.google.com).
2. Create an **OAuth 2.0 Web Client ID**.
3. Set **Authorized JavaScript origins**:
   - `http://localhost:5173`
   - `https://your-project-ref.supabase.co`
   - `https://your-production-domain.vercel.app`
4. Set **Authorized redirect URIs**:
   - `https://your-project-ref.supabase.co/auth/v1/callback` *(Must point to Supabase)*
5. Open [Supabase Dashboard](https://supabase.com):
   - Go to **Authentication** → **Providers** → **Google**.
   - Turn **Enable Sign in with Google** to **ON**.
   - Paste the Google Client ID and Client Secret.
   - Go to **Authentication** → **URL Configuration** and add your redirect URLs (`http://localhost:5173/**`, `https://*.vercel.app/**`).

---

## 20. Testing & Verification

### Backend Test Suite
```bash
cd backend
.venv\Scripts\pytest -v
```

### Frontend Typecheck & Build
```bash
cd frontend
npm run build
```

---

## 21. Deployment Guide

### Backend on Render
1. Create a **Web Service** on [Render](https://render.com).
2. Connect your GitHub repository (`TRUSTGUARD-AI`).
3. Root Directory: `backend` (or repository root if backend is standalone).
4. Environment: `Python 3`.
5. Build Command: `pip install --upgrade pip && pip install -r requirements.txt`.
6. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
7. Health Check Path: `/api/v1/health`.
8. Configure environment variables as detailed in `docs/DEPLOYMENT_READINESS.md`.

### Frontend on Vercel
1. Import repository on [Vercel](https://vercel.com).
2. Framework Preset: `Vite`.
3. Root Directory: `frontend`.
4. Build Command: `npm run build`.
5. Output Directory: `dist`.
6. Add environment variable:
   - `VITE_API_BASE_URL`: `https://your-backend.onrender.com/api/v1`
   - `VITE_GOOGLE_CLIENT_ID`: `your-google-client-id.apps.googleusercontent.com`
7. Deploy.

---

## 22. Repository Directory Structure

```text
TRUSTGUARD-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── admin.py
│   │   │       │   ├── authentication.py
│   │   │       │   ├── community.py
│   │   │       │   ├── health.py
│   │   │       │   ├── maintenance.py
│   │   │       │   ├── scans.py
│   │   │       │   └── users.py
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── admin_security.py
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   └── security.py
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   └── repositories/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── admin_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── community_reporting_service.py
│   │   │   ├── ml_detection_service.py
│   │   │   ├── risk_scoring_service.py
│   │   │   ├── scan_service.py
│   │   │   └── ssl_tls_service.py
│   │   └── main.py
│   ├── migrations/
│   │   ├── 000_full_schema.sql
│   │   └── ... 007_admin_panel_schema.sql
│   ├── ml/
│   │   └── models/
│   │       └── phishing_rf_v1.joblib
│   ├── scripts/
│   │   └── create_admin.py
│   ├── tests/
│   ├── render.yaml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── admin/
│   │   │   ├── auth/
│   │   │   ├── common/
│   │   │   ├── community/
│   │   │   ├── geometric/
│   │   │   └── layout/
│   │   ├── context/
│   │   │   ├── AdminAuthContext.tsx
│   │   │   └── AuthContext.tsx
│   │   ├── layouts/
│   │   │   ├── AdminLayout.tsx
│   │   │   └── RootLayout.tsx
│   │   ├── pages/
│   │   │   ├── admin/
│   │   │   ├── HomePage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── ScannerPage.tsx
│   │   │   └── ReportPage.tsx
│   │   ├── services/
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   ├── vercel.json
│   └── vite.config.ts
├── docs/
│   ├── ADMIN_PANEL_DOCUMENTATION.md
│   ├── DEPLOYMENT_READINESS.md
│   └── FINAL_PROJECT_AUDIT.md
└── README.md
```

---

## 23. Known Limitations & Future Roadmap
- **Browser Sandboxing:** The platform currently analyzes external web endpoints using HTTP/TLS network sockets and lexical indicators; full automated headless browser sandbox execution (DOM snapshotting) is planned for v2.0.
- **DNSSEC Validation:** Basic DNS resolution is active; full cryptographic DNSSEC validation chain checking will be introduced in an upcoming release.
- **Additional Social Providers:** Designed intentionally with Google OAuth exclusively; enterprise SAML / Single Sign-On (SSO) can be integrated via Supabase Auth.

---

## 24. License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
