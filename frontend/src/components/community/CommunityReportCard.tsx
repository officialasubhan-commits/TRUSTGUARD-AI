import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ThumbsUp,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Flag,
  Cpu,
  ExternalLink,
  Search,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { CommunityReportItem } from '../../types/community';
import { communityService } from '../../services/communityService';
import { useAuth } from '../../context/AuthContext';
import { Web3IntegrityModal } from './Web3IntegrityModal';
import { FlagReportModal } from './FlagReportModal';

interface CommunityReportCardProps {
  report: CommunityReportItem;
  onRefresh?: () => void;
}

export const CommunityReportCard: React.FC<CommunityReportCardProps> = ({
  report,
  onRefresh,
}) => {
  const { isAuthenticated } = useAuth();
  const [upvotes, setUpvotes] = useState<number>(report.upvotes || 0);
  const [isConfirmed, setIsConfirmed] = useState<boolean>(!!report.user_confirmed);
  const [isToggling, setIsToggling] = useState<boolean>(false);
  const [isWeb3Open, setIsWeb3Open] = useState<boolean>(false);
  const [isFlagOpen, setIsFlagOpen] = useState<boolean>(false);

  const formattedDate = new Date(report.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  const handleToggleConfirm = async () => {
    if (!isAuthenticated) {
      window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      return;
    }

    setIsToggling(true);
    try {
      const res = await communityService.toggleConfirmation(report.id);
      setIsConfirmed(res.confirmed);
      setUpvotes(res.total_confirmations);
    } catch (err) {
      console.error('Failed to toggle confirmation:', err);
    } finally {
      setIsToggling(false);
    }
  };

  const getCategoryBadgeVariant = (cat: string) => {
    const c = cat.toUpperCase();
    if (c.includes('PHISH')) return 'malicious';
    if (c.includes('MALWARE')) return 'malicious';
    if (c.includes('SCAM') || c.includes('FRAUD')) return 'suspicious';
    return 'default';
  };

  const getModerationBadgeVariant = (status: string) => {
    const s = status.toUpperCase();
    if (s === 'APPROVED' || s === 'VERIFIED') return 'safe';
    if (s === 'UNDER_REVIEW' || s === 'PENDING') return 'suspicious';
    if (s === 'RESOLVED') return 'outline';
    if (s === 'REJECTED') return 'malicious';
    return 'subtle';
  };

  return (
    <Card hoverEffect className="p-4 sm:p-5 bg-[#101010] border border-[#222222] space-y-4 font-mono text-xs">
      {/* Card Header: Category & Moderation Badges */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <Badge variant={getCategoryBadgeVariant(report.category)} size="xs">
            {report.category.replace(/_/g, ' ')}
          </Badge>
          <Badge variant={getModerationBadgeVariant(report.moderation_status)} size="xs">
            {report.moderation_status.replace(/_/g, ' ')}
          </Badge>
        </div>

        <div className="flex items-center space-x-2 text-[11px] text-[#666666]">
          {report.verification_status === 'ADMIN_VERIFIED' ? (
            <span className="flex items-center space-x-1 text-[#4ADE80]">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>ADMIN VERIFIED</span>
            </span>
          ) : report.verification_status === 'COMMUNITY_SUPPORTED' ? (
            <span className="flex items-center space-x-1 text-[#FBBF24]">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>COMMUNITY CONSENSUS</span>
            </span>
          ) : (
            <span className="flex items-center space-x-1 text-[#888888]">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>UNVERIFIED CLAIM</span>
            </span>
          )}
          <span>•</span>
          <span>{formattedDate}</span>
        </div>
      </div>

      {/* Target Domain & URL */}
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-2">
          <h3 className="font-semibold text-sm sm:text-base text-[#F5F5F5] break-all">
            {report.domain || report.normalized_url}
          </h3>
          {report.target_brand && (
            <Badge variant="subtle" size="xs">
              IMPERSONATING: {report.target_brand}
            </Badge>
          )}
        </div>
        <p className="text-[11px] text-[#666666] truncate max-w-xl">
          {report.submitted_url}
        </p>
      </div>

      {/* Description / Threat Indicators */}
      {report.description && (
        <div className="p-3 bg-[#0A0A0A] border border-[#1A1A1A] text-[#A1A1A1] text-xs leading-relaxed break-words">
          {report.description}
        </div>
      )}

      {/* Action Toolbar */}
      <div className="pt-2 border-t border-[#1F1F1F] flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Left: Community Confirmations & Flag */}
        <div className="flex items-center space-x-2">
          <Button
            variant={isConfirmed ? 'primary' : 'secondary'}
            size="sm"
            onClick={handleToggleConfirm}
            isLoading={isToggling}
            leftIcon={<ThumbsUp className={`w-3.5 h-3.5 ${isConfirmed ? 'text-[#080808]' : ''}`} />}
            title={isAuthenticated ? 'Confirm or withdraw independent observation' : 'Sign in to confirm'}
          >
            {isConfirmed ? 'CONFIRMED' : 'CONFIRM'} ({upvotes})
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              if (!isAuthenticated) {
                window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
                return;
              }
              setIsFlagOpen(true);
            }}
            title="Flag inaccurate or abusive report"
            leftIcon={<Flag className="w-3 h-3 text-[#888888]" />}
          >
            FLAG
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsWeb3Open(true)}
            leftIcon={<Cpu className="w-3 h-3 text-[#A1A1A1]" />}
            title="Inspect cryptographic Web3 record integrity proof"
          >
            INTEGRITY
          </Button>
        </div>

        {/* Right: Security Audit Link */}
        <div className="flex items-center space-x-2">
          {report.scan_id ? (
            <Link to={`/report/${report.scan_id}`}>
              <Button
                variant="secondary"
                size="sm"
                rightIcon={<ExternalLink className="w-3.5 h-3.5" />}
              >
                SECURITY REPORT
              </Button>
            </Link>
          ) : (
            <Link to={`/scan?url=${encodeURIComponent(report.submitted_url)}`}>
              <Button
                variant="secondary"
                size="sm"
                rightIcon={<Search className="w-3.5 h-3.5" />}
              >
                SCAN URL
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Modals */}
      <Web3IntegrityModal
        reportId={report.id}
        isOpen={isWeb3Open}
        onClose={() => setIsWeb3Open(false)}
      />

      <FlagReportModal
        reportId={report.id}
        domain={report.domain}
        isOpen={isFlagOpen}
        onClose={() => setIsFlagOpen(false)}
        onSuccess={onRefresh}
      />
    </Card>
  );
};

export default CommunityReportCard;

