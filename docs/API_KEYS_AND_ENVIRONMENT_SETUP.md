# TrustGuard AI — API Keys, Secrets & Environment Setup Guide

**Document Version:** 1.0.0  
**Target:** Backend & Frontend Developers, DevOps Engineers  
**Security Classification:** Public Reference Guide (Contains zero secret values)  

---

## 1. Master Environment Variable & API Key Inventory

The following table details every configuration variable, secret, and API credential recognized by the TrustGuard AI platform:

| Variable / Key Name | Service / Provider | Purpose | Mandatory or Optional | Where to Obtain (Official Link) | Where to Configure |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`APP_NAME`** | Application | Sets the human-readable brand name across OpenAPI docs and headers. | Optional (Default: `"TrustGuard AI"`) | Built-in configuration. | `backend/.env` |
| **`APP_ENV`** | Application | Defines deployment environment (`development`, `staging`, `production`). In `production`, enforces strict credentials validation. | Optional (Default: `development`) | Set by developer/DevOps. | `backend/.env`, Cloud Platform |
| **`APP_DEBUG`** | Application | Enables detailed debug logging and SQL echo. Must be `false` in production. | Optional (Default: `true`) | Set by developer/DevOps. | `backend/.env` |
| **`APP_VERSION`** | Application | Semantic version string displayed in `/health` and OpenAPI docs. | Optional (Default: `"0.1.0"`) | Set in `app/core/config.py`. | `backend/.env` |
| **`HOST`** | Uvicorn / Server | Network interface binding for the ASGI server. | Optional (Default: `"0.0.0.0"`) | Host system network config. | `backend/.env` |
| **`PORT`** | Uvicorn / Server | HTTP port on which the FastAPI application listens. | Optional (Default: `8000`) | Cloud port assignment (`$PORT`). | `backend/.env`, Cloud Platform |
| **`API_V1_PREFIX`** | Application | Base prefix for all version 1 REST API routes. | Optional (Default: `"/api/v1"`) | Built-in architecture spec. | `backend/.env` |
| **`FRONTEND_URL`** | CORS Middleware | Comma-separated list of allowed frontend origins (e.g. `http://localhost:5173,https://trustguard.ai`). | **Mandatory for CORS** (Defaults to local ports in dev) | Deployed frontend domain. | `backend/.env`, Cloud Platform |
| **`SUPABASE_URL`** | Supabase | Project API Gateway URL for PostgreSQL access and Supabase Auth. | **Optional in dev** (uses mock store); **Mandatory in production** | [Supabase Dashboard](https://supabase.com/dashboard/project/_/settings/api) $\rightarrow$ Project Settings $\rightarrow$ API $\rightarrow$ Project URL | `backend/.env`, Cloud Platform |
| **`SUPABASE_ANON_KEY`** | Supabase | Public anonymous client API key. Allows public read/insert where permitted by RLS. | **Optional in dev**; **Mandatory in production** | [Supabase Dashboard](https://supabase.com/dashboard/project/_/settings/api) $\rightarrow$ Project Settings $\rightarrow$ API $\rightarrow$ Project API keys (`anon` / `public`) | `backend/.env`, `frontend/.env` |
| **`SUPABASE_SERVICE_ROLE_KEY`** | Supabase | Secret administrative key. Bypasses Row Level Security for backend-only jobs. **NEVER expose to frontend.** | **Optional in dev**; **Mandatory in production** | [Supabase Dashboard](https://supabase.com/dashboard/project/_/settings/api) $\rightarrow$ Project Settings $\rightarrow$ API $\rightarrow$ Project API keys (`service_role` secret) | `backend/.env` (**Backend ONLY**) |
| **`SUPABASE_JWT_SECRET`** | Supabase | Cryptographic HMAC SHA-256 secret key used by backend to verify Supabase-issued Bearer JWTs. | **Optional in dev** (uses local test secret); **Mandatory in production** | [Supabase Dashboard](https://supabase.com/dashboard/project/_/settings/api) $\rightarrow$ Project Settings $\rightarrow$ API $\rightarrow$ JWT Settings $\rightarrow$ JWT Secret | `backend/.env` (**Backend ONLY**) |
| **`DATABASE_URL`** | PostgreSQL | Direct async PostgreSQL connection string (`postgresql+asyncpg://...`) for direct SQLAlchemy ORM queries. | Optional (Alternative to Supabase REST SDK) | [Supabase Dashboard](https://supabase.com/dashboard/project/_/settings/database) $\rightarrow$ Database $\rightarrow$ Connection string (URI) | `backend/.env` |
| **`VIRUSTOTAL_API_KEY`** | VirusTotal (Google) | VirusTotal v3 REST API key for scanning URLs across 70+ antivirus and domain blocklists. | **Optional** (System gracefully degrades to `API_UNAVAILABLE` and redistributes weights if omitted) | [VirusTotal API Key](https://www.virustotal.com/gui/user/_/apikey) (Free tier available) | `backend/.env` (**Backend ONLY**) |
| **`VIRUSTOTAL_BASE_URL`**| VirusTotal | Base URL endpoint for VirusTotal v3 API calls. | Optional (Default: `"https://www.virustotal.com/api/v3"`) | [VirusTotal v3 API Docs](https://docs.virustotal.com/reference/overview) | `backend/.env` |
| **`VIRUSTOTAL_CACHE_TTL_SECONDS`**| Application | In-memory cache duration in seconds for VT vendor reports to protect free-tier rate limits. | Optional (Default: `3600` / 1 hour) | Backend performance setting. | `backend/.env` |
| **`URLHAUS_API_KEY`** | Abuse.ch URLhaus | Legacy placeholder. URLhaus queries do not require authentication. | Optional (Default: `""`) | [URLhaus API](https://urlhaus.abuse.ch/api/) | `backend/.env` |
| **`RATE_LIMIT_SCAN`** | SlowAPI / Security | Maximum scans allowed per IP address. | Optional (Default: `"5/minute"`) | Anti-abuse policy setting. | `backend/.env` |
| **`RATE_LIMIT_GLOBAL`**| SlowAPI / Security | Maximum general requests allowed per client IP. | Optional (Default: `"60/minute"`) | Anti-abuse policy setting. | `backend/.env` |
| **`VITE_API_BASE_URL`** | Frontend (Vite) | Base URL pointing the frontend client to the FastAPI backend API. | **Mandatory for Frontend** | Generated backend URL (e.g. `http://localhost:8000/api/v1`). | `frontend/.env` |

---

## 2. Current Credential Status in Repository

### A. Credentials Already Configured (Local Decoupled Mode)
The backend is currently configured with **100% functional local mock and decoupled drivers**, allowing development and automated testing without external Internet dependencies:
- **`APP_NAME`:** Configured as `"TrustGuard AI"`
- **`APP_ENV`:** Configured as `development`
- **`HOST` / `PORT`:** Configured as `0.0.0.0` / `8000`
- **`FRONTEND_URL`:** Configured as `"http://localhost:5173,http://localhost:3000"`
- **`ML_MODEL_PATH`:** Configured to pre-trained model artifact `ml/models/phishing_rf_v1.joblib` (Present in repository)
- **`ML_METADATA_PATH`:** Configured to `ml/models/model_metadata.json` (Present in repository)

### B. Placeholder / Mock Credentials in Local `.env`
The following keys currently use safe development placeholders in `backend/.env`:
- `SUPABASE_URL=https://your-project.supabase.co`
- `SUPABASE_ANON_KEY=your-supabase-anon-key-here`
- `SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key-here`
- `SUPABASE_JWT_SECRET=your-supabase-jwt-secret-here`
- `VIRUSTOTAL_API_KEY=your-virustotal-api-key-here`

### C. Services Operating Without Requiring External API Keys
TrustGuard AI was deliberately engineered so that core security engines function autonomously without third-party subscriptions:
1. **Machine Learning Phishing Classifier:**
   - Runs 100% locally on CPU using Scikit-Learn.
   - Evaluates 23 structural features against `ml/models/phishing_rf_v1.joblib` (98.17% accuracy).
   - **No external API key or network access required.**
2. **SSL/TLS Certificate Validation Engine:**
   - Connects directly to target hostnames on port 443 using standard Python `ssl` and `socket`.
   - Inspects cryptographic certificates, expiration dates, subject alternative names, and cipher suites.
   - **No external API key or subscription required.**
3. **URL Validation & Static Lexical Analysis:**
   - Pure Python parsing according to RFC 3986.
   - Performs SSRF checks, IP literal blocking, and suspicious keyword detection locally.
   - **No external API key required.**
4. **Digital Trust Score & Risk Assessment Engine:**
   - Multi-factor mathematical synthesis with dynamic weight redistribution.
   - **No external API key required.**
5. **URLhaus Abuse Feed:**
   - Free public API without registration.

---

## 3. How to Obtain Production Credentials (Step-by-Step)

### Step 1: Supabase Setup (PostgreSQL Database & Authentication)
1. Go to [https://supabase.com](https://supabase.com) and click **Sign Up** or **Sign In**.
2. Click **New Project**, select an organization, name the project (e.g. `trustguard-ai`), and choose a strong database password.
3. Once the project is provisioned (~2 minutes), navigate to:
   - **Settings (gear icon)** $\rightarrow$ **API**.
4. Copy the following values into `backend/.env`:
   - **Project URL** $\rightarrow$ `SUPABASE_URL`
   - **Project API Keys (`anon` / `public`)** $\rightarrow$ `SUPABASE_ANON_KEY`
   - **Project API Keys (`service_role` secret)** $\rightarrow$ `SUPABASE_SERVICE_ROLE_KEY`
   - **JWT Settings $\rightarrow$ JWT Secret** $\rightarrow$ `SUPABASE_JWT_SECRET`
5. Navigate to the **SQL Editor** in your Supabase dashboard and run the migrations in order:
   1. `backend/migrations/001_initial_schema.sql`
   2. `backend/migrations/002_row_level_security.sql`
   3. `backend/migrations/003_scan_history_enhancements.sql`
   4. `backend/migrations/004_community_reporting_enhancements.sql`

### Step 2: VirusTotal v3 API Key Setup
1. Go to [https://www.virustotal.com](https://www.virustotal.com) and create a free account.
2. Verify your email address and log in.
3. Click your username avatar in the top right $\rightarrow$ select **API key**.
4. Copy the 64-character hexadecimal key.
5. Paste into `backend/.env`:
   ```bash
   VIRUSTOTAL_API_KEY=your_actual_64_character_key_here
   ```
*(Note: VirusTotal free tier grants 4 requests/minute, 500 requests/day. The backend automatically caches results for 1 hour to respect this limit).*

---

## 4. Graceful Degradation Behavior

TrustGuard AI implements **zero-crash graceful degradation**:

| Scenario | System Behavior |
| :--- | :--- |
| **Supabase credentials missing / placeholder** | The backend automatically logs `Operating in local decoupled mode` and falls back to in-memory repositories. All auth, scan, history, and community endpoints continue to work seamlessly. |
| **VirusTotal API key missing / placeholder** | The backend marks the VirusTotal module `API_UNAVAILABLE`, logs a benign informational message, and dynamically redistributes weights to the remaining active feeds (ML 50%, URL Heuristics 25%, SSL/TLS 25%) without interrupting or failing the scan. |
| **VirusTotal rate limit (429) hit** | The backend catches the 429 status, marks the feed `RATE_LIMITED`, and scores the URL using all other available signals. |
| **Target website has no SSL / connection refused** | The SSL engine catches the timeout/refusal, sets status to `DNS_RESOLUTION_FAILED` or `HTTPS_NOT_USED`, assigns an appropriate subscore, and completes the scan. |

---

## 5. Security & Secret Protection Checklist

- [x] **NEVER commit `.env` to Git:** The file `backend/.env` is strictly matched in `.gitignore`.
- [x] **Sanitized Template in Version Control:** `backend/.env.example` contains only benign placeholders and comments.
- [x] **Service Role Isolation:** `SUPABASE_SERVICE_ROLE_KEY` is restricted exclusively to the backend server and is NEVER sent to frontend clients.
- [x] **Log Masking:** Application logs sanitize authorization tokens, database connection URIs, and third-party API keys.
- [x] **Centralized Settings:** All configuration reads occur through Pydantic Settings in `app/core/config.py`. No raw `os.environ` accesses occur across routes or business services.

