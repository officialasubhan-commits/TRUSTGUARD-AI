import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Shield,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { DetailedSecurityReport } from '../../types/scan';

interface ExplainableThreatAnalysisProps {
  report: DetailedSecurityReport;
}

export const ExplainableThreatAnalysis: React.FC<ExplainableThreatAnalysisProps> = ({ report }) => {
  const [activeTab, setActiveTab] = useState<'all' | 'risks' | 'positives' | 'unknowns' | 'scoring'>('all');

  const risks = report.risk_indicators || [];
  const positives = report.positive_indicators || [];
  const unknowns = report.unknown_indicators || [];
  const moduleScores = report.module_scores || {};

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'high':
        return <Badge variant="malicious" size="xs">{severity}</Badge>;
      case 'medium':
        return <Badge variant="suspicious" size="xs">{severity}</Badge>;
      case 'low':
      case 'info':
        return <Badge variant="subtle" size="xs">{severity}</Badge>;
      default:
        return <Badge variant="unknown" size="xs">{severity}</Badge>;
    }
  };

  return (
    <Card pixelFrame className="p-6 sm:p-8 space-y-6">
      <div className="space-y-1 pb-4 border-b border-[#222222]">
        <div className="flex items-center space-x-2 text-xs font-mono text-[#A1A1A1]">
          <Shield className="w-4 h-4 text-[#F5F5F5]" />
          <span className="uppercase tracking-wider">TRANSPARENT REASONING ENGINE</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-light text-[#F5F5F5]">
          Why did TrustGuard AI give this assessment?
        </h2>
        <p className="text-xs text-[#666666] font-mono">
          Full attribution of verified security signals, observed anomalies, and inconclusive feeds.
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[#222222] pb-3 text-xs font-mono">
        <button
          type="button"
          onClick={() => setActiveTab('all')}
          className={`px-3 py-1.5 transition-colors ${
            activeTab === 'all'
              ? 'bg-[#F5F5F5] text-[#080808] font-semibold'
              : 'bg-[#101010] text-[#A1A1A1] hover:text-[#F5F5F5] border border-[#222222]'
          }`}
        >
          ALL FINDINGS ({risks.length + positives.length + unknowns.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('risks')}
          className={`px-3 py-1.5 transition-colors ${
            activeTab === 'risks'
              ? 'bg-[#F5F5F5] text-[#080808] font-semibold'
              : 'bg-[#101010] text-[#A1A1A1] hover:text-[#F5F5F5] border border-[#222222]'
          }`}
        >
          RISK FACTORS ({risks.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('positives')}
          className={`px-3 py-1.5 transition-colors ${
            activeTab === 'positives'
              ? 'bg-[#F5F5F5] text-[#080808] font-semibold'
              : 'bg-[#101010] text-[#A1A1A1] hover:text-[#F5F5F5] border border-[#222222]'
          }`}
        >
          POSITIVE AFFIRMATIONS ({positives.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('unknowns')}
          className={`px-3 py-1.5 transition-colors ${
            activeTab === 'unknowns'
              ? 'bg-[#F5F5F5] text-[#080808] font-semibold'
              : 'bg-[#101010] text-[#A1A1A1] hover:text-[#F5F5F5] border border-[#222222]'
          }`}
        >
          UNAVAILABLE / UNKNOWN ({unknowns.length})
        </button>

        {Object.keys(moduleScores).length > 0 && (
          <button
            type="button"
            onClick={() => setActiveTab('scoring')}
            className={`px-3 py-1.5 transition-colors ${
              activeTab === 'scoring'
                ? 'bg-[#F5F5F5] text-[#080808] font-semibold'
                : 'bg-[#101010] text-[#A1A1A1] hover:text-[#F5F5F5] border border-[#222222]'
            }`}
          >
            SCORE BREAKDOWN
          </button>
        )}
      </div>

      {/* Tab 1: Findings List (All, Risks, Positives, Unknowns) */}
      {activeTab !== 'scoring' && (
        <div className="space-y-3 font-mono text-xs">
          {/* Risk Factors */}
          {(activeTab === 'all' || activeTab === 'risks') &&
            risks.map((item, i) => (
              <div
                key={`risk-${i}`}
                className="p-4 bg-[#141414] border border-[#991B1B]/40 space-y-2 text-[#F5F5F5]"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-[#F87171] shrink-0" />
                    <span className="font-semibold text-sm text-[#F5F5F5]">{item.title}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] text-[#888888] uppercase">{item.source_module}</span>
                    {getSeverityBadge(item.severity)}
                  </div>
                </div>

                <p className="text-xs text-[#A1A1A1] leading-relaxed">{item.description}</p>

                {item.evidence && (
                  <div className="p-2 bg-[#0A0A0A] border border-[#222222] text-[11px] text-[#F87171]">
                    <span className="text-[#666666] select-none">EVIDENCE: </span>
                    <span className="break-all">{item.evidence}</span>
                  </div>
                )}

                {item.explanation && (
                  <p className="text-[11px] text-[#666666] leading-relaxed italic">
                    Reason: {item.explanation}
                  </p>
                )}
              </div>
            ))}

          {/* Positive Affirmations */}
          {(activeTab === 'all' || activeTab === 'positives') &&
            positives.map((item, i) => (
              <div
                key={`pos-${i}`}
                className="p-4 bg-[#141414] border border-[#166534]/40 space-y-2 text-[#F5F5F5]"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-[#4ADE80] shrink-0" />
                    <span className="font-semibold text-sm text-[#F5F5F5]">{item.title}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] text-[#888888] uppercase">{item.source_module}</span>
                    <Badge variant="safe" size="xs">VERIFIED</Badge>
                  </div>
                </div>

                <p className="text-xs text-[#A1A1A1] leading-relaxed">{item.description}</p>

                {item.evidence && (
                  <div className="p-2 bg-[#0A0A0A] border border-[#222222] text-[11px] text-[#4ADE80]">
                    <span className="text-[#666666] select-none">EVIDENCE: </span>
                    <span className="break-all">{item.evidence}</span>
                  </div>
                )}

                {item.explanation && (
                  <p className="text-[11px] text-[#666666] leading-relaxed italic">
                    Reason: {item.explanation}
                  </p>
                )}
              </div>
            ))}

          {/* Unknown / Inconclusive Telemetry */}
          {(activeTab === 'all' || activeTab === 'unknowns') &&
            unknowns.map((item, i) => (
              <div
                key={`unk-${i}`}
                className="p-4 bg-[#141414] border border-[#292929] space-y-2 text-[#A1A1A1]"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <HelpCircle className="w-4 h-4 text-[#666666] shrink-0" />
                    <span className="font-semibold text-sm text-[#F5F5F5]">{item.title}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] text-[#666666] uppercase">{item.source_module}</span>
                    <Badge variant="unknown" size="xs">INCONCLUSIVE</Badge>
                  </div>
                </div>

                <p className="text-xs text-[#888888] leading-relaxed">{item.description}</p>

                {item.explanation && (
                  <p className="text-[11px] text-[#666666] leading-relaxed">
                    Impact: {item.explanation}
                  </p>
                )}
              </div>
            ))}

          {risks.length === 0 && positives.length === 0 && unknowns.length === 0 && (
            <div className="p-8 text-center text-[#666666] font-mono text-xs">
              No detailed indicator breakdown available for this scan operation.
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Score Breakdown Matrix */}
      {activeTab === 'scoring' && (
        <div className="space-y-4 font-mono text-xs">
          <p className="text-[#A1A1A1] leading-relaxed">
            The Digital Trust Score is derived through dynamic multi-factor risk weighting.
            Unavailable modules are excluded from the calculation, and available weights are normalized
            without granting artificial security bonuses.
          </p>

          <div className="overflow-x-auto border border-[#222222]">
            <table className="w-full text-left">
              <thead className="bg-[#101010] text-[#666666] text-[11px] border-b border-[#222222]">
                <tr>
                  <th className="py-2.5 px-3">INSPECTION MODULE</th>
                  <th className="py-2.5 px-3">STATUS</th>
                  <th className="py-2.5 px-3">BASE WEIGHT</th>
                  <th className="py-2.5 px-3">RAW SUBSCORE</th>
                  <th className="py-2.5 px-3">NORMALIZED RISK</th>
                  <th className="py-2.5 px-3">INCLUDED IN SCORE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F1F1F] text-[#F5F5F5]">
                {Object.entries(moduleScores).map(([key, mod]: [string, any]) => (
                  <tr key={key} className="hover:bg-[#121212] transition-colors">
                    <td className="py-2.5 px-3 font-semibold uppercase">{mod.module_name || key}</td>
                    <td className="py-2.5 px-3 text-[11px] text-[#A1A1A1]">{mod.status || 'AVAILABLE'}</td>
                    <td className="py-2.5 px-3">
                      {mod.weight !== undefined ? `${Math.round(mod.weight * 100)}%` : 'N/A'}
                    </td>
                    <td className="py-2.5 px-3">
                      {mod.raw_subscore !== null && mod.raw_subscore !== undefined
                        ? `${mod.raw_subscore}/100`
                        : '—'}
                    </td>
                    <td className="py-2.5 px-3">
                      {mod.normalized_risk !== null && mod.normalized_risk !== undefined ? (
                        <span
                          className={
                            mod.normalized_risk >= 70
                              ? 'text-[#F87171] font-bold'
                              : mod.normalized_risk >= 30
                              ? 'text-[#FBBF24]'
                              : 'text-[#4ADE80]'
                          }
                        >
                          {mod.normalized_risk.toFixed(1)} / 100
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="py-2.5 px-3">
                      {mod.included_in_calculation ? (
                        <span className="text-[#4ADE80]">YES</span>
                      ) : (
                        <span className="text-[#888888]">EXCLUDED</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Card>
  );
};
