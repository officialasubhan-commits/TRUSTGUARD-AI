import React from 'react';
import { Layers, CheckCircle2, XCircle, AlertCircle, HelpCircle } from 'lucide-react';
import { Card } from '../common/Card';
import { DetailedSecurityReport } from '../../types/scan';

interface EvidenceCoverageSectionProps {
  report: DetailedSecurityReport;
}

export const EvidenceCoverageSection: React.FC<EvidenceCoverageSectionProps> = ({ report }) => {
  const moduleScores = report.module_scores || {};
  const modulesList = Object.values(moduleScores) as any[];

  // Compute completed, unavailable, failed checks from module scores and findings
  const completed = modulesList.filter((m) => m.included_in_calculation).length;
  const unavailable = modulesList.filter(
    (m) =>
      !m.included_in_calculation &&
      (m.status === 'UNAVAILABLE' ||
        m.status === 'API_UNAVAILABLE' ||
        m.status === 'TIMEOUT' ||
        m.status === 'INCONCLUSIVE' ||
        m.status === 'MODEL_UNAVAILABLE')
  ).length;
  const failed = modulesList.filter(
    (m) =>
      m.included_in_calculation &&
      (m.normalized_risk >= 70 || m.status === 'MALICIOUS' || m.status === 'UNSAFE_DESTINATION')
  ).length;

  const totalEngines = Math.max(4, modulesList.length);
  const notPerformed = Math.max(0, totalEngines - (completed + unavailable));

  const coveragePct =
    report.coverage_percentage ??
    (report.assessment_coverage ? Math.round(report.assessment_coverage * 100) : null) ??
    Math.round((completed / totalEngines) * 100);

  return (
    <Card variant="panel" className="p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#222222]">
        <div className="flex items-center space-x-2 text-xs font-mono text-[#F5F5F5]">
          <Layers className="w-4 h-4 text-[#A1A1A1]" />
          <span className="font-semibold uppercase tracking-wide">
            EVIDENCE COVERAGE & TELEMETRY INTEGRITY
          </span>
        </div>
        <div className="text-xs font-mono text-[#666666]">
          COVERAGE: <span className="text-[#F5F5F5] font-bold">{coveragePct}%</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-[#1A1A1A] h-2 border border-[#292929] overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${
            coveragePct >= 80
              ? 'bg-[#4ADE80]'
              : coveragePct >= 50
              ? 'bg-[#FBBF24]'
              : 'bg-[#F87171]'
          }`}
          style={{ width: `${Math.min(100, Math.max(0, coveragePct))}%` }}
        />
      </div>

      {/* 4 Counter Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
          <div className="flex items-center space-x-1.5 text-[#4ADE80]">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span className="text-[10px] uppercase font-semibold">Completed Checks</span>
          </div>
          <div className="text-lg font-bold text-[#F5F5F5]">{completed} modules</div>
          <p className="text-[10px] text-[#666666]">Active telemetry feeds</p>
        </div>

        <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
          <div className="flex items-center space-x-1.5 text-[#FBBF24]">
            <HelpCircle className="w-3.5 h-3.5" />
            <span className="text-[10px] uppercase font-semibold">Unavailable Feeds</span>
          </div>
          <div className="text-lg font-bold text-[#F5F5F5]">{unavailable} modules</div>
          <p className="text-[10px] text-[#666666]">Inconclusive or offline</p>
        </div>

        <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
          <div className="flex items-center space-x-1.5 text-[#F87171]">
            <XCircle className="w-3.5 h-3.5" />
            <span className="text-[10px] uppercase font-semibold">Threat Detections</span>
          </div>
          <div className="text-lg font-bold text-[#F5F5F5]">{failed} flags</div>
          <p className="text-[10px] text-[#666666]">High/critical anomalies</p>
        </div>

        <div className="p-3 bg-[#141414] border border-[#222222] space-y-1">
          <div className="flex items-center space-x-1.5 text-[#888888]">
            <AlertCircle className="w-3.5 h-3.5" />
            <span className="text-[10px] uppercase font-semibold">Not Performed</span>
          </div>
          <div className="text-lg font-bold text-[#F5F5F5]">{notPerformed} checks</div>
          <p className="text-[10px] text-[#666666]">Excluded by policy</p>
        </div>
      </div>

      <p className="text-xs text-[#888888] font-mono leading-relaxed pt-1">
        <span className="text-[#A1A1A1] font-semibold">Notice regarding evidence coverage:</span>{' '}
        Evidence coverage measures how many security assessment modules successfully contributed findings.
        It must never be confused with security confidence or safety. A domain with 100% coverage can still
        be confirmed malicious, while a domain with 40% coverage cannot be declared safe.
      </p>
    </Card>
  );
};

