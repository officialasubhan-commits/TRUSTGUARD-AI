import React, { useState } from 'react';
import {
  Cpu,
  Database,
  Binary,
  Lock,
  Globe,
  ShieldCheck,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  HelpCircle,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { DetailedSecurityReport } from '../../types/scan';

interface SecurityEngineCardsProps {
  report: DetailedSecurityReport;
}

export const SecurityEngineCards: React.FC<SecurityEngineCardsProps> = ({ report }) => {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    ml: true,
    rep: true,
    vt: true,
    url: true,
    ssl: true,
  });

  const toggle = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const ml = report.ml_phishing_prediction;
  const rep = report.domain_reputation;
  const vt = report.virustotal_findings;
  const urlAnalysis = report.url_analysis;
  const ssl = report.ssl_tls_validation;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-1 border-b border-[#222222]">
        <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-[#A1A1A1]">
          SECURITY INSPECTION ENGINES (MULTI-LAYER INTELLIGENCE)
        </h2>
        <span className="text-[11px] font-mono text-[#666666]">
          EXPANDABLE MODULAR AUDIT TELEMETRY
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* ================================================================= */}
        {/* 1. MACHINE LEARNING DETECTION                                     */}
        {/* ================================================================= */}
        <Card variant="standard" className="p-5 space-y-4">
          <div
            className="flex items-start justify-between cursor-pointer select-none"
            onClick={() => toggle('ml')}
          >
            <div className="flex items-center space-x-2.5">
              <Cpu className="w-4 h-4 text-[#A1A1A1]" />
              <div>
                <h3 className="text-xs font-mono font-semibold uppercase text-[#F5F5F5]">
                  Machine Learning Detection
                </h3>
                <span className="text-[11px] font-mono text-[#666666]">
                  Model: {report.model_version || 'rf-v2.0.0'} (AI Threat Classifier)
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Badge
                variant={
                  ml?.prediction === 'PHISHING'
                    ? 'malicious'
                    : ml?.prediction === 'SUSPICIOUS'
                    ? 'suspicious'
                    : ml?.prediction === 'LIKELY_LEGITIMATE'
                    ? 'safe'
                    : 'unknown'
                }
                size="xs"
                dot
              >
                {ml?.prediction || 'UNAVAILABLE'}
              </Badge>
              {expanded.ml ? (
                <ChevronUp className="w-4 h-4 text-[#666666]" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[#666666]" />
              )}
            </div>
          </div>

          {expanded.ml && (
            <div className="space-y-3 pt-2 border-t border-[#222222] text-xs font-mono">
              {ml && ml.phishing_probability !== null && ml.phishing_probability !== undefined ? (
                <>
                  <div className="grid grid-cols-2 gap-2 bg-[#101010] p-3 border border-[#1F1F1F]">
                    <div>
                      <span className="text-[#666666] text-[10px] uppercase block">
                        Phishing Probability
                      </span>
                      <span
                        className={`text-lg font-bold ${
                          ml.phishing_probability >= 0.7
                            ? 'text-[#F87171]'
                            : ml.phishing_probability >= 0.3
                            ? 'text-[#FBBF24]'
                            : 'text-[#4ADE80]'
                        }`}
                      >
                        {(ml.phishing_probability * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div>
                      <span className="text-[#666666] text-[10px] uppercase block">
                        Engine Subscore
                      </span>
                      <span className="text-lg font-bold text-[#F5F5F5]">
                        {ml.ml_score !== null && ml.ml_score !== undefined ? `${ml.ml_score}/100` : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <p className="text-[#A1A1A1] text-[11px] leading-relaxed">
                    The Random Forest classifier evaluates structural URL entropy, token distribution,
                    and lexical deception vectors against 23 verified features. Phishing probability indicates
                    structural resemblance to confirmed attacks and is not an endorsement of overall domain safety.
                  </p>

                  {ml.features && (
                    <div className="p-2.5 bg-[#0D0D0D] border border-[#1A1A1A] text-[10px] space-y-1">
                      <span className="text-[#666666] uppercase block">
                        Evaluated Feature Vectors (23 Inputs)
                      </span>
                      <div className="flex flex-wrap gap-2 text-[#888888]">
                        <span>length: {ml.features.url_length ?? 'N/A'}</span>
                        <span>•</span>
                        <span>depth: {ml.features.path_depth ?? 'N/A'}</span>
                        <span>•</span>
                        <span>hyphens: {ml.features.hyphen_count ?? 'N/A'}</span>
                        <span>•</span>
                        <span>keywords: {ml.features.suspicious_keyword_count ?? 0}</span>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="p-3 bg-[#181818] border border-[#2A2A2A] text-xs text-[#A1A1A1] space-y-1">
                  <div className="flex items-center space-x-1.5 text-[#FBBF24]">
                    <HelpCircle className="w-3.5 h-3.5" />
                    <span className="font-semibold uppercase">ML analysis unavailable</span>
                  </div>
                  <p className="text-[11px] text-[#888888] leading-relaxed">
                    The offline machine learning phishing classifier did not participate in this assessment.
                    TrustGuard AI never converts missing ML telemetry into a safe result.
                  </p>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* ================================================================= */}
        {/* 2. VIRUSTOTAL THREAT INTELLIGENCE                                 */}
        {/* ================================================================= */}
        <Card variant="standard" className="p-5 space-y-4">
          <div
            className="flex items-start justify-between cursor-pointer select-none"
            onClick={() => toggle('vt')}
          >
            <div className="flex items-center space-x-2.5">
              <Database className="w-4 h-4 text-[#A1A1A1]" />
              <div>
                <h3 className="text-xs font-mono font-semibold uppercase text-[#F5F5F5]">
                  VirusTotal Threat Intelligence
                </h3>
                <span className="text-[11px] font-mono text-[#666666]">
                  Multi-Vendor Antivirus Consensus
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Badge
                variant={
                  vt?.status === 'AVAILABLE'
                    ? (vt.detection_count ?? 0) > 0
                      ? 'malicious'
                      : 'safe'
                    : 'unknown'
                }
                size="xs"
                dot
              >
                {vt?.status === 'AVAILABLE'
                  ? `${vt.detection_count ?? 0} / ${vt.total_engines ?? 0} FLAGGED`
                  : 'UNAVAILABLE'}
              </Badge>
              {expanded.vt ? (
                <ChevronUp className="w-4 h-4 text-[#666666]" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[#666666]" />
              )}
            </div>
          </div>

          {expanded.vt && (
            <div className="space-y-3 pt-2 border-t border-[#222222] text-xs font-mono">
              {vt && vt.total_engines ? (
                <>
                  <div className="grid grid-cols-2 gap-2 bg-[#101010] p-3 border border-[#1F1F1F]">
                    <div>
                      <span className="text-[#666666] text-[10px] uppercase block">
                        Malicious Detections
                      </span>
                      <span
                        className={`text-lg font-bold ${
                          (vt.detection_count ?? 0) > 0 ? 'text-[#F87171]' : 'text-[#4ADE80]'
                        }`}
                      >
                        {vt.detection_count ?? 0} / {vt.total_engines}
                      </span>
                    </div>

                    <div>
                      <span className="text-[#666666] text-[10px] uppercase block">
                        Vendor Consensus Subscore
                      </span>
                      <span className="text-lg font-bold text-[#F5F5F5]">
                        {vt.vt_score !== null && vt.vt_score !== undefined ? `${vt.vt_score}/100` : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <p className="text-[#A1A1A1] text-[11px] leading-relaxed">
                    Telemetry queries global antivirus and security engine reputations.
                    <span className="text-[#FBBF24] block mt-1">
                      Critical Security Principle: Zero detections must not be treated as proof of safety.
                      New zero-day campaigns frequently evade static antivirus signatures during early deployment.
                    </span>
                  </p>
                </>
              ) : (
                <div className="p-3 bg-[#181818] border border-[#2A2A2A] text-xs text-[#A1A1A1] space-y-1">
                  <div className="flex items-center space-x-1.5 text-[#FBBF24]">
                    <HelpCircle className="w-3.5 h-3.5" />
                    <span className="font-semibold uppercase">Feed Unavailable / Unconfigured</span>
                  </div>
                  <p className="text-[11px] text-[#888888] leading-relaxed">
                    External threat intelligence telemetry was not queried or returned inconclusive during this scan.
                    Absence of threat feed data is not evidence of safety.
                  </p>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* ================================================================= */}
        {/* 3. URL STRUCTURE ANALYSIS                                          */}
        {/* ================================================================= */}
        <Card variant="standard" className="p-5 space-y-4">
          <div
            className="flex items-start justify-between cursor-pointer select-none"
            onClick={() => toggle('url')}
          >
            <div className="flex items-center space-x-2.5">
              <Binary className="w-4 h-4 text-[#A1A1A1]" />
              <div>
                <h3 className="text-xs font-mono font-semibold uppercase text-[#F5F5F5]">
                  URL Structure Analysis
                </h3>
                <span className="text-[11px] font-mono text-[#666666]">
                  Lexical Heuristics & Deception Indicators
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Badge
                variant={
                  (urlAnalysis?.indicators?.length ?? 0) > 0 ? 'suspicious' : 'safe'
                }
                size="xs"
                dot
              >
                {urlAnalysis?.indicators?.length ?? 0} ANOMALIES
              </Badge>
              {expanded.url ? (
                <ChevronUp className="w-4 h-4 text-[#666666]" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[#666666]" />
              )}
            </div>
          </div>

          {expanded.url && (
            <div className="space-y-3 pt-2 border-t border-[#222222] text-xs font-mono">
              <div className="grid grid-cols-2 gap-2 bg-[#101010] p-3 border border-[#1F1F1F]">
                <div>
                  <span className="text-[#666666] text-[10px] uppercase block">
                    Syntactic Subscore
                  </span>
                  <span className="text-lg font-bold text-[#F5F5F5]">
                    {urlAnalysis?.url_score !== null && urlAnalysis?.url_score !== undefined
                      ? `${urlAnalysis.url_score}/100`
                      : 'N/A'}
                  </span>
                </div>

                <div>
                  <span className="text-[#666666] text-[10px] uppercase block">
                    Flagged Patterns
                  </span>
                  <span className="text-lg font-bold text-[#F5F5F5]">
                    {urlAnalysis?.indicators?.length ?? 0} flags
                  </span>
                </div>
              </div>

              {urlAnalysis?.indicators && urlAnalysis.indicators.length > 0 ? (
                <div className="space-y-2 pt-1">
                  {urlAnalysis.indicators.map((ind: any, i: number) => (
                    <div
                      key={i}
                      className="p-2.5 bg-[#0F0F0F] border border-[#222222] space-y-1 text-[11px]"
                    >
                      <div className="flex items-center justify-between text-[#F5F5F5]">
                        <span className="font-semibold text-xs text-[#FBBF24]">
                          {ind.name || 'HEURISTIC_FLAG'}
                        </span>
                        <span className="text-[10px] text-[#666666] uppercase">
                          {ind.severity || 'low'}
                        </span>
                      </div>
                      <p className="text-[#888888] leading-relaxed">{ind.description}</p>
                      {ind.reason && (
                        <p className="text-[10px] text-[#666666] italic">
                          Why it matters: {ind.reason}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[#888888] text-[11px] leading-relaxed">
                  No deceptive patterns, userinfo obfuscation (@), homoglyphs, or abnormal token depths
                  were identified in the submitted URL string.
                </p>
              )}
            </div>
          )}
        </Card>

        {/* ================================================================= */}
        {/* 4. SSL/TLS CERTIFICATE VALIDATION                                 */}
        {/* ================================================================= */}
        <Card variant="standard" className="p-5 space-y-4">
          <div
            className="flex items-start justify-between cursor-pointer select-none"
            onClick={() => toggle('ssl')}
          >
            <div className="flex items-center space-x-2.5">
              <Lock className="w-4 h-4 text-[#A1A1A1]" />
              <div>
                <h3 className="text-xs font-mono font-semibold uppercase text-[#F5F5F5]">
                  SSL/TLS Certificate Validation
                </h3>
                <span className="text-[11px] font-mono text-[#666666]">
                  Transport Security & Root CA Audit
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Badge
                variant={
                  ssl?.ssl_status === 'VALID'
                    ? 'safe'
                    : ssl?.ssl_status === 'HTTPS_NOT_USED'
                    ? 'suspicious'
                    : ssl?.ssl_status
                    ? 'malicious'
                    : 'unknown'
                }
                size="xs"
                dot
              >
                {ssl?.ssl_status || 'UNAUDITED'}
              </Badge>
              {expanded.ssl ? (
                <ChevronUp className="w-4 h-4 text-[#666666]" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[#666666]" />
              )}
            </div>
          </div>

          {expanded.ssl && (
            <div className="space-y-3 pt-2 border-t border-[#222222] text-xs font-mono">
              {ssl && ssl.ssl_status ? (
                <>
                  <div className="grid grid-cols-2 gap-2 bg-[#101010] p-3 border border-[#1F1F1F]">
                    <div>
                      <span className="text-[#666666] text-[10px] uppercase block">
                        Certificate Status
                      </span>
                      <span
                        className={`text-sm font-bold uppercase ${
                          ssl.ssl_status === 'VALID' ? 'text-[#4ADE80]' : 'text-[#F87171]'
                        }`}
                      >
                        {ssl.ssl_status}
                      </span>
                    </div>

                    <div>
                      <span className="text-[#666666] text-[10px] uppercase block">
                        Days Remaining
                      </span>
                      <span className="text-sm font-bold text-[#F5F5F5]">
                        {ssl.ssl_days_remaining !== undefined && ssl.ssl_days_remaining !== null
                          ? `${ssl.ssl_days_remaining} days`
                          : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <div className="p-2.5 bg-[#0D0D0D] border border-[#1A1A1A] text-[11px] space-y-1">
                    <div className="text-[#A1A1A1]">
                      <span className="text-[#666666]">Issuer:</span>{' '}
                      {ssl.ssl_issuer || 'Public Certificate Authority'}
                    </div>
                    {ssl.ssl_expiry_date && (
                      <div className="text-[#A1A1A1]">
                        <span className="text-[#666666]">Expires:</span>{' '}
                        {new Date(ssl.ssl_expiry_date).toISOString().split('T')[0]}
                      </div>
                    )}
                  </div>

                  <p className="text-[#A1A1A1] text-[11px] leading-relaxed">
                    <span className="text-[#FBBF24] block font-semibold mb-0.5">
                      Security Clarification:
                    </span>
                    A valid SSL certificate guarantees transport encryption between your browser and the
                    host. It does NOT guarantee corporate authenticity or verify that the website is benign.
                    Over 80% of modern phishing websites utilize valid, free certificates (e.g. Let's Encrypt).
                  </p>
                </>
              ) : (
                <div className="p-3 bg-[#181818] border border-[#2A2A2A] text-xs text-[#A1A1A1] space-y-1">
                  <div className="flex items-center space-x-1.5 text-[#FBBF24]">
                    <HelpCircle className="w-3.5 h-3.5" />
                    <span className="font-semibold uppercase">Transport Audit Inconclusive</span>
                  </div>
                  <p className="text-[11px] text-[#888888] leading-relaxed">
                    Could not establish transport connection to audit SSL/TLS certificates due to network timeout
                    or connection refusal.
                  </p>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* ================================================================= */}
        {/* 5. DOMAIN REPUTATION & BRAND IDENTITY                             */}
        {/* ================================================================= */}
        <Card variant="standard" className="p-5 space-y-4 md:col-span-2">
          <div
            className="flex items-start justify-between cursor-pointer select-none"
            onClick={() => toggle('rep')}
          >
            <div className="flex items-center space-x-2.5">
              <Globe className="w-4 h-4 text-[#A1A1A1]" />
              <div>
                <h3 className="text-xs font-mono font-semibold uppercase text-[#F5F5F5]">
                  Domain Reputation & Brand Identity Intelligence
                </h3>
                <span className="text-[11px] font-mono text-[#666666]">
                  Registered Domain: {rep?.registered_domain || report.domain || 'N/A'}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Badge
                variant={
                  rep?.category === 'VERIFIED_ESTABLISHED'
                    ? 'safe'
                    : rep?.category === 'IMPERSONATION_RISK' || rep?.category === 'CONFIRMED_MALICIOUS'
                    ? 'malicious'
                    : rep?.category === 'SUSPICIOUS_PATTERN'
                    ? 'suspicious'
                    : 'unknown'
                }
                size="xs"
                dot
              >
                {rep?.category?.replace(/_/g, ' ') || 'NEUTRAL UNFAMILIAR'}
              </Badge>
              {expanded.rep ? (
                <ChevronUp className="w-4 h-4 text-[#666666]" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[#666666]" />
              )}
            </div>
          </div>

          {expanded.rep && (
            <div className="space-y-3 pt-2 border-t border-[#222222] text-xs font-mono">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 bg-[#101010] p-3 border border-[#1F1F1F]">
                <div>
                  <span className="text-[#666666] text-[10px] uppercase block">
                    Reputation Subscore
                  </span>
                  <span className="text-sm font-bold text-[#F5F5F5]">
                    {rep?.reputation_score !== undefined ? `${rep.reputation_score}/100` : '50/100 (Neutral)'}
                  </span>
                </div>

                <div>
                  <span className="text-[#666666] text-[10px] uppercase block">
                    Verified Identity
                  </span>
                  <span className="text-sm font-bold text-[#F5F5F5]">
                    {rep?.verified_identity ? (
                      <span className="text-[#4ADE80] flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        {rep.verified_identity}
                      </span>
                    ) : (
                      <span className="text-[#A1A1A1]">Unverified Entity</span>
                    )}
                  </span>
                </div>

                <div>
                  <span className="text-[#666666] text-[10px] uppercase block">
                    Historical Stability
                  </span>
                  <span className="text-sm font-bold text-[#F5F5F5]">
                    {rep?.historical_trend?.reputation_stability?.replace(/_/g, ' ') || 'NEW UNOBSERVED'}
                  </span>
                </div>
              </div>

              {rep?.is_lookalike_or_impersonation && (
                <div className="p-3 bg-[#2A0808] border border-[#7F1D1D] text-[#FCA5A5] flex items-start gap-2 text-xs">
                  <AlertTriangle className="w-4 h-4 text-[#EF4444] shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold block uppercase text-[#EF4444]">
                      Impersonation Alert
                    </span>
                    This domain mimics protected brand{' '}
                    <strong className="underline text-white font-mono">
                      {rep.impersonated_brand}
                    </strong>{' '}
                    using deceptive typo/subdomain structures.
                  </div>
                </div>
              )}

              {rep?.reasons && rep.reasons.length > 0 && (
                <div className="p-2.5 bg-[#0D0D0D] border border-[#1A1A1A] space-y-1">
                  <span className="text-[10px] uppercase text-[#666666] block font-semibold">
                    Reputation Evidence & Observations
                  </span>
                  <ul className="list-disc list-inside text-[11px] text-[#A1A1A1] space-y-0.5">
                    {rep.reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
