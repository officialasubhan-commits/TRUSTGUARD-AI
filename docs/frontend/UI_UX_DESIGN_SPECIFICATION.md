# TrustGuard AI — UI/UX Design Specification

**Design Theme:** Premium Monochromatic Digital Minimalism with Geometric Pixel Animation  
**Primary Brand Philosophy:** Understated Authority, Cryptographic Precision, Mathematical Elegance  
**Target Viewports:** Responsive Web (Mobile 360px+, Tablet 768px+, Desktop 1024px+, Ultra-wide 1440px+)  

---

## 1. Visual Identity & Anti-Patterns

### Core Aesthetic Principles
TrustGuard AI is designed as a mission-critical cybersecurity intelligence instrument, not a generic consumer application or an exaggerated gaming tool. The design communicates uncompromising precision, high signal-to-noise ratio, and mathematical elegance.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      TRUSTGUARD DESIGN MANDATE                         │
├──────────────────────────────────┬─────────────────────────────────────┤
│ DO ENFORCE                       │ STRICT ANTI-PATTERNS (FORBIDDEN)    │
├──────────────────────────────────┼─────────────────────────────────────┤
│ ✓ Pure monochromatic hierarchy   │ ✗ No cartoon robots or AI mascots   │
│ ✓ Razor-sharp 1px borders (#292929)│ ✗ No glowing neon cyan/magenta/green│
│ ✓ Geometric pixel grid motifs    │ ✗ No cyberpunk or sci-fi clichés    │
│ ✓ Monospaced data telemetry      │ ✗ No heavy glassmorphism/blurs      │
│ ✓ Subtle, purposeful movement    │ ✗ No multi-color gradient mesh      │
│ ✓ High whitespace and breathing room│ ✗ No generic bootstrap card templates│
└──────────────────────────────────┴─────────────────────────────────────┘
```

---

## 2. Complete Color Palette

The color system is strictly monochromatic. Subtle variations in luminance and contrast replace loud primary colors to communicate structure, state, and hierarchy.

```text
#080808 (Deep Black Background)
   └── #101010 (Secondary Canvas Background)
         └── #141414 (Card & Surface Background)
               └── #292929 (Structural 1px Border)
                     └── #666666 (Muted Text & Inactive Elements)
                           └── #A1A1A1 (Secondary Text & Supporting Telemetry)
                                 └── #F5F5F5 (Primary Text & Pure High-Contrast Focus)
```

### Color Specification Table

| Token Name | Hex Code | RGB | Usage Description |
| :--- | :--- | :--- | :--- |
| `bg-primary` | `#080808` | `rgb(8, 8, 8)` | Global viewport canvas background; deep absorbing black. |
| `bg-secondary`| `#101010` | `rgb(16, 16, 16)`| Alternate section backgrounds, table headers, and modal backdrop. |
| `bg-surface` | `#141414` | `rgb(20, 20, 20)`| Elevated interactive surfaces: cards, dropdowns, and flyout panels. |
| `bg-surface-hover` | `#1A1A1A` | `rgb(26, 26, 26)`| Interactive surface hover state. |
| `border-subtle` | `#292929` | `rgb(41, 41, 41)`| Standard 1px boundary lines, card borders, and table separators. |
| `border-active` | `#404040` | `rgb(64, 64, 64)`| Focused input fields, active tab indicators, and highlighted cards. |
| `text-primary` | `#F5F5F5` | `rgb(245, 245, 245)`| Main headings, critical metrics, and high-emphasis labels. |
| `text-secondary`| `#A1A1A1` | `rgb(161, 161, 161)`| Body copy, descriptions, subtitles, and supporting labels. |
| `text-muted` | `#666666` | `rgb(102, 102, 102)`| Metadata, timestamps, table column headers, and disabled states. |

### Monochromatic Semantic Score Mapping
To maintain the monochromatic mandate while conveying urgent security warnings, risk levels are expressed primarily through **luminance, typography weight, geometric iconography, and restrained tonal indicators** (rather than garish red/yellow/green blobs):

| Risk Classification | Trust Score | Visual Representation | Geometric Symbol |
| :--- | :---: | :--- | :---: |
| **CRITICAL RISK** | 0 – 24 | Inverted High-Contrast Badge (`bg-[#F5F5F5] text-[#080808] font-bold`) | `[ ■ ■ ■ ■ ]` |
| **HIGH RISK** | 25 – 49 | Solid High-Emphasis Border (`border-[#F5F5F5] text-[#F5F5F5]`) | `[ ■ ■ ■ □ ]` |
| **MODERATE RISK** | 50 – 74 | Neutral Subtle Tone (`border-[#404040] text-[#A1A1A1]`) | `[ ■ ■ □ □ ]` |
| **LOW / MINIMAL** | 75 – 100 | Refined Muted Outline (`border-[#292929] text-[#666666]`) | `[ ■ □ □ □ ]` |

---

## 3. Typography Hierarchy

The typography pairs **Geist Sans** (for elegant, modern, highly legible editorial content) with **Geist Mono** (for cryptographic hashes, technical indicators, URLs, and numeric data).

### Type Scale Specification

| Role | Font Family | Size | Weight | Tracking | Line Height |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display Hero** | Geist Sans | `48px` / `3.0rem` | Light (`300`) | `-0.04em` | `1.1` |
| **Page Title (H1)**| Geist Sans | `32px` / `2.0rem` | Normal (`400`) | `-0.03em` | `1.2` |
| **Section Header (H2)**| Geist Sans | `24px` / `1.5rem` | Medium (`500`) | `-0.02em` | `1.3` |
| **Card Header (H3)**| Geist Sans | `18px` / `1.125rem`| Medium (`500`) | `-0.01em` | `1.4` |
| **Body Standard** | Geist Sans | `14px` / `0.875rem`| Regular (`400`)| `normal` | `1.6` |
| **Body Compact** | Geist Sans | `13px` / `0.8125rem`| Regular (`400`)| `normal` | `1.5` |
| **Mono Metric** | Geist Mono | `28px` / `1.75rem` | SemiBold (`600`)| `-0.02em` | `1.0` |
| **Mono URL / Hash**| Geist Mono | `13px` / `0.8125rem`| Regular (`400`)| `+0.01em` | `1.4` |
| **Mono Caption** | Geist Mono | `11px` / `0.6875rem`| Regular (`400`)| `+0.05em` | `1.4` |

---

## 4. Geometric Pixel Animation System

The central visual motif of TrustGuard AI is the **Geometric Pixel Lattice**. It embodies the conversion of raw internet data packets into crystal-clear risk intelligence.

```text
     ┌──┐                     ┌──┐
     │  │  ┌──┐         ┌──┐  └──┘
     └──┘  │  │   ┌──┐  └──┘
           └──┘   │  │
                  └──┘
  ═════════════════════════════════════  ◄── Scanning Beam (Y-Axis)
                  ┌──┐
     ┌──┐         │  │   ┌──┐
     │  │   ┌──┐  └──┘   └──┘
     └──┘   └──┘
```

### Motion Archetypes & Execution

#### 1. Interactive Canvas Grid Lattice (`PixelBackground.tsx`)
- **Structure:** A viewport-spanning coordinate grid of microscopic squares (each `3px x 3px` on a `24px x 24px` pitch).
- **Idle State:** Pixels oscillate in opacity between `0.04` and `0.14` using a Perlin-noise mathematical drift.
- **Mouse Proximity Influence:** When the user moves their cursor across the viewport, pixels within an `80px` radius gently increase in opacity to `0.45` and shift outward by `2px to 4px`, creating a dynamic geometric gravitational field.
- **Performance:** Rendered via 2D Canvas `requestAnimationFrame` maintaining `60 FPS` at $< 2\%$ CPU utilization. Automatically pauses when tab loses focus.

#### 2. Scanning-Line Beam Animation (`PixelScanner.tsx`)
- **Application:** Triggered during active URL analysis on the `/scan` page.
- **Visual:** A crisp `1px` horizontal line (`#F5F5F5` with `0.7` opacity) sweeps down the target URL input card.
- **Accompanying Effect:** As the line traverses the card, small `4px` squares materialize beneath the beam and gently dissolve, symbolizing cryptographic packet inspection.
- **Duration:** Cycles smoothly over `2.4s` using a linear ease function.

#### 3. Pixel Formation & Dissolution Micro-Interactions
- **Buttons (`Button.tsx`):** On hover, 4 tiny pixel dots (`2px x 2px`) fade into the 4 external corners of the button border, locking into place.
- **Card Focus (`Card.tsx`):** When hovering over a detailed report card, a corner bracket `[  ]` pixel configuration sharpens from `#292929` to `#F5F5F5`.
- **Trust Score Materialization (`TrustScoreGauge.tsx`):** The numerical score counts up from `0` to the computed value while the perimeter circular gauge fills in stepped pixel arcs rather than smooth blurry fills.

#### 4. Accessibility & Motion Safeguards
All animations strictly respect user system accessibility preferences:
```css
@media (prefers-reduced-motion: reduce) {
  canvas#pixel-background {
    display: none;
  }
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 5. Page Layout Wireframes & Spatial Design

### A. Homepage (`/`)
- **Navigation Bar:** Fixed at top, `h-14`, border-bottom `1px solid #292929`, backdrop blur `4px`, brand logo (minimalist square glyph + "TRUSTGUARD AI"), links: "Scanner", "Community", "Docs", and "Sign In / Register".
- **Hero Section:**
  - Status indicator pill: `[ ● OPERATIONAL ] v1.0.0 ENGINE ONLINE`
  - Headline: "Autonomous Digital Trust & Threat Intelligence."
  - Subhead: "Instant multi-engine phishing, SSL/TLS, and heuristic reputation inspection for the modern web."
  - Embedded Fast Scan Bar: Full-width search bar allowing instant guest scanning with zero clicks.
- **Feature Matrix:** 4 minimalist cards detailing the 4 security inspection layers (VirusTotal Telemetry, Random Forest ML, Cryptographic SSL Audit, Structural Heuristics).
- **Live Community Threat Ticker:** Compact horizontal feed showcasing recently verified malicious domains.

### B. URL Scanner & Analysis Console (`/scan`)
- **Central Control Panel:**
  - High-visibility monospaced input field with instant protocol prefix handling (`https://` by default).
  - Multi-threaded progress stepper:
    1. `LEXICAL_ANALYSIS` (URL syntax and heuristics)
    2. `REPUTATION_FEED` (VirusTotal multi-vendor consensus)
    3. `CRYPTOGRAPHIC_AUDIT` (SSL/TLS certificate handshake)
    4. `NEURAL_CLASSIFICATION` (Random Forest phishing inference)
    5. `TRUST_SYNTHESIS` (Score calculation and override evaluation)

### C. Comprehensive Security Assessment Report (`/scan/:id`)
- **Top Summary Banner:**
  - Large Monospaced Trust Score (e.g. `20 / 100`) accompanied by Risk Badge (`CRITICAL RISK`).
  - Scan metadata: Target URL, Domain, Resolved IP, Submission Timestamp, and Guest/User Attribution.
  - Action buttons: "Export JSON", "Share Report", "Report as False Positive".
- **Evidence Grid (2 x 2 Balanced Matrix):**
  1. **Card 1: Machine Learning Phishing Classification** (Prediction verdict, 98% probability bar, active model version `rf-v1.0.0`).
  2. **Card 2: SSL/TLS Handshake & Certificate** (TLS 1.3 verification, 85 days remaining, issuer authority, SAN domain validation).
  3. **Card 3: External Threat Feeds (VirusTotal)** (Vendor detection ratio, malicious hits, clean verdicts, or "Telemetry Unavailable" clean fallback).
  4. **Card 4: Lexical & Heuristic Indicators** (Detected suspicious keywords, entropy level, path depth, hyphen counts).
- **Actionable Mitigation Checklist:** Bulleted instructions for end users (e.g., "Do not enter credentials", "Domain flagged for credential harvesting").

### D. User Dashboard & History (`/dashboard` & `/history`)
- **Executive Metric Cards:** Total Scans, Average Trust Score, Malicious URLs Detected, Clean Certificates.
- **Search & Filter Console:**
  - Debounced keyword search input.
  - Risk Level dropdown (`ALL`, `CRITICAL`, `HIGH`, `MODERATE`, `LOW`).
  - Date range quick-filters (`Today`, `Last 7 Days`, `Last 30 Days`).
- **Data Table:**
  - Column headers: `DOMAIN`, `TRUST SCORE`, `RISK LEVEL`, `STATUS`, `DATE`, `ACTIONS`.
  - Row hover reveals inline action triggers ("View Report", "Export", "Delete").
  - Server-side pagination controls at bottom right.

### E. Community Threat Hub (`/community`)
- **Submission Trigger:** "Submit Suspicious URL" modal dialog.
- **Public Feed:** Community-vetted threats displaying domain, category (`PHISHING`, `MALWARE`, `SCAM`), upvote count, verification badge (`ADMIN_VERIFIED`), and date.
- **Reporter Privacy:** Submitter identities are completely redacted to ensure anonymous whistleblower security.

### F. Administrative Moderation Console (`/admin`)
- **Moderation Queue:** Paginated list of pending community submissions.
- **Review Drawer:** Slide-over modal showing full URL, submitter IP, automated scanner cross-reference, and input fields for `Moderation Verdict` (`APPROVED`, `REJECTED`, `DUPLICATE`) and `Analyst Notes`.

