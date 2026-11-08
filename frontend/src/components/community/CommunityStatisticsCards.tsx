import React from 'react';
import {
  FileText,
  Clock,
  ShieldAlert,
  CheckCircle2,
  Users,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Skeleton } from '../common/Skeleton';
import { CommunityStatistics } from '../../types/community';

interface CommunityStatisticsCardsProps {
  statistics: CommunityStatistics | null;
  isLoading: boolean;
}

export const CommunityStatisticsCards: React.FC<CommunityStatisticsCardsProps> = ({
  statistics,
  isLoading,
}) => {
  const cards = [
    {
      id: 'total',
      label: 'Total Reports',
      subtext: 'COMMUNITY SUBMISSIONS',
      value: statistics?.total_reports ?? 0,
      icon: <FileText className="w-4 h-4 text-[#F5F5F5]" />,
    },
    {
      id: 'pending',
      label: 'Awaiting Review',
      subtext: 'PENDING MODERATION',
      value: statistics?.pending_review ?? 0,
      icon: <Clock className="w-4 h-4 text-[#FBBF24]" />,
    },
    {
      id: 'verified',
      label: 'Verified Threats',
      subtext: 'ADMIN CONFIRMED',
      value: statistics?.verified_reports ?? 0,
      icon: <ShieldAlert className="w-4 h-4 text-[#F87171]" />,
    },
    {
      id: 'resolved',
      label: 'Resolved Reports',
      subtext: 'TAKEDOWN / REMEDIATED',
      value: statistics?.resolved_reports ?? 0,
      icon: <CheckCircle2 className="w-4 h-4 text-[#4ADE80]" />,
    },
    {
      id: 'confirmations',
      label: 'Active Confirmations',
      subtext: 'COMMUNITY CONSENSUS',
      value: statistics?.active_confirmations ?? 0,
      icon: <Users className="w-4 h-4 text-[#A1A1A1]" />,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
      {cards.map((card) => (
        <Card key={card.id} className="p-4 bg-[#101010] border border-[#222222] space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-[#888888] uppercase tracking-wider text-[11px] truncate">
              {card.label}
            </span>
            <div className="p-1 bg-[#161616] border border-[#292929]">{card.icon}</div>
          </div>

          <div className="space-y-0.5">
            {isLoading ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <div className="text-xl sm:text-2xl font-mono font-bold text-[#F5F5F5]">
                {card.value.toLocaleString()}
              </div>
            )}
            <span className="text-[10px] font-mono text-[#555555] block truncate">
              {card.subtext}
            </span>
          </div>
        </Card>
      ))}
    </div>
  );
};

export default CommunityStatisticsCards;

