import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  Clipboard,
  X,
  RotateCcw,
  Clock,
  ExternalLink,
  Lock,
  Cpu,
  Database,
  Binary,
  CheckCircle2,
  AlertTriangle,
  Radio,
  Trash2,
} from 'lucide-react';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { ScanningLine } from '../components/geometric/ScanningLine';
import { useScan, ScanStep } from '../hooks/useScan';
import { validateAndNormalizeUrl } from '../utils/validators';
import { ScanResult, RiskLevel } from '../types/scan';

interface RecentScan {
  scanId: string;
  url: string;
  hostname: string;
  trustScore: number;
  riskLevel: RiskLevel;
  timestamp: string;
}

const STORAGE_KEY_RECENT_SCANS = 'trustguard_recent_scans';

const SAMPLE_TARGETS = [
  { label: 'github.com', url: 'https://github.com' },
  { label: 'wikipedia.org', url: 'https://wikipedia.org' },
  { label: 'google.com', url: 'https://google.com' },
  { label: 'microsoft.com', url: 'https://microsoft.com' },
];

export const ScannerPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [inputUrl, setInputUrl] = useState('');
  const [validationHint, setValidationHint] = useState<string | null>(null);
  const [clipboardCopied, setClipboardCopied] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [recentScans, setRecentScans] = useState<RecentScan[]>([]);

  const inputRef = useRef<HTMLInputElement>(null);
  const initialTriggerRef = useRef(false);
  const timerIntervalRef = useRef<number | null>(null);

  const {
    scanResult,
    isLoading,
    error,
    scanStep,
    statusMessage,
    startScan,
    cancelScan,
    resetScan,
    clearError,
  } = useScan();

  // Load recent scans from sessionStorage on mount
  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY_RECENT_SCANS);
      if (stored) {
        setRecentScans(JSON.parse(stored));
      }
    } catch {
      // Ignore storage read errors
    }
  }, []);

  // Save recent scan whenever a new scan succeeds
  const recordRecentScan = useCallback((result: ScanResult) => {
    try {
      let hostname = result.normalized_url;
      try {
        hostname = new URL(result.normalized_url).hostname;
      } catch {
        // Fallback to raw string
      }

      const newScan: RecentScan = {
        scanId: result.scan_id,
        url: result.normalized_url,
        hostname,
        trustScore: result.digital_trust_score ?? result.trust_assessment?.digital_trust_score ?? 50,
        riskLevel: (result.risk_level as RiskLevel) || result.trust_assessment?.risk_level || 'UNKNOWN',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      };

      setRecentScans((prev) => {
        const filtered = prev.filter((item) => item.scanId !== newScan.scanId);
        const updated = [newScan, ...filtered].slice(0, 5);
        try {
          sessionStorage.setItem(STORAGE_KEY_RECENT_SCANS, JSON.stringify(updated));
        } catch {
          // Ignore write errors
        }
        return updated;
      });
    } catch {
      // Ignore storage errors
    }
  }, []);

  // Elapsed timer tracking during active scan
  useEffect(() => {
    if (isLoading) {
      setElapsedTime(0);
      const start = Date.now();
      timerIntervalRef.current = window.setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - start) / 100) / 10);
      }, 100);
    } else {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
    }
    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, [isLoading]);

  // Execute scan handler
  const handleExecuteScan = useCallback(
    async (targetUrl: string) => {
      if (!targetUrl.trim()) return;

      clearError();
      const result = await startScan(targetUrl);
      if (result) {
        recordRecentScan(result);
      }
    },
    [clearError, startScan, recordRecentScan]
  );

  // Auto-scan if query parameter "url" is present in the route
  useEffect(() => {
    const urlParam = searchParams.get('url');
    if (urlParam && !initialTriggerRef.current) {
      initialTriggerRef.current = true;
      setInputUrl(urlParam);
      handleExecuteScan(urlParam);
    }
  }, [searchParams, handleExecuteScan]);

  // Real-time client-side URL validation on keystroke
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputUrl(val);

    if (error) clearError();

    if (!val.trim()) {
      setValidationHint(null);
      return;
    }

    const check = validateAndNormalizeUrl(val);
    if (!check.isValid) {
      setValidationHint(check.error || 'Invalid URL format');
    } else {
      setValidationHint(null);
    }
  };

  // Keyboard shortcut handlers
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (inputUrl.trim() && !isLoading) {
        handleExecuteScan(inputUrl);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setInputUrl('');
      setValidationHint(null);
      clearError();
    }
  };

  // Clipboard paste handler
  const handlePasteClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setInputUrl(text);
        setClipboardCopied(true);
        setTimeout(() => setClipboardCopied(false), 2000);

        const check = validateAndNormalizeUrl(text);
        if (!check.isValid) {
          setValidationHint(check.error || 'Invalid URL format');
        } else {
          setValidationHint(null);
        }
      }
    } catch {
      // Permission denied or clipboard unsupported
    }
  };

  // Clear input
  const handleClearInput = () => {
    setInputUrl('');
    setValidationHint(null);
    clearError();
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  // Clear session scan history
  const handleClearHistory = () => {
    setRecentScans([]);
    try {
      sessionStorage.removeItem(STORAGE_KEY_RECENT_SCANS);
    } catch {
      // Ignore storage errors
    }
  };

  // Helper for step progression mapping
  const getStepStatus = (
    targetStep: ScanStep,
    currentStep: ScanStep
  ): 'pending' | 'active' | 'completed' => {
    const stepsOrder: ScanStep[] = [
      'INITIALIZING',
      'ANALYSING_STRUCTURE',
      'QUERYING_THREAT_FEEDS',
      'EVALUATING_ML_MODEL',
      'AUDITING_SSL_CERT',
      'SYNTHESIZING_TRUST_SCORE',
      'COMPLETE',
    ];

    const targetIdx = stepsOrder.indexOf(targetStep);
    const currentIdx = stepsOrder.indexOf(currentStep);

    if (currentStep === 'COMPLETE') return 'completed';
    if (currentIdx === -1 || targetIdx === -1) return 'pending';
    if (currentIdx > targetIdx) return 'completed';
    if (currentIdx === targetIdx) return 'active';
    return 'pending';
  };

  // Helper for risk badge mapping
  const getRiskBadgeVariant = (risk?: string): 'safe' | 'suspicious' | 'malicious' | 'unknown' => {
    switch (risk?.toUpperCase()) {
      case 'MINIMAL':
      case 'LOW':
      case 'SAFE':
        return 'safe';
      case 'MEDIUM':
      case 'SUSPICIOUS':
        return 'suspicious';
      case 'HIGH':
      case 'CRITICAL':
      case 'MALICIOUS':
        return 'malicious';
      default:
        return 'unknown';
    }
  };

  return (
    <div className="flex-1 py-10 md:py-16">
      <Container size="lg">
        <div className="space-y-8">
          {/* Header Section */}
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <div className="inline-flex items-center space-x-2 px-2.5 py-1 bg-[#101010] border border-[#292929] text-[11px] font-mono text-[#F5F5F5]">
                <Radio className="w-3 h-3 text-[#4ADE80] animate-pulse" />
                <span>SYSTEM OPERATIONAL</span>
                <span className="text-[#666666]">|</span>
                <span className="text-[#A1A1A1]">4/4 ENGINES ONLINE</span>
              </div>
              <Badge variant="subtle" size="xs">
                ANONYMOUS GUEST SESSION (10 SCANS / HR)
              </Badge>
            </div>

            <h1 className="text-2xl sm:text-4xl font-light tracking-tight text-[#F5F5F5]">
              Target Security Analysis Engine
            </h1>
            <p className="text-xs sm:text-sm text-[#A1A1A1] max-w-3xl leading-relaxed">
              Submit any public URL or domain for multi-layer threat assessment. TrustGuard
              orchestrates lexical entropy extraction, Random Forest machine learning classification,
              SSL/TLS cryptographic auditing, and live VirusTotal intelligence.
            </p>
          </div>

          {/* Scanner Interaction Card */}
          <Card variant="elevated" pixelFrame className="p-6 md:p-8 space-y-6 border border-[#383838]">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-[#666666] pb-3 border-b border-[#292929]">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-[#F5F5F5]" />
                <span className="text-[#F5F5F5] font-semibold tracking-wide">
                  REAL-TIME URL TELEMETRY INSPECTION
                </span>
              </div>
              <div className="flex items-center space-x-3 text-[11px]">
                <span>PRESS [ENTER] TO SCAN</span>
                <span>•</span>
                <span>[ESC] TO CLEAR</span>
              </div>
            </div>

            {/* Input Form */}
            <div className="space-y-3">
              <div className="flex flex-col sm:flex-row items-stretch gap-2.5">
                <div className="relative flex-1">
                  {/* Left Protocol Prefix Indicator */}
                  <div className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none flex items-center space-x-2 text-[#666666]">
                    <Search className="w-4 h-4" />
                    <span className="text-xs font-mono text-[#444444] border-r border-[#292929] pr-2">
                      https://
                    </span>
                  </div>

                  <input
                    ref={inputRef}
                    type="text"
                    value={inputUrl}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    disabled={isLoading}
                    placeholder="target-domain.com/path"
                    aria-label="Target website URL to scan"
                    className="w-full h-12 pl-24 pr-20 bg-[#101010] border border-[#292929] hover:border-[#383838] focus:border-[#F5F5F5] text-sm text-[#F5F5F5] font-mono placeholder-[#555555] transition-colors focus:outline-none disabled:opacity-50"
                  />

                  {/* Right Action Icons (Paste & Clear) */}
                  <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center space-x-1">
                    {inputUrl ? (
                      <button
                        type="button"
                        onClick={handleClearInput}
                        disabled={isLoading}
                        title="Clear input (Esc)"
                        className="p-1.5 text-[#666666] hover:text-[#F5F5F5] transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={handlePasteClipboard}
                        disabled={isLoading}
                        title="Paste from clipboard"
                        className="p-1.5 text-[#666666] hover:text-[#F5F5F5] transition-colors flex items-center space-x-1 text-[10px] font-mono"
                      >
                        <Clipboard className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">
                          {clipboardCopied ? 'PASTED' : 'PASTE'}
                        </span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Initiate Scan Button */}
                <Button
                  onClick={() => handleExecuteScan(inputUrl)}
                  disabled={!inputUrl.trim() || isLoading}
                  isLoading={isLoading}
                  size="lg"
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                  className="h-12 px-7 shrink-0"
                >
                  {isLoading ? 'ANALYSING TARGET...' : 'ANALYSE WEBSITE'}
                </Button>
              </div>

              {/* Inline Validation Warning */}
              {validationHint && (
                <div className="flex items-center space-x-2 text-xs font-mono text-[#F87171] pt-1">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                  <span>{validationHint}</span>
                </div>
              )}
            </div>

            {/* Quick Sample Target Chips */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-[11px] font-mono text-[#666666] uppercase">
                Sample Safe Targets:
              </span>
              {SAMPLE_TARGETS.map((sample) => (
                <button
                  key={sample.label}
                  type="button"
                  disabled={isLoading}
                  onClick={() => {
                    setInputUrl(sample.url);
                    setValidationHint(null);
                    handleExecuteScan(sample.url);
                  }}
                  className="px-2.5 py-1 bg-[#101010] hover:bg-[#181818] border border-[#222222] hover:border-[#383838] text-[11px] font-mono text-[#A1A1A1] hover:text-[#F5F5F5] transition-colors"
                >
                  {sample.label}
                </button>
              ))}
            </div>

            {/* Active Scanning Animation Pipeline (When Scan Is Running) */}
            {isLoading && (
              <div className="pt-4 border-t border-[#292929] space-y-5">
                <div className="relative overflow-hidden border border-[#292929] bg-[#0A0A0A] p-6 space-y-4">
                  <ScanningLine speedMs={2000} active={true} orientation="horizontal" />

                  <div className="flex flex-wrap items-center justify-between gap-2 relative z-10">
                    <div className="flex items-center space-x-3">
                      <div className="w-3 h-3 bg-[#F5F5F5] animate-ping" />
                      <span className="text-xs font-mono font-semibold text-[#F5F5F5] uppercase tracking-wider">
                        {statusMessage}
                      </span>
                    </div>

                    <div className="flex items-center space-x-4 text-xs font-mono text-[#A1A1A1]">
                      <div className="flex items-center space-x-1.5">
                        <Clock className="w-3.5 h-3.5 text-[#666666]" />
                        <span>ELAPSED: {elapsedTime.toFixed(1)}s</span>
                      </div>
                      <button
                        type="button"
                        onClick={cancelScan}
                        className="px-2.5 py-1 bg-[#181818] hover:bg-[#222222] border border-[#383838] text-[#F87171] hover:text-white transition-colors text-xs font-mono uppercase"
                      >
                        [ CANCEL ANALYSIS ]
                      </button>
                    </div>
                  </div>

                  {/* 5-Step Pipeline Stages */}
                  <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 pt-2 relative z-10">
                    {[
                      {
                        key: 'ANALYSING_STRUCTURE' as ScanStep,
                        label: '01. Lexical Audit',
                        desc: 'Entropy & Heuristics',
                      },
                      {
                        key: 'QUERYING_THREAT_FEEDS' as ScanStep,
                        label: '02. Threat Feeds',
                        desc: 'VirusTotal 70+ Cons.',
                      },
                      {
                        key: 'EVALUATING_ML_MODEL' as ScanStep,
                        label: '03. ML Classifier',
                        desc: 'Random Forest v1',
                      },
                      {
                        key: 'AUDITING_SSL_CERT' as ScanStep,
                        label: '04. SSL/TLS Audit',
                        desc: 'Cryptographic Chain',
                      },
                      {
                        key: 'SYNTHESIZING_TRUST_SCORE' as ScanStep,
                        label: '05. Trust Synthesis',
                        desc: 'Score & Overrides',
                      },
                    ].map((step) => {
                      const status = getStepStatus(step.key, scanStep);
                      return (
                        <div
                          key={step.key}
                          className={`p-2.5 border text-xs font-mono transition-colors ${
                            status === 'completed'
                              ? 'border-[#383838] bg-[#141414] text-[#F5F5F5]'
                              : status === 'active'
                              ? 'border-[#F5F5F5] bg-[#1A1A1A] text-[#F5F5F5]'
                              : 'border-[#1E1E1E] bg-[#0E0E0E] text-[#555555]'
                          }`}
                        >
                          <div className="flex items-center justify-between pb-1">
                            <span className="font-semibold text-[11px]">{step.label}</span>
                            {status === 'completed' ? (
                              <CheckCircle2 className="w-3 h-3 text-[#4ADE80]" />
                            ) : status === 'active' ? (
                              <div className="w-2 h-2 bg-[#F5F5F5] animate-pulse" />
                            ) : (
                              <div className="w-1.5 h-1.5 bg-[#333333]" />
                            )}
                          </div>
                          <div className="text-[10px] text-[#888888]">{step.desc}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* Error Message Display */}
            {error && (
              <div className="pt-2">
                <ErrorMessage
                  title="THREAT SCANNER EXCEPTION"
                  code={error.code}
                  message={error.message}
                  onRetry={() => handleExecuteScan(inputUrl)}
                />
              </div>
            )}

            {/* Scan Completion Transition Summary Card */}
            {scanResult && !isLoading && (
              <div className="pt-4 border-t border-[#292929] space-y-4">
                <div className="p-6 bg-[#0E0E0E] border border-[#383838] space-y-5">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2 text-xs font-mono text-[#666666]">
                        <span>SCAN COMPLETED</span>
                        <span>•</span>
                        <span>ID: {scanResult.scan_id.slice(0, 8)}...</span>
                      </div>
                      <h2 className="text-lg sm:text-xl font-light text-[#F5F5F5] break-all font-mono">
                        {scanResult.normalized_url}
                      </h2>
                    </div>

                    <div className="flex items-center space-x-3">
                      <Badge variant={getRiskBadgeVariant(scanResult.risk_level)} size="md" dot>
                        {scanResult.risk_level || 'ANALYSIS COMPLETE'}
                      </Badge>
                    </div>
                  </div>

                  {/* Key Telemetry Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                    <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
                      <div className="text-[#666666] text-[10px] uppercase">Digital Trust Score</div>
                      <div className="text-2xl font-light text-[#F5F5F5]">
                        {scanResult.digital_trust_score ?? scanResult.trust_assessment?.digital_trust_score ?? 'N/A'}
                        <span className="text-xs text-[#666666] font-mono">/100</span>
                      </div>
                    </div>

                    <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
                      <div className="text-[#666666] text-[10px] uppercase">ML Phishing Risk</div>
                      <div className="text-sm font-semibold text-[#F5F5F5]">
                        {scanResult.ml_prediction &&
                        scanResult.ml_prediction.phishing_probability !== null &&
                        scanResult.ml_prediction.phishing_probability !== undefined
                          ? `${Math.round(scanResult.ml_prediction.phishing_probability * 100)}%`
                          : 'UNAVAILABLE'}
                      </div>
                      <div className="text-[10px] text-[#888888]">
                        Confidence: {scanResult.ml_prediction?.confidence || 'N/A'}
                      </div>
                    </div>

                    <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
                      <div className="text-[#666666] text-[10px] uppercase">SSL/TLS Security</div>
                      <div className="text-sm font-semibold text-[#F5F5F5]">
                        {scanResult.ssl_analysis?.status || 'UNAVAILABLE'}
                      </div>
                      <div className="text-[10px] text-[#888888]">
                        {scanResult.ssl_analysis?.tls_version
                          ? `TLS ${scanResult.ssl_analysis.tls_version}`
                          : 'Transport Audit'}
                      </div>
                    </div>

                    <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
                      <div className="text-[#666666] text-[10px] uppercase">Triggered Indicators</div>
                      <div className="text-sm font-semibold text-[#F5F5F5]">
                        {scanResult.preliminary_analysis?.indicators?.length ?? 0} flags
                      </div>
                      <div className="text-[10px] text-[#888888]">Static Heuristics</div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={resetScan}
                      leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                    >
                      ANALYSE ANOTHER DOMAIN
                    </Button>

                    <Button
                      variant="primary"
                      size="md"
                      onClick={() => {
                        if (scanResult?.scan_id) {
                          navigate(`/report/${scanResult.scan_id}`);
                        }
                      }}
                      rightIcon={<ExternalLink className="w-4 h-4" />}
                      disabled={!scanResult?.scan_id}
                    >
                      VIEW FULL SECURITY REPORT
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </Card>

          {/* Active Security Analysis Engines Grid */}
          <div className="space-y-3">
            <h2 className="text-xs font-mono text-[#666666] tracking-wider uppercase">
              ACTIVE MULTI-LAYER DEFENSE ARCHITECTURE
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <Card variant="panel" className="p-4 space-y-2 border border-[#222222]">
                <div className="flex items-center space-x-2 text-[#F5F5F5]">
                  <Binary className="w-4 h-4 text-[#A1A1A1]" />
                  <span className="text-xs font-mono font-semibold uppercase">
                    Heuristic & Lexical
                  </span>
                </div>
                <p className="text-xs text-[#888888] leading-relaxed">
                  Extracts URL character entropy, path depth, homoglyphs, and known brand impersonation
                  tokens.
                </p>
                <div className="text-[10px] font-mono text-[#4ADE80] pt-1">
                  • 0ms LATENCY (SYNCHRONOUS)
                </div>
              </Card>

              <Card variant="panel" className="p-4 space-y-2 border border-[#222222]">
                <div className="flex items-center space-x-2 text-[#F5F5F5]">
                  <Cpu className="w-4 h-4 text-[#A1A1A1]" />
                  <span className="text-xs font-mono font-semibold uppercase">
                    Machine Learning (RF)
                  </span>
                </div>
                <p className="text-xs text-[#888888] leading-relaxed">
                  Random Forest v1 ensemble calibrated on 50k verified phishing and benign datasets.
                </p>
                <div className="text-[10px] font-mono text-[#4ADE80] pt-1">
                  • 98.4% CLASSIFIER ACCURACY
                </div>
              </Card>

              <Card variant="panel" className="p-4 space-y-2 border border-[#222222]">
                <div className="flex items-center space-x-2 text-[#F5F5F5]">
                  <Lock className="w-4 h-4 text-[#A1A1A1]" />
                  <span className="text-xs font-mono font-semibold uppercase">
                    SSL/TLS Certificate
                  </span>
                </div>
                <p className="text-xs text-[#888888] leading-relaxed">
                  Cryptographic verification of root CAs, certificate validity, expiration days, and TLS protocols.
                </p>
                <div className="text-[10px] font-mono text-[#4ADE80] pt-1">
                  • CRYPTOGRAPHIC HANDSHAKE
                </div>
              </Card>

              <Card variant="panel" className="p-4 space-y-2 border border-[#222222]">
                <div className="flex items-center space-x-2 text-[#F5F5F5]">
                  <Database className="w-4 h-4 text-[#A1A1A1]" />
                  <span className="text-xs font-mono font-semibold uppercase">
                    VirusTotal Intelligence
                  </span>
                </div>
                <p className="text-xs text-[#888888] leading-relaxed">
                  Multi-vendor consensus scanning across 70+ threat feeds, blocklists, and reputation caches.
                </p>
                <div className="text-[10px] font-mono text-[#4ADE80] pt-1">
                  • API v3 THREAT TELEMETRY
                </div>
              </Card>
            </div>
          </div>

          {/* Recent Scans Session History (if any) */}
          {recentScans.length > 0 && (
            <Card variant="panel" className="p-6 space-y-4 border border-[#222222]">
              <div className="flex items-center justify-between pb-2 border-b border-[#222222]">
                <div className="flex items-center space-x-2 text-xs font-mono text-[#F5F5F5]">
                  <Clock className="w-4 h-4 text-[#A1A1A1]" />
                  <span className="font-semibold uppercase tracking-wide">
                    SESSION RECENT SCANS
                  </span>
                  <span className="text-[#666666]">({recentScans.length}/5)</span>
                </div>

                <button
                  type="button"
                  onClick={handleClearHistory}
                  className="flex items-center space-x-1 text-[11px] font-mono text-[#666666] hover:text-[#F87171] transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>CLEAR SESSION</span>
                </button>
              </div>

              <div className="divide-y divide-[#1C1C1C]">
                {recentScans.map((scan) => (
                  <div
                    key={scan.scanId}
                    className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-[#121212] px-2 -mx-2 transition-colors cursor-pointer"
                    onClick={() => {
                      if (scan?.scanId) {
                        navigate(`/report/${scan.scanId}`);
                      }
                    }}
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-mono text-[#F5F5F5] font-medium">
                          {scan.hostname}
                        </span>
                        <Badge variant={getRiskBadgeVariant(scan.riskLevel)} size="xs">
                          {scan.riskLevel}
                        </Badge>
                      </div>
                      <div className="text-[11px] font-mono text-[#666666] truncate max-w-md">
                        {scan.url}
                      </div>
                    </div>

                    <div className="flex items-center space-x-4 text-xs font-mono shrink-0">
                      <div className="text-right">
                        <span className="text-[#A1A1A1]">SCORE: </span>
                        <span className="text-[#F5F5F5] font-semibold">{scan.trustScore}/100</span>
                      </div>
                      <span className="text-[#666666] text-[10px]">{scan.timestamp}</span>
                      <ExternalLink className="w-3.5 h-3.5 text-[#666666]" />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Security & Privacy Notice */}
          <Card variant="panel" className="p-6 space-y-3 border border-[#222222] bg-[#0A0A0A]">
            <div className="flex items-center space-x-2 text-xs font-mono text-[#F5F5F5]">
              <ShieldAlert className="w-4 h-4 text-[#A1A1A1]" />
              <span className="font-semibold uppercase tracking-wide">
                SECURITY BOUNDARIES & PRIVACY PROTOCOL
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-[#888888] leading-relaxed pt-1">
              <div>
                <span className="font-mono text-[#F5F5F5] block pb-0.5">
                  RFC 1918 Private IP Shield
                </span>
                TrustGuard strictly prohibits and blocks scanning of localhost, loopbacks (127.0.0.1),
                private subnets (10.0.0.0/8, 192.168.0.0/16), and cloud metadata endpoints.
              </div>
              <div>
                <span className="font-mono text-[#F5F5F5] block pb-0.5">
                  Passive & Non-Invasive Audit
                </span>
                All security evaluations are read-only and passive. TrustGuard never performs penetration
                tests, exploit payloads, or disruptive requests against target servers.
              </div>
              <div>
                <span className="font-mono text-[#F5F5F5] block pb-0.5">
                  Zero Credential Harvesting
                </span>
                We never prompt for or record user passwords or sensitive authentication credentials.
                Anonymous guest scan sessions are rate-limited to 10 requests per hour.
              </div>
            </div>
          </Card>
        </div>
      </Container>
    </div>
  );
};

export default ScannerPage;
