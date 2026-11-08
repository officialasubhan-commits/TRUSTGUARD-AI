import React, { useState } from 'react';
import {
  RotateCcw,
  Sparkles,
  MousePointer,
  Scan,
  Grid,
  Layers,
} from 'lucide-react';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Tabs } from '../components/common/Tabs';
import {
  PixelGrid,
  GeometricPixelField,
  InteractivePixelGrid,
  GeometricFormation,
  ScanningLine,
  PixelReveal,
  GeometricTransition,
} from '../components/geometric';
import type { FormationPattern } from '../components/geometric';

export const AnimationShowcasePage: React.FC = () => {
  const [activeSection, setActiveSection] = useState('all');
  const [formationPattern, setFormationPattern] = useState<FormationPattern>('cycle');
  const [revealKey, setRevealKey] = useState(0);

  return (
    <div className="flex-1 py-12 md:py-20 space-y-16">
      <Container size="xl">
        {/* Showcase Header */}
        <div className="space-y-4 pb-8 border-b border-[#292929]">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 bg-[#141414] border border-[#292929] text-xs font-mono text-[#A1A1A1]">
            <Sparkles className="w-3.5 h-3.5 text-[#F5F5F5]" />
            <span>GENERATIVE MOTION & INTERACTION ENGINE // PROMPT 04</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-light tracking-tight text-[#F5F5F5]">
            Geometric Pixel Animation Engine
          </h1>

          <p className="text-sm sm:text-base text-[#A1A1A1] max-w-3xl font-sans leading-relaxed">
            Mathematically structured, 60 FPS generative motion systems designed for digital trust
            intelligence. Monochromatic squares emerge, interact with the user&apos;s cursor, and morph
            between cryptographic geometries with zero WebGL bloat.
          </p>

          <Tabs
            tabs={[
              { id: 'all', label: 'ALL SYSTEMS' },
              { id: 'interactive', label: '01 // CURSOR INTERACTION' },
              { id: 'formation', label: '02 // FORMATION & MORPH' },
              { id: 'scanner', label: '03 // SCANNING BEAM' },
              { id: 'field', label: '04 // PIXEL FIELD & GRID' },
            ]}
            activeTab={activeSection}
            onChange={setActiveSection}
          />
        </div>

        {/* SECTION 1: CURSOR-RESPONSIVE INTERACTION */}
        {(activeSection === 'all' || activeSection === 'interactive') && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <div className="flex items-center space-x-2 text-xs font-mono text-[#666666]">
                  <MousePointer className="w-4 h-4 text-[#F5F5F5]" />
                  <span>SYSTEM 01 // INTERACTIVE GRAVITATIONAL FIELD</span>
                </div>
                <h2 className="text-xl font-mono text-[#F5F5F5]">Cursor-Responsive Pixel Grid</h2>
              </div>
              <span className="text-xs font-mono text-[#666666]">
                HOVER / MOVE CURSOR INSIDE CANVAS
              </span>
            </div>

            <Card className="p-0 overflow-hidden h-[340px] relative border border-[#383838]">
              <InteractivePixelGrid
                pixelSize={3}
                gap={24}
                interactionRadius={110}
                displacementStrength={7}
                baseOpacity={0.05}
                activeOpacity={0.65}
              >
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none p-6 text-center space-y-2">
                  <span className="text-[10px] font-mono tracking-widest text-[#666666] uppercase">
                    DYNAMIC DISTORTION ENGINE
                  </span>
                  <p className="text-sm sm:text-base font-mono text-[#F5F5F5] max-w-md">
                    Squares displace away from proximity radius while elevating luminance.
                  </p>
                </div>
              </InteractivePixelGrid>
            </Card>
          </div>
        )}

        {/* SECTION 2: GEOMETRIC FORMATION & DISSOLUTION */}
        {(activeSection === 'all' || activeSection === 'formation') && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2 text-xs font-mono text-[#666666]">
                  <Layers className="w-4 h-4 text-[#F5F5F5]" />
                  <span>SYSTEM 02 // MATHEMATICAL REASSEMBLY</span>
                </div>
                <h2 className="text-xl font-mono text-[#F5F5F5]">
                  Geometric Formation & Morphing
                </h2>
              </div>

              {/* Pattern Controller */}
              <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
                {(['shield', 'matrix', 'crosshair', 'horizon', 'cycle'] as FormationPattern[]).map(
                  (pat) => (
                    <button
                      key={pat}
                      onClick={() => setFormationPattern(pat)}
                      className={`px-3 py-1 uppercase tracking-wider border transition-colors ${
                        formationPattern === pat
                          ? 'bg-[#F5F5F5] text-[#080808] border-[#F5F5F5] font-semibold'
                          : 'bg-[#141414] text-[#A1A1A1] border-[#292929] hover:border-[#383838]'
                      }`}
                    >
                      {pat}
                    </button>
                  )
                )}
              </div>
            </div>

            <Card className="p-0 overflow-hidden h-[340px] relative border border-[#383838]">
              <GeometricFormation
                pattern={formationPattern}
                pixelCount={72}
                size={4}
                cycleInterval={3500}
              />
              <div className="absolute bottom-4 left-4 text-xs font-mono text-[#666666] tracking-wider pointer-events-none">
                ACTIVE PATTERN: [ {formationPattern.toUpperCase()} ]
              </div>
            </Card>
          </div>
        )}

        {/* SECTION 3: SCANNING-LINE ANIMATION */}
        {(activeSection === 'all' || activeSection === 'scanner') && (
          <div className="space-y-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-xs font-mono text-[#666666]">
                <Scan className="w-4 h-4 text-[#F5F5F5]" />
                <span>SYSTEM 03 // TELEMETRY RADAR</span>
              </div>
              <h2 className="text-xl font-mono text-[#F5F5F5]">Scanning-Line Beam Animation</h2>
              <p className="text-xs text-[#A1A1A1]">
                Sweeps across target analysis surfaces with trailing packet dissolution particles.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Horizontal Beam */}
              <Card className="p-0 overflow-hidden relative h-[220px]">
                <ScanningLine orientation="horizontal" speedMs={2000}>
                  <div className="p-6 h-full flex flex-col justify-between font-mono text-xs">
                    <div className="flex items-center justify-between text-[#666666]">
                      <span>HORIZONTAL PACKET TRAVERSAL</span>
                      <span className="text-[#F5F5F5] font-semibold">2000MS CYCLE</span>
                    </div>
                    <div className="space-y-1">
                      <p className="text-[#F5F5F5] font-medium">https://secure-chase-update.com</p>
                      <p className="text-[11px] text-[#A1A1A1]">
                        LEXICAL_CHECK // VT_FEED // SSL_HANDSHAKE
                      </p>
                    </div>
                  </div>
                </ScanningLine>
              </Card>

              {/* Vertical Beam */}
              <Card className="p-0 overflow-hidden relative h-[220px]">
                <ScanningLine orientation="vertical" speedMs={2400}>
                  <div className="p-6 h-full flex flex-col justify-between font-mono text-xs">
                    <div className="flex items-center justify-between text-[#666666]">
                      <span>VERTICAL RADAR SWEEP</span>
                      <span className="text-[#F5F5F5] font-semibold">2400MS CYCLE</span>
                    </div>
                    <div className="space-y-1">
                      <p className="text-[#F5F5F5] font-medium">CRYPTOGRAPHIC CERTIFICATE AUDIT</p>
                      <p className="text-[11px] text-[#A1A1A1]">
                        SHA-256 FINGERPRINT & CHAIN VALIDATION
                      </p>
                    </div>
                  </div>
                </ScanningLine>
              </Card>
            </div>
          </div>
        )}

        {/* SECTION 4: PIXEL FIELD & STATIC GRID */}
        {(activeSection === 'all' || activeSection === 'field') && (
          <div className="space-y-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-xs font-mono text-[#666666]">
                <Grid className="w-4 h-4 text-[#F5F5F5]" />
                <span>SYSTEM 04 // AMBIENT MATHEMATICAL GRID</span>
              </div>
              <h2 className="text-xl font-mono text-[#F5F5F5]">
                Geometric Pixel Field & Static Matrix
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Dynamic Pixel Field */}
              <Card className="p-0 overflow-hidden relative h-[240px]">
                <GeometricPixelField
                  pixelSize={3}
                  gap={18}
                  baseOpacity={0.03}
                  peakOpacity={0.25}
                  speed={0.012}
                />
                <div className="absolute bottom-3 left-3 text-[10px] font-mono text-[#666666]">
                  PERLIN SINE WAVE INTERFERENCE
                </div>
              </Card>

              {/* Static Pixel Grid */}
              <Card className="p-0 overflow-hidden relative h-[240px]">
                <PixelGrid gridSize={20} crosshairInterval={4} opacity={0.3} showCoordinates>
                  <div className="p-6 h-full flex flex-col justify-between font-mono text-xs">
                    <span className="text-[#666666]">COORDINATE RETICLE PATTERN</span>
                    <p className="text-[#A1A1A1]">
                      Precision 1px SVG matrix providing cryptographic spatial grounding.
                    </p>
                  </div>
                </PixelGrid>
              </Card>
            </div>
          </div>
        )}

        {/* SECTION 5: PIXEL REVEAL & TRANSITIONS */}
        {activeSection === 'all' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-xs font-mono text-[#666666]">
                  SYSTEM 05 // ENTRANCE ORCHESTRATION
                </span>
                <h2 className="text-xl font-mono text-[#F5F5F5]">Pixel Reveal Transitions</h2>
              </div>
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                onClick={() => setRevealKey((k) => k + 1)}
              >
                RE-TRIGGER ENTRANCE
              </Button>
            </div>

            <GeometricTransition key={revealKey} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <PixelReveal delay={0.05}>
                <Card variant="elevated" className="space-y-2">
                  <span className="text-xs font-mono text-[#666666]">STAGGER 01</span>
                  <h3 className="font-mono text-sm text-[#F5F5F5]">Lexical Analysis</h3>
                  <p className="text-xs text-[#A1A1A1]">Entropy and path depth evaluation.</p>
                </Card>
              </PixelReveal>

              <PixelReveal delay={0.15}>
                <Card variant="elevated" className="space-y-2">
                  <span className="text-xs font-mono text-[#666666]">STAGGER 02</span>
                  <h3 className="font-mono text-sm text-[#F5F5F5]">ML Phishing Classifier</h3>
                  <p className="text-xs text-[#A1A1A1]">Random Forest model v1 inference.</p>
                </Card>
              </PixelReveal>

              <PixelReveal delay={0.25}>
                <Card variant="elevated" className="space-y-2">
                  <span className="text-xs font-mono text-[#666666]">STAGGER 03</span>
                  <h3 className="font-mono text-sm text-[#F5F5F5]">Digital Trust Score</h3>
                  <p className="text-xs text-[#A1A1A1]">Evidence synthesis and overrides.</p>
                </Card>
              </PixelReveal>
            </GeometricTransition>
          </div>
        )}
      </Container>
    </div>
  );
};
