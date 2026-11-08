# TrustGuard AI — Pre-Deployment Readiness Guide

**Target Environments:**
- **Frontend Hosting:** Vercel (Edge CDN, Vite React SPA)
- **Backend Hosting:** Render (Web Service, Python 3.11 FastAPI)
- **Database & Auth:** Supabase PostgreSQL & Supabase Auth

---

## 1. Vercel Frontend Deployment Specification

### 1.1 Project Settings in Vercel Dashboard
- **Framework Preset:** Vite
- **Root Directory:** `frontend` (if deploying from a root monorepo) or repository root
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`
- **Node.js Version:** `18.x` or `20.x`
- **Routing Configuration:** Configured in `frontend/vercel.json` with SPA rewrites (`"source": "/(.*)", "destination": "/index.html"`) to prevent 404s on direct navigation or refresh.

### 1.2 Frontend Environment Variables Checklist (Vercel)
| Variable | Value / Description | Sensitive? |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `https://trustguard-ai-backend.onrender.com/api/v1` *(replace with actual Render service URL)* | No (Public) |
| `VITE_GOOGLE_CLIENT_ID` | `your-google-client-id.apps.googleusercontent.com` | No (Public Client ID) |

> [!CAUTION]
> Never add `SUPABASE_SERVICE_ROLE_KEY` or `GOOGLE_CLIENT_SECRET` to frontend environment variables.

---

## 2. Render Backend Deployment Specification

### 2.1 Web Service Settings in Render Dashboard
- **Service Type:** Web Service
- **Environment:** `Python 3`
- **Repository:** `https://github.com/officialasubhan-commits/TRUSTGUARD-AI`
- **Branch:** `main`
- **Build Command:** `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/api/v1/health`
- **Auto-Deploy:** Enabled on push to `main`

### 2.2 Backend Environment Variables Checklist (Render)
| Variable Name | Required Value / Source |
| :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` |
| `APP_NAME` | `TrustGuard AI` |
| `APP_ENV` | `production` |
| `APP_DEBUG` | `false` |
| `API_V1_PREFIX` | `/api/v1` |
| `FRONTEND_URL` | `https://your-app.vercel.app` *(add both production and localhost if needed, comma-separated)* |
| `RATE_LIMIT_SCAN` | `5/minute` |
| `RATE_LIMIT_GLOBAL` | `60/minute` |
| `SUPABASE_URL` | `https://gtkiuspypsqgornxsafl.supabase.co` |
| `SUPABASE_ANON_KEY` | *(From Supabase Dashboard -> Settings -> API -> anon/public)* |
| `SUPABASE_SERVICE_ROLE_KEY` | *(From Supabase Dashboard -> Settings -> API -> service_role)* |
| `SUPABASE_JWT_SECRET` | *(From Supabase Dashboard -> Settings -> API -> JWT Secret)* |
| `DATABASE_URL` | *(PostgreSQL connection URI from Supabase)* |
| `VIRUSTOTAL_API_KEY` | *(Your VirusTotal v3 API Key)* |
| `GOOGLE_CLIENT_ID` | `your-google-client-id.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | `your-google-client-secret` |

---

## 3. External Dashboard Settings (Manual Action Required)

### 3.1 Google Cloud Console (`console.cloud.google.com`)
1. Navigate to **APIs & Services** → **Credentials**.
2. Select your OAuth 2.0 Web Client.
3. **Authorized JavaScript origins:**
   - `http://localhost:5173`
   - `https://gtkiuspypsqgornxsafl.supabase.co`
   - `https://your-frontend.vercel.app`
4. **Authorized redirect URIs:**
   - `https://gtkiuspypsqgornxsafl.supabase.co/auth/v1/callback` *(CRITICAL: Must point to Supabase, NOT frontend)*
5. Click **Save**.

### 3.2 Supabase Dashboard (`supabase.com/dashboard/project/gtkiuspypsqgornxsafl`)
1. Navigate to **Authentication** → **Providers** → **Google**:
   - Set **Enable Sign in with Google** to **ON**.
   - **Client ID:** `your-google-client-id.apps.googleusercontent.com`
   - **Client Secret:** `your-google-client-secret`
   - Click **Save**.
2. Navigate to **Authentication** → **URL Configuration**:
   - **Site URL:** `https://your-frontend.vercel.app` (or `http://localhost:5173` during development)
   - **Redirect URLs:**
     - `http://localhost:5173/**`
     - `http://localhost:5173/auth/callback`
     - `https://*.vercel.app/**`
     - `https://*.vercel.app/auth/callback`
     - `https://your-custom-domain.com/**`
   - Click **Save**.
3. Navigate to **SQL Editor**:
   - Execute migration `backend/migrations/007_admin_panel_schema.sql` to initialize `admin_users`, `admin_audit_logs`, and `system_settings` tables in PostgreSQL.

---

## 4. Production Smoke-Test Checklist

- [ ] **Health Endpoint:** `GET https://your-backend.onrender.com/api/v1/health` returns `{"status": "healthy"}`.
- [ ] **Homepage & Scanner:** Frontend loads cleanly without console errors.
- [ ] **URL Scanning:** Submitting `https://github.com` returns a valid completed security report with Trust Score.
- [ ] **Email/Password Auth:** Registering a new user and logging in succeeds.
- [ ] **Google Sign-In:** Clicking "Continue with Google" opens the Google account chooser and returns to `/dashboard` with an active session.
- [ ] **Community Reports:** Submitting and viewing verified threat reports displays correctly.
- [ ] **Admin Authentication:** Accessing `/admin/login` and signing in with provisioned administrator credentials opens `/admin`.
- [ ] **System Diagnostics:** `/admin/system` reports green health status across services.
- [ ] **Maintenance Mode:** Toggling maintenance mode blocks public visitors with HTTP 503 and overlay screen, while preserving administrative workspace.

