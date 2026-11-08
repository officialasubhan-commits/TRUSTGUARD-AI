import React from 'react';
import { Link } from 'react-router-dom';
import { History, ArrowRight, ExternalLink, ShieldCheck, ShieldAlert, AlertTriangle, Clock } from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Skeleton } from '../common/Skeleton';
import { ScanHistorySummary } from '../../types/scan';

interface RecentActivityListProps {
  recentScans: ScanHistorySummary[];
  isLoading: boolean;
}

export const RecentActivityList: React.FC<RecentActivityListProps> = ({
  recentScans,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <Card pixelFrame className="p-5 md:p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#222222]">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-4 w-24" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="p-3 bg-[#101010] border border-[#222222] flex items-center justify-between">
              <div className="space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-3 w-32" />
              </div>
              <Skeleton className="h-8 w-24" />
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card pixelFrame className="p-5 md:p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#222222]">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-[#A1A1A1]" />
          <div>
            <h3 className="text-xs font-mono font-semibold uppercase text-[#F5F5F5]">
              RECENT SECURITY AUDITS (LATEST 5)
            </h3>
            <span className="text-[11px] font-mono text-[#666666]">
              CHRONOLOGICAL AUDIT TELEMETRY LOGS
            </span>
          </div>
        </div>

        <Link to="/dashboard/history">
          <Button variant="secondary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
            VIEW FULL HISTORY
          </Button>
        </Link>
      </div>

      {/* Body */}
      {recentScans.length === 0 ? (
        <div className="py-12 flex flex-col items-center justify-center space-y-3 text-center border border-dashed border-[#222222] p-6">
          <Clock className="w-8 h-8 text-[#555555]" />
          <div className="space-y-1">
            <h4 className="text-sm font-mono font-semibold uppercase text-[#F5F5F5]">
              NO RECENT AUDITS RECORDED
            </h4>
            <p className="text-xs font-mono text-[#666666] max-w-sm">
              You haven't scanned any websites yet. Conduct your first security audit to begin logging threat telemetry.
            </p>
          </div>
          <div className="pt-2">
            <Link to="/scan">
              <Button size="sm" variant="primary" rightIcon={<ArrowRight className="w-4 h-4" />}>
                RUN FIRST SCAN
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-2.5">
          {recentScans.map((scan) => {
            const formattedDate = new Date(scan.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            });

            const isThreat =
              scan.risk_level === 'CRITICAL' ||
              scan.risk_level === 'HIGH' ||
              scan.risk_level === 'CRITICAL_RISK' ||
              scan.risk_level === 'HIGH_RISK';

            const isSafe =
              scan.risk_level === 'SAFE' ||
              scan.risk_level === 'LOW' ||
              scan.risk_level === 'LOW_RISK';

            return (
              <div
                key={scan.scan_id}
                className="p-3.5 bg-[#101010] hover:bg-[#141414] border border-[#222222] hover:border-[#333333] transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono"
              >
                {/* Domain & Meta */}
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    {isThreat ? (
                      <ShieldAlert className="w-4 h-4 text-[#F87171] shrink-0" />
                    ) : isSafe ? (
                      <ShieldCheck className="w-4 h-4 text-[#4ADE80] shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-[#FBBF24] shrink-0" />
                    )}
                    <span className="font-semibold text-sm text-[#F5F5F5] truncate max-w-md">
                      {scan.domain || scan.normalized_url}
                    </span>
                    <Badge
                      variant={
                        scan.scan_status === 'complete'
                          ? 'safe'
                          : scan.scan_status === 'processing' || scan.scan_status === 'pending'
                          ? 'subtle'
                          : 'malicious'
                      }
                      size="xs"
                    >
                      {scan.scan_status.toUpperCase()}
                    </Badge>
                  </div>

                  <p className="text-[11px] text-[#666666] truncate max-w-lg">
                    <span>{scan.submitted_url}</span>
                    <span className="mx-2">•</span>
                    <span>{formattedDate}</span>
                  </p>
                </div>

                {/* Scores & Report Action */}
                <div className="flex items-center space-x-4 shrink-0">
                  <div className="text-right">
                    <span className="text-[10px] text-[#666666] uppercase block">
                      Trust Score
                    </span>
                    <span
                      className={`text-sm font-bold ${
                        scan.digital_trust_score !== null && scan.digital_trust_score !== undefined
                          ? scan.digital_trust_score >= 80
                            ? 'text-[#4ADE80]'
                            : scan.digital_trust_score >= 50
                            ? 'text-[#FBBF24]'
                            : 'text-[#F87171]'
                          : 'text-[#666666]'
                      }`}
                    >
                      {scan.digital_trust_score !== null && scan.digital_trust_score !== undefined
                        ? `${scan.digital_trust_score}/100`
                        : 'N/A'}
                    </span>
                  </div>

                  <div className="text-right min-w-[80px]">
                    <span className="text-[10px] text-[#666666] uppercase block">
                      Risk Level
                    </span>
                    <span className="text-xs text-[#A1A1A1] uppercase font-semibold">
                      {scan.risk_label || scan.risk_level || 'UNKNOWN'}
                    </span>
                  </div>

                  <Link to={`/report/${scan.scan_id}`}>
                    <Button
                      variant="secondary"
                      size="sm"
                      rightIcon={<ExternalLink className="w-3.5 h-3.5" />}
                    >
                      REPORT
                    </Button>
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};

export default RecentActivityList;
