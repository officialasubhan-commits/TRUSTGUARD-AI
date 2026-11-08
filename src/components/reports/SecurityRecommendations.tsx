import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, CheckCircle2 } from 'lucide-react';
import { Card } from '../common/Card';
import { DetailedSecurityReport } from '../../types/scan';

interface SecurityRecommendationsProps {
  report: DetailedSecurityReport;
}

export const SecurityRecommendations: React.FC<SecurityRecommendationsProps> = ({ report }) => {
  const recommendations = report.recommendations || [];
  const riskLevel = report.risk_level;

  return (
    <Card pixelFrame className="p-6 space-y-4">
      <div className="flex items-center space-x-2 text-xs font-mono text-[#F5F5F5] pb-3 border-b border-[#222222]">
        <ShieldCheck className="w-4 h-4 text-[#A1A1A1]" />
        <span className="font-semibold uppercase tracking-wide">
          ACTIONABLE SECURITY RECOMMENDATIONS
        </span>
      </div>

      <div className="space-y-3 font-mono text-xs">
        {recommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {recommendations.map((rec, index) => (
              <div
                key={index}
                className="p-3 bg-[#101010] border border-[#222222] flex items-start space-x-2.5 text-[#F5F5F5]"
              >
                {riskLevel === 'CRITICAL' || riskLevel === 'HIGH' ? (
                  <AlertOctagon className="w-4 h-4 text-[#F87171] shrink-0 mt-0.5" />
                ) : riskLevel === 'MEDIUM' ? (
                  <AlertTriangle className="w-4 h-4 text-[#FBBF24] shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-[#4ADE80] shrink-0 mt-0.5" />
                )}
                <span className="text-[11px] leading-relaxed text-[#A1A1A1]">{rec}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 bg-[#101010] border border-[#222222] text-[#888888] space-y-1">
            <span className="text-[#F5F5F5] font-semibold block">STANDARD USER HYGIENE:</span>
            <p className="leading-relaxed">
              Always verify destination URLs in official browser address bars. Never submit banking or
              account credentials to links received via unverified SMS or unsolicited email correspondence.
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};

