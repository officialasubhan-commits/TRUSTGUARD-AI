# TrustGuard AI — Frontend Application

The official web frontend for **TrustGuard AI**, an AI-powered website threat detection and digital trust intelligence platform.

Designed under the **Premium Monochromatic Digital Minimalism** paradigm with an interactive geometric pixel canvas engine.

---

## 🛠️ Technology Stack

- **Framework:** [React 18](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Language:** [TypeScript 5](https://www.typescriptlang.org/) (Strict mode)
- **Styling:** [Tailwind CSS 3.4](https://tailwindcss.com/)
- **Routing:** [React Router DOM 6](https://reactrouter.com/)
- **Animation & Motion:** [Framer Motion 11](https://www.framer.com/motion/) + Native HTML5 Canvas Pixel Engine
- **Visualizations:** [Recharts 2.x](https://recharts.org/)
- **Iconography:** [Lucide React](https://lucide.dev/)
- **HTTP Client:** [Axios 1.7](https://axios-http.com/)

---

## 🎨 Visual Identity & Design Tokens

- **Background (Primary):** `#080808` (`--bg-primary`)
- **Background (Secondary):** `#101010` (`--bg-secondary`)
- **Card Surface:** `#141414` (`--bg-surface`)
- **Elevated Surface:** `#181818` (`--bg-surface-elevated`)
- **Card Hover:** `#1C1C1C` (`--bg-surface-hover`)
- **Structural Border:** `#292929` (`--border-subtle`)
- **Strong Border:** `#383838` (`--border-strong`)
- **Primary Text:** `#F5F5F5` (`--text-primary`)
- **Secondary Text:** `#A1A1A1` (`--text-secondary`)
- **Muted Text:** `#666666` (`--text-muted`)
- **Security Status Tokens (Restrained):**
  - **Safe / Benign:** Text `#4ADE80`, Bg `#052E16`, Border `#166534`
  - **Suspicious / Warning:** Text `#FBBF24`, Bg `#451A03`, Border `#92400E`
  - **Malicious / Critical:** Text `#F87171`, Bg `#450A0A`, Border `#991B1B`
  - **Unknown / Offline:** Text `#A1A1A1`, Bg `#141414`, Border `#383838`
- **Typography:** Geist Sans & Geist Mono

---

## 🧩 Component Design System

Located in `src/components/common/`:

- **Button (`Button.tsx`):** Primary, Secondary, Outline, Ghost, Danger, Icon, Loading, and Pixel Corners.
- **Input (`Input.tsx`):** URL, Text, Password with visibility toggle, Search, Error and Focus states.
- **Card (`Card.tsx`):** Standard, Elevated, Panel, Information card, and Pixel corner brackets.
- **Badge (`Badge.tsx`):** Monochromatic and security status pills with dot/pulse options.
- **StatusIndicator (`StatusIndicator.tsx`):** High-precision status indicators (`safe`, `suspicious`, `malicious`, `unknown`).
- **Tooltip (`Tooltip.tsx`):** Accessible hover/focus micro-telemetry tooltip.
- **Divider (`Divider.tsx`):** 1px horizontal/vertical dividers with optional uppercase label.
- **Modal (`Modal.tsx`):** Accessible focus-trapped dialog with Escape key dismiss and backdrop blur.
- **Dropdown (`Dropdown.tsx`):** Monochromatic menu dropdown with trigger and custom actions.
- **Tabs (`Tabs.tsx`):** Accessible tab list with line or pill active indicators.
- **Skeleton (`Skeleton.tsx`):** Geometric loading skeletons (text, rectangle, circle, card).
- **PageLoader (`PageLoader.tsx`):** Full-page geometric spinner loader.
- **ErrorMessage (`ErrorMessage.tsx`):** Uniform error envelope display.
- **EmptyState (`EmptyState.tsx`):** Clean empty records card with icon and action.

---

## 🏠 Homepage & Landing Page Architecture

The production homepage (`/`) is composed of modular, accessible, monochromatic sections:

1. **Navigation Bar (`Navigation.tsx`):** Sticky, backdrop-blurred monochromatic header with brand mark, anchor navigation (`Product`, `How It Works`, `Security`, `Community`), and action buttons.
2. **Editorial Hero Section:** High-impact typography (*"Know what you're connecting to"*), clear value proposition, primary and secondary CTAs, and integrated `GeometricFormation` generative canvas.
3. **Homepage URL Scanner (`HomepageScanner.tsx`):** Prominently embedded URL input with pre-flight SSRF and syntax validation, autofocus, loading indicators, and route-preserving dispatch.
4. **Trust & Core Capabilities (`#capabilities`):** 4 modular blocks detailing URL Structure Analysis, VirusTotal Threat Feeds, Machine Learning Phishing Classification, and Cryptographic SSL/TLS Handshakes.
5. **How It Works (`#how-it-works`):** 3-step numbered workflow explaining the URL inspection lifecycle.
6. **Security Report Preview:** Realistically structured specimen demonstrating score gauges, risk categorization, multi-signal breakdown, and actionable recommendations (*explicitly marked as illustrative preview telemetry*).
7. **Privacy & Transparency:** Commitments to explainable security, dynamic weight re-normalization when feeds are offline, and auditability.
8. **Community Threat Defense:** Introduction to whistleblower threat reporting and collaborative protection with a direct link to the community feed.
9. **Platform Footer (`Footer.tsx`):** Brand information, product links, legal and operational security disclaimers, and copyright notices.

---

## ⚡ Geometric Pixel Animation Engine

Located in `src/components/geometric/`:

- **`PixelBackground` (`PixelBackground.tsx`):** **Global cursor-reactive background canvas** integrated in `RootLayout`. Tracks window-level pointer coordinates, dynamically displacing nodes within an interaction radius with heightened luminance. Features route awareness (automatically bypassing `/` to preserve the hero animation without double-rendering), mobile ambient wave modulation with 45% reduced node count, and static rendering under `prefers-reduced-motion`.
- **`InteractivePixelGrid` (`InteractivePixelGrid.tsx`):** 60 FPS cursor-responsive canvas component; squares displace smoothly away from cursor proximity ($110\text{px}$) with heightened luminance. Powers the homepage hero section.
- **`PixelGrid` (`PixelGrid.tsx`):** Precision SVG coordinate grid with crosshairs and coordinate markers.
- **`GeometricPixelField` (`GeometricPixelField.tsx`):** High-performance HTML5 Canvas wave interference field with Perlin drift and responsive particle reduction.
- **`GeometricFormation` (`GeometricFormation.tsx`):** Mathematical morphing engine between 4 cryptographic patterns (`shield`, `matrix`, `crosshair`, `horizon`).
- **`ScanningLine` (`ScanningLine.tsx`):** Horizontal/vertical telemetry beam with trailing packet dissolution particles.
- **`PixelReveal` (`PixelReveal.tsx`):** Stepped entrance animation with corner pixel flashes.
- **`GeometricTransition` (`GeometricTransition.tsx`):** Staggered geometric container for list and grid entrances.

---

## 🔍 URL Scanner & Backend Integration

Located in `src/pages/ScannerPage.tsx` and `src/hooks/useScan.ts`:

- **Dedicated Scanner Route:** `/scan` (accepts query parameters such as `/scan?url=...`).
- **Real-Time Client-Side Validation (`src/utils/validators.ts`):**
  - Protocol auto-inference (`https://` default prepend).
  - RFC 1918 & Cloud Metadata SSRF Protection (prohibits `localhost`, `127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`, `169.254.169.254`).
  - Top-Level Domain (TLD) and character validity checks.
- **Backend API Integration (`src/services/scanService.ts`):**
  - Connects directly to `POST /api/v1/scan`.
  - AbortController cancellation via `cancelScan()`.
  - Strictly typed responses matching `URLSubmissionResponse` (Digital Trust Score, Risk Level, Heuristics, ML Prediction, SSL Analysis, Recommendations).
- **Geometric Pipeline Loading State:**
  - Integrated `ScanningLine` canvas animation.
  - 5-step visual pipeline:
    1. `URL Normalization & Lexical Analysis`
    2. `Threat Feed Intelligence (VirusTotal)`
    3. `Machine Learning Classification`
    4. `SSL/TLS Certificate Audit`
    5. `Trust Score Synthesis`
  - Real-time elapsed stopwatch timer and immediate cancel button.
- **Scan Result Summary Transition:**
  - Displays target normalized URL, Digital Trust Score (0-100), Risk Level badge, ML Phishing Probability, SSL status, and heuristic indicators.
  - Action button routing directly to `/report/:scanId`.
- **Session Scan History:**
  - Stores last 5 scans in `sessionStorage` (`trustguard_recent_scans`).
  - Quick reload and one-click navigation with session clear option.

---

## 👁️ Interactive Showcases

- **Design System Showcase:** `http://localhost:5173/design-system`
- **Geometric Animation Showcase:** `http://localhost:5173/animations`

---

## 📁 Directory Structure

```text
frontend/
├── public/                         # Public static assets & favicon
├── src/
│   ├── assets/                     # Vector graphics and branding marks
│   ├── components/                 # Component library
│   │   ├── common/                 # Reusable UI primitives (Button, Input, Card, Modal)
│   │   ├── layout/                 # Shell components (Navigation, Footer)
│   │   ├── geometric/              # Geometric canvas & pixel lattice components
│   │   ├── scanner/                # Scanner-specific inputs & telemetry panels
│   │   ├── dashboard/              # User metrics and analytics charts
│   │   ├── reports/                # Security breakdown and assessment evidence
│   │   └── community/              # Community threat feed and reporting cards
│   ├── pages/                      # Route page components
│   │   ├── HomePage.tsx            # / — Platform overview & hero
│   │   ├── ScannerPage.tsx         # /scan — Multi-layer URL scanner
│   │   ├── ReportPage.tsx          # /report/:scanId — Assessment report
│   │   ├── LoginPage.tsx           # /login — Authentication portal
│   │   ├── RegisterPage.tsx        # /register — New account registration
│   │   ├── DashboardPage.tsx       # /dashboard — User metrics and telemetry
│   │   ├── HistoryPage.tsx         # /history — Paginated scan history
│   │   ├── CommunityPage.tsx       # /community — Public threat feed
│   │   ├── ProfilePage.tsx         # /profile — Analyst account profile
│   │   ├── AdminPage.tsx           # /admin — Moderation desk
│   │   └── NotFoundPage.tsx        # 404 — Not found
│   ├── layouts/                    # Layout shells (RootLayout)
│   ├── hooks/                      # Custom React hooks
│   ├── services/                   # API clients & configuration (api.ts, apiConfig.ts)
│   ├── context/                    # Global state providers
│   ├── types/                      # TypeScript definitions (api, auth, scan)
│   ├── utils/                      # Helper utilities (cn, formatters)
│   ├── styles/                     # Tailwind & global stylesheet (globals.css)
│   ├── App.tsx                     # Top-level Router configuration
│   └── main.tsx                    # Application entry point
├── .env.example                    # Environment template
├── .gitignore                      # Git exclusion rules
├── package.json                    # Dependencies & build scripts
├── tsconfig.json                   # TypeScript configuration
├── vite.config.ts                  # Vite build configuration
└── README.md                       # Setup and developer documentation
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to create your local `.env`:

```bash
cp .env.example .env
```

| Variable Name | Required | Default Value | Description |
| :--- | :---: | :--- | :--- |
| `VITE_API_BASE_URL` | **Yes** | `http://localhost:8000/api/v1` | URL of the FastAPI backend API |

*Note: The frontend bundle never contains private API keys or database secrets.*

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The application will start at: `http://localhost:5173/`

### 3. TypeScript Type-Checking

```bash
npm run lint
```

### 4. Build for Production

```bash
npm run build
```

Production output will be generated in `frontend/dist/`.

