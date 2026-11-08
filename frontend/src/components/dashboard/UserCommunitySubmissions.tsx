import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  ArrowRight,
  ExternalLink,
  Plus,
  Clock,
  ThumbsUp,
  AlertCircle,
  CheckCircle2,
  XCircle,
  FileQuestion,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Skeleton } from '../common/Skeleton';
import { CommunityReportUserItem } from '../../types/community';

interface UserCommunitySubmissionsProps {
  reports: CommunityReportUserItem[];
  totalReports: number;
  isLoading: boolean;
}

export const UserCommunitySubmissions: React.FC<UserCommunitySubmissionsProps> = ({
  reports,
  totalReports,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <Card pixelFrame className="p-5 md:p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#222222]">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-4 w-28" />
        </div>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="p-3 bg-[#101010] border border-[#222222] flex items-center justify-between"
            >
              <div className="space-y-2">
                <Skeleton className="h-4 w-56" />
                <Skeleton className="h-3 w-32" />
              </div>
              <Skeleton className="h-6 w-20" />
            </div>
          ))}
        </div>
      </Card>
    );
  }

  // Calculate quick summary metrics from reports
  const underReviewCount = reports.filter(
    (r) =>
      r.moderation_status === 'PENDING' ||
      r.moderation_status === 'UNDER_REVIEW' ||
      r.moderation_status?.toLowerCase().includes('pending')
  ).length;

  const verifiedCount = reports.filter(
    (r) =>
      r.moderation_status === 'APPROVED' ||
      r.moderation_status === 'VERIFIED' ||
      r.verification_status === 'ADMIN_VERIFIED' ||
      r.verification_status === 'COMMUNITY_SUPPORTED'
  ).length;

  const resolvedCount = reports.filter(
    (r) => r.moderation_status === 'RESOLVED' || r.moderation_status === 'resolved'
  ).length;

  const getStatusBadge = (status: string) => {
    const s = (status || '').toUpperCase();
    switch (s) {
      case 'APPROVED':
      case 'VERIFIED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono uppercase bg-[#142918] text-[#4ADE80] border border-[#4ADE80]/30">
            <CheckCircle2 className="w-3 h-3 text-[#4ADE80]" />
            VERIFIED
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono uppercase bg-[#10243E] text-[#60A5FA] border border-[#60A5FA]/30">
            <CheckCircle2 className="w-3 h-3 text-[#60A5FA]" />
            RESOLVED
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono uppercase bg-[#2C1515] text-[#F87171] border border-[#F87171]/30">
            <XCircle className="w-3 h-3 text-[#F87171]" />
            REJECTED
          </span>
        );
      case 'UNDER_REVIEW':
      case 'PENDING':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono uppercase bg-[#2C2411] text-[#FBBF24] border border-[#FBBF24]/30">
            <AlertCircle className="w-3 h-3 text-[#FBBF24]" />
            UNDER REVIEW
          </span>
        );
    }
  };

  return (
    <Card pixelFrame className="p-5 md:p-6 space-y-4 font-mono">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#222222] gap-3">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-[#FBBF24]" />
          <div>
            <h3 className="text-xs font-semibold uppercase text-[#F5F5F5] tracking-wide">
              COMMUNITY THREAT SUBMISSIONS & STATUS
            </h3>
            <span className="text-[11px] text-[#666666]">
              CONTRIBUTIONS TO DISTRIBUTED THREAT RADAR
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {totalReports > 0 && (
            <Link to="/community/my-reports">
              <Button
                variant="secondary"
                size="sm"
                rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
              >
                MY REPORTS ({totalReports})
              </Button>
            </Link>
          )}
          <Link to="/community/report">
            <Button variant="primary" size="sm" leftIcon={<Plus className="w-3.5 h-3.5" />}>
              REPORT THREAT
            </Button>
          </Link>
        </div>
      </div>

      {/* Summary Counter Pills */}
      {totalReports > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <div className="p-2.5 bg-[#101010] border border-[#222222] flex flex-col justify-between">
            <span className="text-[10px] text-[#888888] uppercase">SUBMISSIONS</span>
            <span className="text-sm font-bold text-[#F5F5F5] mt-1">{totalReports}</span>
          </div>
          <div className="p-2.5 bg-[#101010] border border-[#222222] flex flex-col justify-between">
            <span className="text-[10px] text-[#FBBF24] uppercase">UNDER REVIEW</span>
            <span className="text-sm font-bold text-[#FBBF24] mt-1">{underReviewCount}</span>
          </div>
          <div className="p-2.5 bg-[#101010] border border-[#222222] flex flex-col justify-between">
            <span className="text-[10px] text-[#4ADE80] uppercase">VERIFIED</span>
            <span className="text-sm font-bold text-[#4ADE80] mt-1">{verifiedCount}</span>
          </div>
          <div className="p-2.5 bg-[#101010] border border-[#222222] flex flex-col justify-between">
            <span className="text-[10px] text-[#60A5FA] uppercase">RESOLVED</span>
            <span className="text-sm font-bold text-[#60A5FA] mt-1">{resolvedCount}</span>
          </div>
        </div>
      )}

      {/* Content List or Empty State */}
      {reports.length === 0 ? (
        <div className="p-6 md:p-8 bg-[#101010] border border-[#222222] text-center space-y-3">
          <FileQuestion className="w-8 h-8 text-[#555555] mx-auto" />
          <div className="space-y-1">
            <p className="text-xs font-semibold text-[#A1A1A1] uppercase">
              NO THREAT REPORTS SUBMITTED YET
            </p>
            <p className="text-[11px] text-[#666666] max-w-md mx-auto">
              Help protect the community by submitting suspicious domains, phishing kits, or scam
              URLs to our decentralized threat intelligence database.
            </p>
          </div>
          <div className="pt-2">
            <Link to="/community/report">
              <Button variant="secondary" size="sm" leftIcon={<Plus className="w-3.5 h-3.5" />}>
                SUBMIT YOUR FIRST THREAT REPORT
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {reports.slice(0, 5).map((report) => {
            const formattedDate = new Date(report.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            });

            return (
              <div
                key={report.id}
                className="p-3 bg-[#101010] border border-[#222222] hover:border-[#333333] transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1.5 min-w-0 flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-[#F5F5F5] truncate max-w-[280px] sm:max-w-md md:max-w-lg">
                      {report.submitted_url}
                    </span>
                    <Badge variant="outline" size="sm" className="shrink-0 text-[10px]">
                      {report.category}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-3 text-[11px] text-[#666666]">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-[#666666]" />
                      <span>{formattedDate}</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <ThumbsUp className="w-3 h-3 text-[#666666]" />
                      <span>{report.upvotes || 0} confirmations</span>
                    </span>
                    {report.domain && (
                      <span className="text-[#888888] truncate hidden md:inline">
                        domain: {report.domain}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2.5 shrink-0">
                  {getStatusBadge(report.moderation_status)}
                  <Link
                    to={`/community?search=${encodeURIComponent(report.domain || report.submitted_url)}`}
                  >
                    <Button
                      variant="ghost"
                      size="sm"
                      className="px-2"
                      title="View in Community Feed"
                    >
                      <ExternalLink className="w-3.5 h-3.5 text-[#888888]" />
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
