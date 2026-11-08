import React, { useState } from 'react';
import {
  Shield,
  Search,
  Lock,
  AlertTriangle,
  Terminal,
  ExternalLink,
} from 'lucide-react';
import {
  Button,
  Input,
  Card,
  Container,
  Badge,
  StatusIndicator,
  Tooltip,
  Divider,
  Modal,
  Dropdown,
  Tabs,
  Skeleton,
} from '../components/common';

export const DesignSystemShowcasePage: React.FC = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('palette');
  const [demoInput, setDemoInput] = useState('');

  return (
    <div className="flex-1 py-12 md:py-20 space-y-16">
      <Container size="xl">
        {/* Showcase Header */}
        <div className="space-y-4 pb-8 border-b border-[#292929]">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 bg-[#141414] border border-[#292929] text-xs font-mono text-[#A1A1A1]">
            <span className="w-1.5 h-1.5 bg-[#F5F5F5] rounded-full" />
            <span>DESIGN SYSTEM SPECIFICATION // V1.0.0</span>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-5xl font-light tracking-tight text-[#F5F5F5]">
            Premium Monochromatic Digital Minimalism
          </h1>

          <p className="text-sm sm:text-base text-[#A1A1A1] max-w-3xl font-sans">
            Understated authority, cryptographic precision, and mathematical restraint. The
            visual language eliminates decorative noise in favor of pure monochromatic contrast and
            purposeful security telemetry.
          </p>

          <Tabs
            tabs={[
              { id: 'palette', label: '01 // COLOUR & STATUS' },
              { id: 'typography', label: '02 // TYPOGRAPHY' },
              { id: 'components', label: '03 // CORE COMPONENTS' },
              { id: 'surfaces', label: '04 // SURFACES & OVERLAYS' },
            ]}
            activeTab={activeTab}
            onChange={setActiveTab}
          />
        </div>

        {/* TAB 1: COLOUR & STATUS TOKENS */}
        {activeTab === 'palette' && (
          <div className="space-y-12">
            <div className="space-y-4">
              <h2 className="text-lg font-mono uppercase tracking-wider text-[#F5F5F5]">
                PRIMARY MONOCHROMATIC PALETTE
              </h2>
              <p className="text-xs text-[#A1A1A1]">
                High-contrast luminance hierarchy replacing arbitrary colorful accents.
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8 gap-3">
                {[
                  { name: 'CANVAS BG', hex: '#080808', border: '#292929' },
                  { name: 'SECONDARY', hex: '#101010', border: '#292929' },
                  { name: 'SURFACE', hex: '#141414', border: '#292929' },
                  { name: 'ELEVATED', hex: '#181818', border: '#383838' },
                  { name: 'BORDER SUBTLE', hex: '#292929', border: '#383838' },
                  { name: 'BORDER STRONG', hex: '#383838', border: '#525252' },
                  { name: 'TEXT MUTED', hex: '#666666', border: '#383838' },
                  { name: 'TEXT PRIMARY', hex: '#F5F5F5', border: '#F5F5F5' },
                ].map((color) => (
                  <div
                    key={color.name}
                    className="p-3 bg-[#101010] border border-[#292929] space-y-3"
                  >
                    <div
                      className="w-full h-12 border"
                      style={{ backgroundColor: color.hex, borderColor: color.border }}
                    />
                    <div className="space-y-0.5 font-mono">
                      <p className="text-[11px] text-[#F5F5F5] font-semibold">{color.name}</p>
                      <p className="text-[10px] text-[#666666]">{color.hex}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <h2 className="text-lg font-mono uppercase tracking-wider text-[#F5F5F5]">
                SECURITY STATUS TOKENS (RESTRAINED)
              </h2>
              <p className="text-xs text-[#A1A1A1]">
                Employed strictly when communicating risk, verification verdicts, or critical alerts.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="space-y-3">
                  <div className="flex items-center justify-between">
                    <StatusIndicator status="safe" pulse />
                    <Badge variant="safe">SAFE</Badge>
                  </div>
                  <p className="text-xs text-[#A1A1A1]">
                    Restrained green for confirmed benign domains and valid SSL chains.
                  </p>
                  <p className="text-[10px] font-mono text-[#666666]">#4ADE80 • #052E16</p>
                </Card>

                <Card className="space-y-3">
                  <div className="flex items-center justify-between">
                    <StatusIndicator status="suspicious" />
                    <Badge variant="suspicious">SUSPICIOUS</Badge>
                  </div>
                  <p className="text-xs text-[#A1A1A1]">
                    Restrained amber for unusual entropy, redirect loops, or expiring certs.
                  </p>
                  <p className="text-[10px] font-mono text-[#666666]">#FBBF24 • #451A03</p>
                </Card>

                <Card className="space-y-3">
                  <div className="flex items-center justify-between">
                    <StatusIndicator status="malicious" pulse />
                    <Badge variant="malicious">MALICIOUS</Badge>
                  </div>
                  <p className="text-xs text-[#A1A1A1]">
                    Restrained red for confirmed phishing, malware, or critical VT hits.
                  </p>
                  <p className="text-[10px] font-mono text-[#666666]">#F87171 • #450A0A</p>
                </Card>

                <Card className="space-y-3">
                  <div className="flex items-center justify-between">
                    <StatusIndicator status="unknown" />
                    <Badge variant="unknown">UNKNOWN</Badge>
                  </div>
                  <p className="text-xs text-[#A1A1A1]">
                    Neutral tone for unresolvable hostnames or offline external feeds.
                  </p>
                  <p className="text-[10px] font-mono text-[#666666]">#A1A1A1 • #141414</p>
                </Card>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: TYPOGRAPHY SCALE */}
        {activeTab === 'typography' && (
          <div className="space-y-8">
            <div className="space-y-2">
              <h2 className="text-lg font-mono uppercase tracking-wider text-[#F5F5F5]">
                GEIST SANS & GEIST MONO HIERARCHY
              </h2>
              <p className="text-xs text-[#A1A1A1]">
                Pairing modern sans for editorial clarity with cryptographic monospace for data.
              </p>
            </div>

            <Card className="divide-y divide-[#292929] p-0 overflow-hidden">
              <div className="p-6 space-y-1">
                <span className="type-label">TYPE-HERO // 48PX - 64PX LIGHT</span>
                <p className="type-hero">Autonomous Threat Assessment.</p>
              </div>

              <div className="p-6 space-y-1">
                <span className="type-label">TYPE-H1 // 32PX - 40PX LIGHT</span>
                <p className="type-h1">Cryptographic Clarity for the Modern Web</p>
              </div>

              <div className="p-6 space-y-1">
                <span className="type-label">TYPE-H2 // 24PX - 28PX REGULAR</span>
                <p className="type-h2">Multi-Engine VirusTotal Consensus & Machine Learning</p>
              </div>

              <div className="p-6 space-y-1">
                <span className="type-label">TYPE-H3 // 18PX MEDIUM</span>
                <p className="type-h3">Digital Trust Score Synthesis & Override Engine</p>
              </div>

              <div className="p-6 space-y-1">
                <span className="type-label">TYPE-BODY // 14PX REGULAR</span>
                <p className="type-body max-w-2xl">
                  TrustGuard AI inspects target URLs across four concurrent security layers. Each
                  layer evaluates empirical evidence against known threat models without false
                  positives or artificial scoring inflations.
                </p>
              </div>

              <div className="p-6 space-y-1">
                <span className="type-label">TYPE-MONO-METRIC // 36PX - 44PX SEMIBOLD</span>
                <p className="type-mono-metric">88.4 / 100</p>
              </div>

              <div className="p-6 space-y-1">
                <span className="type-label">TYPE-MONO-CODE // 12PX REGULAR</span>
                <p className="type-mono-code">
                  SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                </p>
              </div>
            </Card>
          </div>
        )}

        {/* TAB 3: CORE COMPONENTS */}
        {activeTab === 'components' && (
          <div className="space-y-12">
            {/* Buttons Section */}
            <div className="space-y-4">
              <h2 className="text-lg font-mono uppercase tracking-wider text-[#F5F5F5]">
                BUTTON VARIANTS & STATES
              </h2>

              <div className="flex flex-wrap items-center gap-3">
                <Button variant="primary">PRIMARY ACTION</Button>
                <Button variant="secondary">SECONDARY ACTION</Button>
                <Button variant="outline">OUTLINE BORDER</Button>
                <Button variant="ghost">GHOST BUTTON</Button>
                <Button variant="danger">CRITICAL ACTION</Button>
                <Button variant="primary" isLoading>
                  LOADING
                </Button>
                <Button variant="secondary" disabled>
                  DISABLED
                </Button>
                <Button variant="primary" pixelCorners>
                  PIXEL CORNERS
                </Button>
                <Button size="icon" variant="secondary" aria-label="Shield">
                  <Shield className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <Divider label="INPUT FIELD PRIMITIVES" />

            {/* Inputs Section */}
            <div className="space-y-4">
              <h2 className="text-lg font-mono uppercase tracking-wider text-[#F5F5F5]">
                INPUT CONTROLS & VALIDATION
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Input
                  label="URL INPUT (MONOSPACED)"
                  placeholder="https://target-domain.com/login"
                  value={demoInput}
                  onChange={(e) => setDemoInput(e.target.value)}
                  leftElement={<Search className="w-4 h-4" />}
                  mono
                  hint="Supports standard HTTP and HTTPS schemes with SSRF guard."
                />

                <Input
                  label="PASSWORD INPUT WITH REVEAL"
                  type="password"
                  defaultValue="SecretToken123!"
                  leftElement={<Lock className="w-4 h-4" />}
                  hint="Click the eye icon to toggle visibility."
                />

                <Input
                  label="VALIDATION ERROR STATE"
                  defaultValue="ftp://unsupported-scheme.com"
                  error="INVALID_URL: Scheme 'ftp' is not permitted. Only HTTP/HTTPS supported."
                  leftElement={<AlertTriangle className="w-4 h-4" />}
                />

                <Input
                  label="DISABLED STATE"
                  defaultValue="readonly@trustguard.ai"
                  disabled
                  leftElement={<Lock className="w-4 h-4" />}
                  hint="Field is locked against user modification."
                />
              </div>
            </div>

            <Divider label="BADGES & PILLS" />

            {/* Badges Section */}
            <div className="space-y-4">
              <h2 className="text-lg font-mono uppercase tracking-wider text-[#F5F5F5]">
                BADGES & STATUS LABELS
              </h2>

              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="default">DEFAULT BADGE</Badge>
                <Badge variant="inverted">INVERTED BADGE</Badge>
                <Badge variant="outline">OUTLINE PILL</Badge>
                <Badge variant="subtle">SUBTLE LABEL</Badge>
                <Badge variant="safe" dot pulse>
                  TLS 1.3 VALID
                </Badge>
                <Badge variant="suspicious" dot>
                  HEURISTIC FLAG
                </Badge>
                <Badge variant="malicious" dot pulse>
                  PHISHING 98%
                </Badge>
                <Badge variant="unknown" dot>
                  VT OFFLINE
                </Badge>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: SURFACES, CARDS & OVERLAYS */}
        {activeTab === 'surfaces' && (
          <div className="space-y-12">
            <div className="space-y-4">
              <h2 className="text-lg font-mono uppercase tracking-wider text-[#F5F5F5]">
                SURFACES & CARD VARIANTS
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card variant="standard" title="STANDARD SURFACE" subtitle="#141414 / #292929">
                  <p className="text-xs text-[#A1A1A1]">
                    Default background for content modules, tables, and settings forms.
                  </p>
                </Card>

                <Card variant="elevated" title="ELEVATED SURFACE" subtitle="#181818 / #383838">
                  <p className="text-xs text-[#A1A1A1]">
                    Higher contrast and subtle shadow for featured cards and metrics.
                  </p>
                </Card>

                <Card variant="panel" title="PANEL SURFACE" subtitle="#101010 / #292929">
                  <p className="text-xs text-[#A1A1A1]">
                    Recessed canvas used for code outputs, metadata boxes, and lists.
                  </p>
                </Card>

                <Card variant="info" title="INFORMATION CARD" subtitle="Accent Left Border">
                  <p className="text-xs text-[#A1A1A1]">
                    Highlighting key findings, recommendations, or operational tips.
                  </p>
                </Card>
              </div>
            </div>

            <div className="space-y-4">
              <h2 className="text-lg font-mono uppercase tracking-wider text-[#F5F5F5]">
                INTERACTIVE OVERLAYS & TOOLTIPS
              </h2>

              <div className="flex flex-wrap items-center gap-4">
                <Button onClick={() => setModalOpen(true)}>OPEN ACCESSIBLE MODAL</Button>

                <Tooltip content="Cryptographic hash of the target URL">
                  <Button variant="secondary">HOVER FOR TOOLTIP</Button>
                </Tooltip>

                <Dropdown
                  label="EXPORT FORMAT"
                  items={[
                    { id: '1', label: 'EXPORT AS JSON', icon: <Terminal className="w-3.5 h-3.5" /> },
                    { id: '2', label: 'EXPORT AS CSV', icon: <ExternalLink className="w-3.5 h-3.5" /> },
                    { id: '3', label: 'DELETE SCAN RECORD', destructive: true },
                  ]}
                />
              </div>
            </div>

            <div className="space-y-4">
              <h2 className="text-lg font-mono uppercase tracking-wider text-[#F5F5F5]">
                GEOMETRIC SKELETON LOADERS
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-[#141414] border border-[#292929] space-y-3">
                  <Skeleton variant="text" width="60%" />
                  <Skeleton variant="text" width="90%" />
                  <Skeleton variant="text" width="40%" />
                </div>
                <div className="p-4 bg-[#141414] border border-[#292929] flex items-center space-x-4">
                  <Skeleton variant="circle" />
                  <div className="flex-1 space-y-2">
                    <Skeleton variant="text" width="70%" />
                    <Skeleton variant="text" width="40%" />
                  </div>
                </div>
                <Skeleton variant="card" />
              </div>
            </div>
          </div>
        )}

        {/* Modal Demonstration */}
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="ACCESSIBLE DIALOGUE DEMO"
          subtitle="KEYBOARD ESCAPE & FOCUS TRAP VERIFIED"
          footerActions={
            <>
              <Button variant="secondary" onClick={() => setModalOpen(false)}>
                DISMISS
              </Button>
              <Button onClick={() => setModalOpen(false)}>CONFIRM ACTION</Button>
            </>
          }
        >
          <p className="text-sm text-[#A1A1A1] leading-relaxed">
            This modal complies with WCAG accessibility guidelines: it traps focus, restores body
            scroll on unmount, responds to the Escape key, and features razor-sharp monochromatic
            pixel corner marks.
          </p>
        </Modal>
      </Container>
    </div>
  );
};
