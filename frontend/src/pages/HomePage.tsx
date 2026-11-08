import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Cpu,
  Lock,
  Globe,
  Binary,
  Users,
} from 'lucide-react';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { HomepageScanner } from '../components/scanner/HomepageScanner';
import {
  GeometricFormation,
  InteractivePixelGrid,
  PixelReveal,
  GeometricTransition,
} from '../components/geometric';

export const HomePage: React.FC = () => {
  const scrollToScanner = () => {
    const scannerEl = document.getElementById('scanner');
    if (scannerEl) {
      scannerEl.scrollIntoView({ behavior: 'smooth' });
      const input = scannerEl.querySelector('input');
      input?.focus();
    }
  };

  const scrollToHowItWorks = () => {
    const el = document.getElementById('how-it-works');
    el?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="flex-1 flex flex-col space-y-24 md:space-y-36 pb-24">
      {/* =========================================================================
          1. HERO SECTION WITH CURSOR-REACTIVE PIXEL GRID
          ========================================================================= */}
      <section className="relative border-b border-[#292929] overflow-hidden">
        <InteractivePixelGrid
          pixelSize={3}
          gap={22}
          interactionRadius={120}
          displacementStrength={8}
          baseOpacity={0.08}
          activeOpacity={0.6}
          className="pt-12 md:pt-20 pb-16 md:pb-24 bg-[#080808]"
        >
          <Container size="xl">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
              {/* Left Editorial Copy */}
              <div className="lg:col-span-7 space-y-8">
                <PixelReveal delay={0.05}>
                  <div className="inline-flex items-center space-x-2 px-3 py-1 bg-[#141414] border border-[#292929] text-xs font-mono text-[#A1A1A1]">
                    <span className="w-1.5 h-1.5 bg-[#4ADE80] rounded-full animate-pulse" />
                    <span>AUTONOMOUS DIGITAL TRUST ASSESSMENT // V1.0.0</span>
                  </div>
                </PixelReveal>

                <PixelReveal delay={0.12}>
                  <h1 className="text-4xl sm:text-5xl lg:text-6xl font-light tracking-tight text-[#F5F5F5] leading-[1.1]">
                    Know what you&apos;re connecting to.
                  </h1>
                </PixelReveal>

                <PixelReveal delay={0.18}>
                  <p className="text-base sm:text-lg text-[#A1A1A1] max-w-xl font-sans leading-relaxed">
                    Analyse websites, identify potential threats, and make informed decisions before
                    you browse.
                  </p>
                </PixelReveal>

                <PixelReveal delay={0.24}>
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2">
                    <Button
                      size="lg"
                      onClick={scrollToScanner}
                      rightIcon={<ArrowRight className="w-4 h-4" />}
                      pixelCorners
                    >
                      ANALYSE A URL
                    </Button>
                    <Button variant="secondary" size="lg" onClick={scrollToHowItWorks}>
                      EXPLORE HOW IT WORKS
                    </Button>
                  </div>
                </PixelReveal>
              </div>

              {/* Right Generative Geometric Visual */}
              <div className="lg:col-span-5 relative flex items-center justify-center">
                <PixelReveal delay={0.3} className="w-full">
                  <Card
                    variant="panel"
                    className="p-0 overflow-hidden relative h-[320px] sm:h-[380px] border border-[#292929] flex items-center justify-center bg-[#080808]/90"
                  >
                    <GeometricFormation pattern="cycle" pixelCount={64} size={4} cycleInterval={4000} />
                    <div className="absolute top-4 left-4 text-[10px] font-mono text-[#666666] tracking-widest pointer-events-none">
                      [ MATHEMATICAL LATTICE FORMATION ]
                    </div>
                    <div className="absolute bottom-4 right-4 text-[10px] font-mono text-[#666666] tracking-widest pointer-events-none">
                      60 FPS // BUFFER ZERO
                    </div>
                  </Card>
                </PixelReveal>
              </div>
            </div>

            {/* =========================================================================
                2. HOMEPAGE URL SCANNER (IMMEDIATELY VISIBLE)
                ========================================================================= */}
            <div className="mt-14 md:mt-20">
              <PixelReveal delay={0.35}>
                <HomepageScanner />
              </PixelReveal>
            </div>
          </Container>
        </InteractivePixelGrid>
      </section>

      {/* =========================================================================
          3. TRUST AND CAPABILITY SECTION
          ========================================================================= */}
      <section id="capabilities" className="relative">
        <Container size="xl">
          <div className="space-y-12">
            <div className="space-y-3 max-w-2xl">
              <span className="text-xs font-mono text-[#666666] uppercase tracking-widest">
                CORE VERIFICATION ENGINES
              </span>
              <h2 className="text-2xl sm:text-3xl font-light text-[#F5F5F5] tracking-tight">
                Multi-layer inspection for modern threat surfaces.
              </h2>
              <p className="text-sm text-[#A1A1A1] leading-relaxed">
                TrustGuard AI runs four concurrent verification pipelines to deliver an objective,
                probabilistic assessment of any submitted web address.
              </p>
            </div>

            <GeometricTransition className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Capability 1 */}
              <Card variant="standard" hoverEffect className="space-y-4">
                <div className="w-10 h-10 bg-[#101010] border border-[#292929] flex items-center justify-center text-[#F5F5F5]">
                  <Binary className="w-5 h-5" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="font-mono text-xs uppercase tracking-wider text-[#F5F5F5] font-semibold">
                    1. URL Structure Analysis
                  </h3>
                  <p className="text-xs text-[#A1A1A1] leading-relaxed">
                    Identify suspicious URL patterns and characteristics. Extracts lexical depth,
                    entropy variations, and character anomalies.
                  </p>
                </div>
                <div className="pt-2 border-t border-[#292929] text-[10px] font-mono text-[#666666]">
                  LEXICAL & HEURISTIC ENGINE
                </div>
              </Card>

              {/* Capability 2 */}
              <Card variant="standard" hoverEffect className="space-y-4">
                <div className="w-10 h-10 bg-[#101010] border border-[#292929] flex items-center justify-center text-[#F5F5F5]">
                  <Globe className="w-5 h-5" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="font-mono text-xs uppercase tracking-wider text-[#F5F5F5] font-semibold">
                    2. Threat Intelligence
                  </h3>
                  <p className="text-xs text-[#A1A1A1] leading-relaxed">
                    Analyse available external threat intelligence findings. Queries 70+ security
                    vendors via VirusTotal API v3 with automatic caching.
                  </p>
                </div>
                <div className="pt-2 border-t border-[#292929] text-[10px] font-mono text-[#666666]">
                  MULTI-VENDOR CONSENSUS
                </div>
              </Card>

              {/* Capability 3 */}
              <Card variant="standard" hoverEffect className="space-y-4">
                <div className="w-10 h-10 bg-[#101010] border border-[#292929] flex items-center justify-center text-[#F5F5F5]">
                  <Cpu className="w-5 h-5" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="font-mono text-xs uppercase tracking-wider text-[#F5F5F5] font-semibold">
                    3. Machine Learning Detection
                  </h3>
                  <p className="text-xs text-[#A1A1A1] leading-relaxed">
                    Estimate potential phishing risk using our Random Forest classifier trained on
                    structural features with 98.17% validation accuracy.
                  </p>
                </div>
                <div className="pt-2 border-t border-[#292929] text-[10px] font-mono text-[#666666]">
                  RF MODEL V1.0.0
                </div>
              </Card>

              {/* Capability 4 */}
              <Card variant="standard" hoverEffect className="space-y-4">
                <div className="w-10 h-10 bg-[#101010] border border-[#292929] flex items-center justify-center text-[#F5F5F5]">
                  <Lock className="w-5 h-5" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="font-mono text-xs uppercase tracking-wider text-[#F5F5F5] font-semibold">
                    4. SSL/TLS Validation
                  </h3>
                  <p className="text-xs text-[#A1A1A1] leading-relaxed">
                    Examine certificate validity and connection security. Performs direct socket
                    handshakes to audit expiration and root CA trust.
                  </p>
                </div>
                <div className="pt-2 border-t border-[#292929] text-[10px] font-mono text-[#666666]">
                  CRYPTOGRAPHIC HANDSHAKE
                </div>
              </Card>
            </GeometricTransition>
          </div>
        </Container>
      </section>

      {/* =========================================================================
          4. HOW IT WORKS SECTION
          ========================================================================= */}
      <section id="how-it-works" className="relative">
        <Container size="xl">
          <div className="space-y-12">
            <div className="space-y-3 max-w-2xl">
              <span className="text-xs font-mono text-[#666666] uppercase tracking-widest">
                STREAMLINED WORKFLOW
              </span>
              <h2 className="text-2xl sm:text-3xl font-light text-[#F5F5F5] tracking-tight">
                From target URL to evidence-based assessment.
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card variant="panel" className="space-y-4 p-8 relative">
                <div className="text-3xl font-mono text-[#666666] font-light">01</div>
                <h3 className="font-mono text-sm uppercase text-[#F5F5F5] font-semibold tracking-wider">
                  Submit a URL
                </h3>
                <p className="text-xs text-[#A1A1A1] leading-relaxed">
                  Enter any website address. The client automatically sanitises the protocol and
                  applies pre-flight SSRF protection to block private network addresses.
                </p>
              </Card>

              <Card variant="panel" className="space-y-4 p-8 relative">
                <div className="text-3xl font-mono text-[#666666] font-light">02</div>
                <h3 className="font-mono text-sm uppercase text-[#F5F5F5] font-semibold tracking-wider">
                  Analyse security signals
                </h3>
                <p className="text-xs text-[#A1A1A1] leading-relaxed">
                  The backend fans out concurrent async inspection tasks across VirusTotal, the
                  Random Forest classifier, direct SSL handshakes, and lexical heuristics.
                </p>
              </Card>

              <Card variant="panel" className="space-y-4 p-8 relative">
                <div className="text-3xl font-mono text-[#666666] font-light">03</div>
                <h3 className="font-mono text-sm uppercase text-[#F5F5F5] font-semibold tracking-wider">
                  Review your Assessment
                </h3>
                <p className="text-xs text-[#A1A1A1] leading-relaxed">
                  Inspect the unified 0–100 Digital Trust Score, clear risk category, underlying
                  evidence from each module, and specific browsing guidance.
                </p>
              </Card>
            </div>
          </div>
        </Container>
      </section>

      {/* =========================================================================
          5. SECURITY REPORT PREVIEW (SPECIMEN TELEMETRY)
          ========================================================================= */}
      <section className="relative">
        <Container size="xl">
          <div className="space-y-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-xs font-mono text-[#666666] uppercase tracking-widest">
                  ASSESSMENT TELEMETRY SPECIMEN
                </span>
                <h2 className="text-2xl sm:text-3xl font-light text-[#F5F5F5] tracking-tight">
                  Transparent, explainable risk intelligence.
                </h2>
              </div>
              <Badge variant="subtle" className="text-[10px]">
                PREVIEW SPECIMEN // ILLUSTRATIVE TELEMETRY ONLY
              </Badge>
            </div>

            {/* Specimen Report Card */}
            <Card variant="elevated" pixelFrame className="p-6 md:p-8 space-y-8 border border-[#383838]">
              {/* Specimen Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-[#292929]">
                <div className="space-y-2">
                  <span className="text-[11px] font-mono text-[#666666] uppercase tracking-wider">
                    TARGET SPECIMEN // DEMONSTRATION RECORD
                  </span>
                  <h4 className="text-lg md:text-xl font-mono font-medium text-[#F5F5F5]">
                    https://example-corporate-domain.com
                  </h4>
                  <p className="text-xs text-[#A1A1A1] font-mono">
                    STATUS: AUDIT COMPLETE • COVERAGE: 100% (4 OF 4 MODULES)
                  </p>
                </div>

                <div className="flex items-center space-x-6 bg-[#101010] border border-[#292929] px-6 py-4">
                  <div className="text-center">
                    <span className="text-3xl sm:text-4xl font-mono font-bold text-[#F5F5F5]">
                      88
                    </span>
                    <span className="text-xs font-mono text-[#666666] block">/ 100</span>
                  </div>
                  <div className="border-l border-[#292929] pl-6 space-y-1">
                    <Badge variant="safe" dot pulse>
                      LOW RISK
                    </Badge>
                    <span className="text-xs font-mono text-[#A1A1A1] block">BENIGN SPECIMEN</span>
                  </div>
                </div>
              </div>

              {/* 4 Signals Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
                <div className="p-4 bg-[#101010] border border-[#292929] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[#666666]">LEXICAL ANALYSIS</span>
                    <span className="text-[#4ADE80]">CLEAN</span>
                  </div>
                  <p className="text-[#F5F5F5] font-semibold">100 / 100</p>
                  <p className="text-[11px] text-[#A1A1A1]">0 suspicious keyword indicators.</p>
                </div>

                <div className="p-4 bg-[#101010] border border-[#292929] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[#666666]">THREAT FEEDS</span>
                    <span className="text-[#4ADE80]">0 DETECTIONS</span>
                  </div>
                  <p className="text-[#F5F5F5] font-semibold">100 / 100</p>
                  <p className="text-[11px] text-[#A1A1A1]">72 vendor engines clean.</p>
                </div>

                <div className="p-4 bg-[#101010] border border-[#292929] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[#666666]">ML INFERENCE</span>
                    <span className="text-[#4ADE80]">BENIGN</span>
                  </div>
                  <p className="text-[#F5F5F5] font-semibold">99.2% CONFIDENCE</p>
                  <p className="text-[11px] text-[#A1A1A1]">Model rf-v1.0.0 classification.</p>
                </div>

                <div className="p-4 bg-[#101010] border border-[#292929] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[#666666]">SSL/TLS AUDIT</span>
                    <span className="text-[#4ADE80]">VALID TLS 1.3</span>
                  </div>
                  <p className="text-[#F5F5F5] font-semibold">100 / 100</p>
                  <p className="text-[11px] text-[#A1A1A1]">120 days remaining, CA trusted.</p>
                </div>
              </div>

              {/* Explanations & Recommendations Box */}
              <div className="p-4 bg-[#101010] border-l-2 border-l-[#F5F5F5] border-y border-r border-[#292929] space-y-2 text-xs">
                <span className="font-mono text-[#F5F5F5] font-semibold uppercase tracking-wider block">
                  SYSTEM RECOMMENDATIONS & EXPLANATION
                </span>
                <p className="text-[#A1A1A1] font-sans leading-relaxed">
                  The target demonstrates valid cryptographic certificates, zero vendor threat flags,
                  and a benign structural profile. No credential harvesting or malware vectors were
                  identified.
                </p>
              </div>
            </Card>
          </div>
        </Container>
      </section>

      {/* =========================================================================
          6. PRIVACY AND TRANSPARENCY SECTION
          ========================================================================= */}
      <section className="relative">
        <Container size="xl">
          <Card variant="panel" className="p-8 md:p-12 space-y-6 border border-[#292929]">
            <div className="max-w-3xl space-y-4">
              <span className="text-xs font-mono text-[#666666] uppercase tracking-widest">
                TRANSPARENCY & ETHICAL COMMITMENT
              </span>
              <h2 className="text-2xl sm:text-3xl font-light text-[#F5F5F5] tracking-tight">
                Explainable intelligence without opaque assumptions.
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 text-xs font-sans text-[#A1A1A1] leading-relaxed">
                <div className="space-y-2">
                  <h4 className="font-mono text-sm text-[#F5F5F5] font-medium uppercase">
                    Multiple Security Signals
                  </h4>
                  <p>
                    We never rely on a single data point. Lexical patterns, third-party vendor
                    consensus, cryptographic certificates, and trained models are combined into an
                    evidence-backed composite score.
                  </p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-mono text-sm text-[#F5F5F5] font-medium uppercase">
                    Auditable Coverage
                  </h4>
                  <p>
                    If an external intelligence feed is temporarily offline or rate-limited,
                    TrustGuard AI marks it as unavailable and normalizes weights across remaining
                    active checks rather than inventing false data.
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </Container>
      </section>

      {/* =========================================================================
          7. COMMUNITY SECTION
          ========================================================================= */}
      <section className="relative">
        <Container size="xl">
          <Card variant="elevated" pixelFrame className="p-8 md:p-12 space-y-6 border border-[#383838]">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              <div className="space-y-3 max-w-xl">
                <div className="flex items-center space-x-2 text-xs font-mono text-[#666666]">
                  <Users className="w-4 h-4 text-[#F5F5F5]" />
                  <span>COLLABORATIVE DEFENSE</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-light text-[#F5F5F5] tracking-tight">
                  Security is stronger when knowledge is shared.
                </h2>
                <p className="text-xs sm:text-sm text-[#A1A1A1] leading-relaxed">
                  Encountered an active phishing page or fraudulent impersonation? Submit threat
                  reports to protect the wider web community with strict submitter privacy.
                </p>
              </div>

              <div className="shrink-0 flex flex-col sm:flex-row items-stretch gap-3">
                <Link to="/community">
                  <Button size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
                    EXPLORE COMMUNITY THREATS
                  </Button>
                </Link>
              </div>
            </div>
          </Card>
        </Container>
      </section>
    </div>
  );
};
