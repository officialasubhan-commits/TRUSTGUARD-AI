import React from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, HelpCircle, AlertOctagon } from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { DetailedSecurityReport, RiskLevel } from '../../types/scan';

interface OverallAssessmentCardProps {
  report: DetailedSecurityReport;
}

export const OverallAssessmentCard: React.FC<OverallAssessmentCardProps> = ({ report }) => {
  const score = report.digital_trust_score;
  const isInsufficient =
    report.assessment_status === 'INSUFFICIENT_DATA' || score === null || score === undefined;

  const coveragePct =
    report.coverage_percentage ??
    (report.assessment_coverage ? Math.round(report.assessment_coverage * 100) : null);

  const getRiskColor = (level?: RiskLevel) => {
    switch (level) {
      case 'SAFE':
      case 'LOW':
        return '#4ADE80';
      case 'MEDIUM':
        return '#FBBF24';
      case 'HIGH':
      case 'CRITICAL':
        return '#F87171';
      default:
        return '#A1A1A1';
    }
  };

  const getRiskIcon = (level?: RiskLevel) => {
    switch (level) {
      case 'SAFE':
      case 'LOW':
        return <ShieldCheck className="w-5 h-5 text-[#4ADE80]" />;
      case 'MEDIUM':
        return <AlertTriangle className="w-5 h-5 text-[#FBBF24]" />;
      case 'HIGH':
        return <ShieldAlert className="w-5 h-5 text-[#F87171]" />;
      case 'CRITICAL':
        return <AlertOctagon className="w-5 h-5 text-[#F87171]" />;
      default:
        return <HelpCircle className="w-5 h-5 text-[#A1A1A1]" />;
    }
  };

  const getBadgeVariant = (level?: RiskLevel) => {
    switch (level) {
      case 'SAFE':
      case 'LOW':
        return 'safe';
      case 'MEDIUM':
        return 'suspicious';
      case 'HIGH':
      case 'CRITICAL':
        return 'malicious';
      default:
        return 'unknown';
    }
  };

  // Circular gauge parameters
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset =
    score !== null && score !== undefined
      ? circumference - (score / 100) * circumference
      : circumference;
  const strokeColor = getRiskColor(report.risk_level);

  return (
    <Card pixelFrame className="p-6 sm:p-8 space-y-6">
      {/* High Severity Override Alert Banner */}
      {report.high_severity_override && (
        <div className="p-4 bg-[#450A0A]/40 border border-[#991B1B] text-[#F87171] text-xs font-mono space-y-1">
          <div className="flex items-center space-x-2 font-semibold tracking-wider uppercase">
            <AlertOctagon className="w-4 h-4 shrink-0" />
            <span>CRITICAL SECURITY OVERRIDE TRIGGERED</span>
          </div>
          <p className="text-[#F5F5F5] leading-relaxed">
            {report.override_reason ||
              'A critical threat vector was confirmed. The final Digital Trust Score was overridden to reflect immediate risk.'}
          </p>
        </div>
      )}

      {/* Main Assessment Layout */}
      <div className="flex flex-col lg:flex-row items-center justify-between gap-8">
        {/* Left: Target Domain & Synthesis Summary */}
        <div className="space-y-4 flex-1 text-center lg:text-left">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-2 text-xs font-mono text-[#666666]">
              <span>ASSESSMENT VERDICT</span>
              <span>•</span>
              <span>ALGORITHM: {report.scoring_version || 'v1.0.0'}</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-light text-[#F5F5F5] break-all font-mono">
              {report.domain}
            </h2>
          </div>

          <p className="text-xs sm:text-sm text-[#A1A1A1] font-mono leading-relaxed max-w-2xl">
            {report.summary ||
              'Synthesized evaluation from available threat intelligence, structural URL entropy, and offline machine learning models.'}
          </p>

          <div className="flex flex-wrap items-center justify-center lg:justify-start gap-3 pt-2">
            <Badge variant={getBadgeVariant(report.risk_level)} size="md" dot>
              {report.risk_label || report.risk_level || 'UNKNOWN'}
            </Badge>

            <span className="text-xs font-mono text-[#666666] border border-[#222222] px-2.5 py-1 bg-[#101010]">
              {coveragePct !== null ? `${coveragePct}% EVIDENCE COVERAGE` : 'COVERAGE UNKNOWN'}
            </span>

            {report.assessment_status && (
              <span className="text-xs font-mono text-[#888888] border border-[#222222] px-2.5 py-1 bg-[#101010] uppercase">
                STATUS: {report.assessment_status}
              </span>
            )}
          </div>
        </div>

        {/* Right: Circular Score Gauge */}
        <div className="flex flex-col items-center justify-center shrink-0 p-4 bg-[#101010] border border-[#222222] min-w-[200px]">
          <div className="relative w-36 h-36 flex items-center justify-center">
            {/* Background SVG Gauge Ring */}
            <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 128 128">
              <circle
                cx="64"
                cy="64"
                r={radius}
                stroke="#222222"
                strokeWidth="8"
                fill="none"
              />
              {!isInsufficient && (
                <circle
                  cx="64"
                  cy="64"
                  r={radius}
                  stroke={strokeColor}
                  strokeWidth="8"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="square"
                  fill="none"
                  className="transition-all duration-700 ease-out"
                />
              )}
            </svg>

            {/* Inner Score Readout */}
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              {isInsufficient ? (
                <div className="space-y-0.5">
                  <span className="text-2xl font-mono font-bold text-[#A1A1A1]">N/A</span>
                  <span className="text-[10px] font-mono text-[#666666] block">INCONCLUSIVE</span>
                </div>
              ) : (
                <div className="space-y-0.5">
                  <span className="text-3xl font-mono font-bold text-[#F5F5F5]">{score}</span>
                  <span className="text-[10px] font-mono text-[#666666] block">/ 100 TRUST</span>
                </div>
              )}
            </div>
          </div>

          <div className="mt-3 flex items-center space-x-1.5 text-xs font-mono text-[#A1A1A1]">
            {getRiskIcon(report.risk_level)}
            <span className="font-semibold uppercase tracking-wider">
              {report.risk_label || report.risk_level || 'EVALUATED'}
            </span>
          </div>
        </div>
      </div>

      {/* Uncertainty Notice if Telemetry is Incomplete */}
      {isInsufficient && (
        <div className="p-3 bg-[#181818] border border-[#333333] text-xs font-mono text-[#A1A1A1] space-y-1">
          <span className="text-[#FBBF24] font-semibold uppercase block">
            [ NOTICE: INSUFFICIENT EVIDENCE FOR DEFINITIVE SCORING ]
          </span>
          <p className="text-[11px] text-[#888888] leading-relaxed">
            Critical security feeds were unavailable or returned inconclusive during this scan. TrustGuard AI
            refuses to fabricate positive trust scores without verified telemetry. Exercise caution before
            interacting with or submitting credentials to this destination.
          </p>
        </div>
      )}
    </Card>
  );
};

