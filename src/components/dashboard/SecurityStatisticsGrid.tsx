import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, HelpCircle, Activity, Globe } from 'lucide-react';
import { Card } from '../common/Card';
import { Skeleton } from '../common/Skeleton';
import { ScanStatistics } from '../../types/scan';

interface SecurityStatisticsGridProps {
  statistics: ScanStatistics | null;
  isLoading: boolean;
}

export const SecurityStatisticsGrid: React.FC<SecurityStatisticsGridProps> = ({
  statistics,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} variant="standard" className="p-4 space-y-3">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-7 w-16" />
            <Skeleton className="h-2.5 w-full" />
          </Card>
        ))}
      </div>
    );
  }

  const total = statistics?.total_scans ?? 0;
  const critical = statistics?.critical_risk_scans ?? 0;
  const high = statistics?.high_risk_scans ?? 0;
  const totalThreats = critical + high;
  const moderate = statistics?.moderate_risk_scans ?? 0;
  const low = statistics?.low_risk_scans ?? 0;
  const incomplete = statistics?.incomplete_assessments ?? 0;
  const avgScore =
    statistics?.average_trust_score !== null && statistics?.average_trust_score !== undefined
      ? `${statistics.average_trust_score}/100`
      : 'N/A';

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between pb-1">
        <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-[#A1A1A1]">
          ACCOUNT AUDIT TELEMETRY & METRICS
        </h2>
        <span className="text-[11px] font-mono text-[#666666]">
          REAL-TIME PERSISTED DATABASE TOTALS
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {/* Metric 1: Total Scans */}
        <Card variant="standard" className="p-4 space-y-2 relative overflow-hidden">
          <div className="flex items-center justify-between text-[#A1A1A1]">
            <span className="text-[10px] font-mono uppercase tracking-wider">TOTAL INSPECTIONS</span>
            <Globe className="w-3.5 h-3.5 text-[#666666]" />
          </div>
          <div className="text-2xl font-mono font-bold text-[#F5F5F5]">{total}</div>
          <p className="text-[10px] font-mono text-[#666666] leading-relaxed">
            Lifetime private scans conducted by your account.
          </p>
        </Card>

        {/* Metric 2: Average Trust Score */}
        <Card variant="standard" className="p-4 space-y-2">
          <div className="flex items-center justify-between text-[#A1A1A1]">
            <span className="text-[10px] font-mono uppercase tracking-wider">AVG TRUST SCORE</span>
            <Activity className="w-3.5 h-3.5 text-[#666666]" />
          </div>
          <div className="text-2xl font-mono font-bold text-[#F5F5F5]">{avgScore}</div>
          <p className="text-[10px] font-mono text-[#666666] leading-relaxed">
            Mean weighted score across completed assessments.
          </p>
        </Card>

        {/* Metric 3: Critical & High Threats */}
        <Card variant="standard" className="p-4 space-y-2">
          <div className="flex items-center justify-between text-[#A1A1A1]">
            <span className="text-[10px] font-mono uppercase tracking-wider">THREATS FLAGGED</span>
            <ShieldAlert className="w-3.5 h-3.5 text-[#F87171]" />
          </div>
          <div className="text-2xl font-mono font-bold text-[#F87171]">{totalThreats}</div>
          <p className="text-[10px] font-mono text-[#666666] leading-relaxed">
            {critical} critical and {high} high risk confirmed anomalies.
          </p>
        </Card>

        {/* Metric 4: Moderate / Medium Risk */}
        <Card variant="standard" className="p-4 space-y-2">
          <div className="flex items-center justify-between text-[#A1A1A1]">
            <span className="text-[10px] font-mono uppercase tracking-wider">MODERATE RISK</span>
            <AlertTriangle className="w-3.5 h-3.5 text-[#FBBF24]" />
          </div>
          <div className="text-2xl font-mono font-bold text-[#FBBF24]">{moderate}</div>
          <p className="text-[10px] font-mono text-[#666666] leading-relaxed">
            Ambiguous lexical patterns or unverified certificate roots.
          </p>
        </Card>

        {/* Metric 5: Safe / Low Risk */}
        <Card variant="standard" className="p-4 space-y-2">
          <div className="flex items-center justify-between text-[#A1A1A1]">
            <span className="text-[10px] font-mono uppercase tracking-wider">SAFE / LOW RISK</span>
            <ShieldCheck className="w-3.5 h-3.5 text-[#4ADE80]" />
          </div>
          <div className="text-2xl font-mono font-bold text-[#4ADE80]">{low}</div>
          <p className="text-[10px] font-mono text-[#666666] leading-relaxed">
            Scans with high Trust Scores (&ge; 80) and valid TLS.
          </p>
        </Card>

        {/* Metric 6: Incomplete / Inconclusive */}
        <Card variant="standard" className="p-4 space-y-2">
          <div className="flex items-center justify-between text-[#A1A1A1]">
            <span className="text-[10px] font-mono uppercase tracking-wider">INCOMPLETE AUDITS</span>
            <HelpCircle className="w-3.5 h-3.5 text-[#A1A1A1]" />
          </div>
          <div className="text-2xl font-mono font-bold text-[#A1A1A1]">{incomplete}</div>
          <p className="text-[10px] font-mono text-[#666666] leading-relaxed">
            Partial telemetry or errors — never treated as safe.
          </p>
        </Card>
      </div>
    </div>
  );
};

export default SecurityStatisticsGrid;

