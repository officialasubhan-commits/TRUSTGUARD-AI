import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Container } from '../components/common/Container';
import {
  ReportHeader,
  OverallAssessmentCard,
  SecurityEngineCards,
  ExplainableThreatAnalysis,
  EvidenceCoverageSection,
  SecurityRecommendations,
  ReportLoadingSkeleton,
  ReportErrorState,
  ReportProcessingState,
} from '../components/reports';
import { scanService } from '../services/scanService';
import { formatApiError } from '../services/api';
import { DetailedSecurityReport, RiskLevel } from '../types/scan';

const UUID_REGEX =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/**
 * Safely transforms composite scan details (from /api/v1/scan/{id}) into
 * a DetailedSecurityReport document without unsafe property assumptions.
 */
function mapScanDetailToReport(raw: any, fallbackScanId: string): DetailedSecurityReport {
  const scan = raw?.scan || (raw?.scan_id ? raw : {});
  const result = raw?.result || raw?.trust_assessment || {};
  const breakdown = result?.score_breakdown || {};

  const scanId = scan?.id || raw?.scan_id || fallbackScanId;
  const originalUrl = scan?.submitted_url || raw?.original_url || '';
  const normalizedUrl = scan?.normalized_url || raw?.normalized_url || originalUrl;

  // Safe domain extraction
  let domain = scan?.domain || raw?.domain || '';
  if (!domain && typeof normalizedUrl === 'string' && normalizedUrl.trim() !== '') {
    try {
      const parsed = new URL(
        normalizedUrl.startsWith('http') ? normalizedUrl : `https://${normalizedUrl}`
      );
      domain = parsed.hostname;
    } catch {
      domain = normalizedUrl.replace(/^https?:\/\//i, '').split('/')[0];
    }
  }
  if (!domain) {
    domain = 'unknown-domain';
  }

  // Derive risk label if absent
  let riskLabel = breakdown?.risk_label || null;
  const trustScore =
    scan?.trust_score ?? result?.trust_score ?? raw?.digital_trust_score ?? null;
  if (!riskLabel && trustScore !== null && trustScore !== undefined) {
    if (trustScore >= 80) riskLabel = 'LOW RISK';
    else if (trustScore >= 60) riskLabel = 'MODERATE RISK';
    else if (trustScore >= 30) riskLabel = 'HIGH RISK';
    else riskLabel = 'CRITICAL RISK';
  }

  const cov = scan?.assessment_coverage ?? breakdown?.assessment_coverage ?? null;
  const covPct =
    breakdown?.coverage_percentage ??
    (cov !== null && cov !== undefined ? Math.round(cov * 100) : null);

  return {
    scan_id: scanId,
    original_url: originalUrl,
    normalized_url: normalizedUrl,
    domain,
    is_guest: Boolean(scan?.is_guest ?? raw?.is_guest ?? true),
    scan_status: scan?.scan_status || raw?.scan_status || 'complete',
    digital_trust_score: trustScore,
    risk_score: scan?.risk_score ?? result?.risk_score ?? null,
    risk_level: (scan?.risk_level ?? result?.overall_risk_level ?? raw?.risk_level ?? 'UNKNOWN') as RiskLevel,
    risk_label: riskLabel,
    assessment_status: scan?.assessment_status ?? breakdown?.assessment_status ?? null,
    assessment_coverage: cov,
    coverage_percentage: covPct,
    high_severity_override: Boolean(breakdown?.high_severity_override ?? false),
    override_reason: breakdown?.override_reason ?? null,
    scoring_version: scan?.scoring_version ?? breakdown?.scoring_version ?? null,
    model_version: result?.ml_prediction ?? null,
    submitted_at: scan?.created_at || raw?.submitted_at || new Date().toISOString(),
    completed_at: scan?.completed_at || raw?.completed_at || null,
    summary: result?.analysis_summary ?? breakdown?.summary ?? raw?.summary ?? null,
    recommendations: breakdown?.recommendations ?? result?.recommendations ?? [],
    risk_indicators: breakdown?.risk_indicators || [],
    positive_indicators: breakdown?.positive_indicators || [],
    unknown_indicators: breakdown?.unknown_indicators || [],
    module_scores: breakdown?.module_scores || {},
    url_analysis: result?.url_risk_indicators
      ? { url_score: result?.url_score ?? null, indicators: result.url_risk_indicators }
      : raw?.url_analysis ?? null,
    virustotal_findings: result?.virustotal_total_engines
      ? {
          detection_count: result?.virustotal_detection_count ?? 0,
          total_engines: result.virustotal_total_engines,
          status: result?.threat_intelligence_status ?? 'AVAILABLE',
          vt_score: result?.vt_score ?? null,
        }
      : raw?.virustotal_findings ?? null,
    ml_phishing_prediction: result?.ml_prediction
      ? {
          prediction: result.ml_prediction,
          phishing_probability: result?.phishing_probability ?? null,
          ml_score: result?.ml_score ?? null,
          features: result?.ml_features ?? null,
        }
      : raw?.ml_phishing_prediction ?? null,
    ssl_tls_validation: result?.ssl_status
      ? {
          ssl_status: result.ssl_status,
          ssl_valid: result?.ssl_valid ?? null,
          ssl_issuer: result?.ssl_issuer ?? null,
          ssl_expiry_date: result?.ssl_expiry_date ?? null,
          ssl_days_remaining: result?.ssl_days_remaining ?? null,
          ssl_score: result?.ssl_score ?? null,
        }
      : raw?.ssl_tls_validation ?? null,
    domain_reputation: raw?.domain_reputation ?? result?.domain_reputation ?? null,
  };
}

export const ReportPage: React.FC = () => {
  const { scanId } = useParams<{ scanId: string }>();

  const [report, setReport] = useState<DetailedSecurityReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [error, setError] = useState<{ code: string; message: string } | null>(null);

  const pollTimerRef = useRef<number | null>(null);
  const elapsedTimerRef = useRef<number | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isFetchingRef = useRef<boolean>(false);

  const clearTimers = useCallback(() => {
    if (pollTimerRef.current) {
      window.clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    if (elapsedTimerRef.current) {
      window.clearInterval(elapsedTimerRef.current);
      elapsedTimerRef.current = null;
    }
  }, []);

  const fetchReportData = useCallback(
    async (isPoll: boolean = false, retryAttempt: number = 0) => {
      // 1. Validate route identifier
      const cleanScanId = scanId ? scanId.trim() : '';

      if (!cleanScanId || cleanScanId === 'undefined' || cleanScanId === 'null') {
        clearTimers();
        setIsLoading(false);
        setIsProcessing(false);
        setError({
          code: 'MISSING_SCAN_ID',
          message: 'No scan identifier was provided in the route URL.',
        });
        return;
      }

      if (!UUID_REGEX.test(cleanScanId)) {
        clearTimers();
        setIsLoading(false);
        setIsProcessing(false);
        setError({
          code: 'INVALID_SCAN_ID',
          message: `The provided scan identifier '${cleanScanId}' is not a valid UUID format.`,
        });
        return;
      }

      // Prevent duplicate simultaneous initial lookups
      if (isFetchingRef.current && !isPoll) {
        return;
      }

      if (!isPoll) {
        setIsLoading(true);
        setError(null);
      }

      // Cancel any prior in-flight request before launching new one
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;
      isFetchingRef.current = true;

      try {
        let detailedData: DetailedSecurityReport;

        try {
          // Primary: Retrieve detailed security report from /api/v1/scans/{id}
          detailedData = await scanService.getDetailedReport(cleanScanId, controller.signal);
        } catch (primaryErr: any) {
          // If aborted by unmount or user action, exit silently
          if (
            controller.signal.aborted ||
            primaryErr?.name === 'CanceledError' ||
            primaryErr?.code === 'ERR_CANCELED' ||
            primaryErr?.code === 'SCAN_CANCELLED'
          ) {
            return;
          }

          // If a transient 404 occurs on the very first navigation attempt (e.g. database write-replication window),
          // retry once after 350ms before failing or falling back
          if (
            !isPoll &&
            retryAttempt === 0 &&
            (primaryErr?.response?.status === 404 || primaryErr?.status === 404)
          ) {
            await new Promise((resolve) => window.setTimeout(resolve, 350));
            if (controller.signal.aborted) return;
            return fetchReportData(false, 1);
          }

          // Fallback: Query /api/v1/scan/{id} composite endpoint if /scans was unavailable
          try {
            const composite = await scanService.getScanById(cleanScanId, controller.signal);
            if (controller.signal.aborted) return;
            detailedData = mapScanDetailToReport(composite, cleanScanId);
          } catch (fallbackErr: any) {
            // If fallback also failed or was cancelled, throw the original primary error
            if (
              controller.signal.aborted ||
              fallbackErr?.name === 'CanceledError' ||
              fallbackErr?.code === 'ERR_CANCELED'
            ) {
              return;
            }
            throw primaryErr;
          }
        }

        // If request was aborted while resolving, do not update state
        if (controller.signal.aborted) {
          return;
        }

        setReport(detailedData);
        setError(null);
        setIsLoading(false);

        // Handle async scan in-flight processing status
        if (detailedData.scan_status === 'pending' || detailedData.scan_status === 'processing') {
          setIsProcessing(true);
          if (!elapsedTimerRef.current) {
            elapsedTimerRef.current = window.setInterval(() => {
              setElapsedSeconds((s) => s + 1);
            }, 1000);
          }
          // Poll every 2.5 seconds up to timeout
          pollTimerRef.current = window.setTimeout(() => {
            fetchReportData(true);
          }, 2500);
        } else {
          setIsProcessing(false);
          clearTimers();
        }
      } catch (err: any) {
        // Silently exit if aborted
        if (
          controller.signal.aborted ||
          err?.name === 'CanceledError' ||
          err?.code === 'ERR_CANCELED' ||
          err?.code === 'SCAN_CANCELLED'
        ) {
          return;
        }

        clearTimers();
        setIsLoading(false);
        setIsProcessing(false);

        const formatted = formatApiError(err);
        setError({
          code:
            formatted.code ||
            (err instanceof TypeError ? 'CLIENT_ERROR' : 'SCAN_NOT_FOUND'),
          message:
            formatted.message ||
            'Unable to retrieve the requested security report from the database.',
        });
      } finally {
        isFetchingRef.current = false;
      }
    },
    [scanId, clearTimers]
  );

  useEffect(() => {
    // Reset state on route change
    setReport(null);
    setError(null);
    setElapsedSeconds(0);
    setIsProcessing(false);

    fetchReportData(false);

    return () => {
      clearTimers();
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      isFetchingRef.current = false;
    };
  }, [scanId, fetchReportData, clearTimers]);

  return (
    <div className="flex-1 py-10 md:py-16">
      <Container size="lg">
        {/* State 1: Initial Loading Skeleton */}
        {isLoading && <ReportLoadingSkeleton />}

        {/* State 2: Error Screen */}
        {error && !isLoading && (
          <ReportErrorState
            code={error.code}
            message={error.message}
            onRetry={() => fetchReportData(false)}
          />
        )}

        {/* State 3: Async In-Flight Processing Screen */}
        {isProcessing && !isLoading && !error && (
          <ReportProcessingState
            elapsedSeconds={elapsedSeconds}
            onCancel={() => {
              clearTimers();
              setIsProcessing(false);
            }}
          />
        )}

        {/* State 4: Complete Security Audit Report */}
        {report && !isLoading && !error && !isProcessing && (
          <div className="space-y-10">
            {/* Section A: Report Header */}
            <ReportHeader report={report} />

            {/* Section B: Overall Security Assessment */}
            <OverallAssessmentCard report={report} />

            {/* Section C: Security Engine Overview (4 Expandable Subsystems) */}
            <SecurityEngineCards report={report} />

            {/* Section D: Explainable Threat Analysis */}
            <ExplainableThreatAnalysis report={report} />

            {/* Section E: Evidence Coverage & Integrity */}
            <EvidenceCoverageSection report={report} />

            {/* Section F: Practical Security Recommendations */}
            <SecurityRecommendations report={report} />
          </div>
        )}
      </Container>
    </div>
  );
};

export default ReportPage;
