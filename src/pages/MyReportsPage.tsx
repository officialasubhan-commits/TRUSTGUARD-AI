import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  ShieldCheck,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  ExternalLink,
  Search,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  FileQuestion,
} from 'lucide-react';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Skeleton } from '../components/common/Skeleton';
import { communityService } from '../services/communityService';
import { CommunityReportUserItem, PaginatedCommunityResponse } from '../types/community';
import { formatApiError } from '../services/api';

export const MyReportsPage: React.FC = () => {
  const [reportsData, setReportsData] = useState<PaginatedCommunityResponse<CommunityReportUserItem> | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const pageSize = 10;

  const fetchMyReports = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await communityService.getMyReports(currentPage, pageSize);
      setReportsData(data);
    } catch (err: any) {
      setErrorMessage(formatApiError(err).message);
    } finally {
      setIsLoading(false);
    }
  }, [currentPage]);

  useEffect(() => {
    fetchMyReports();
  }, [fetchMyReports]);

  const handleCopyId = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === 'APPROVED' || s === 'VERIFIED') {
      return (
        <Badge variant="safe" size="xs" icon={<CheckCircle2 className="w-3 h-3 text-[#4ADE80]" />}>
          VERIFIED
        </Badge>
      );
    }
    if (s === 'UNDER_REVIEW') {
      return (
        <Badge variant="suspicious" size="xs" icon={<Clock className="w-3 h-3 text-[#FBBF24]" />}>
          UNDER REVIEW
        </Badge>
      );
    }
    if (s === 'RESOLVED') {
      return (
        <Badge variant="outline" size="xs" icon={<ShieldCheck className="w-3 h-3 text-[#F5F5F5]" />}>
          RESOLVED
        </Badge>
      );
    }
    if (s === 'REJECTED') {
      return (
        <Badge variant="malicious" size="xs" icon={<XCircle className="w-3 h-3 text-[#F87171]" />}>
          REJECTED
        </Badge>
      );
    }
    return (
      <Badge variant="subtle" size="xs" icon={<Clock className="w-3 h-3 text-[#888888]" />}>
        PENDING REVIEW
      </Badge>
    );
  };

  const totalPages = reportsData?.total_pages || 0;
  const totalItems = reportsData?.total || 0;
  const items = reportsData?.items || [];

  return (
    <div className="flex-1 py-8 md:py-12 animate-fade-in font-mono">
      <Container size="xl">
        <div className="space-y-6">
          {/* Back Nav */}
          <Link
            to="/community"
            className="inline-flex items-center space-x-2 text-xs text-[#888888] hover:text-[#F5F5F5] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>BACK TO COMMUNITY FEED</span>
          </Link>

          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#222222]">
            <div className="space-y-1">
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#F5F5F5] uppercase">
                My Threat Submissions
              </h1>
              <p className="text-xs text-[#888888]">
                TRACK SUBMITTED THREAT INTELLIGENCE & REVIEWER MODERATION DECISIONS
              </p>
            </div>

            <Link to="/community/report">
              <Button variant="primary" size="sm" leftIcon={<Plus className="w-4 h-4" />}>
                SUBMIT NEW THREAT
              </Button>
            </Link>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="p-4 bg-[#1C1212] border border-[#F87171]/40 flex items-center justify-between gap-3 text-xs text-[#FCA5A5]">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-[#F87171] shrink-0" />
                <span>{errorMessage}</span>
              </div>
              <Button size="sm" variant="secondary" onClick={() => fetchMyReports()}>
                RETRY
              </Button>
            </div>
          )}

          {/* Table / List Container */}
          <Card pixelFrame className="p-0 overflow-hidden bg-[#101010] border border-[#292929]">
            {isLoading ? (
              <div className="p-6 space-y-4">
                {[1, 2, 3].map((n) => (
                  <div key={n} className="space-y-2 pb-4 border-b border-[#1A1A1A]">
                    <Skeleton className="h-5 w-40" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                ))}
              </div>
            ) : items.length === 0 ? (
              <div className="py-16 flex flex-col items-center justify-center space-y-3 text-center p-6">
                <FileQuestion className="w-8 h-8 text-[#555555]" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold uppercase text-[#F5F5F5]">
                    No Threat Reports Submitted
                  </h4>
                  <p className="text-xs text-[#888888] max-w-sm">
                    You have not submitted any website threat reports yet. Report suspicious URLs to
                    protect the TrustGuard AI community.
                  </p>
                </div>
                <Link to="/community/report">
                  <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
                    SUBMIT FIRST REPORT
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[#0A0A0A] border-b border-[#222222] text-[#666666] select-none">
                    <tr>
                      <th className="py-3.5 px-4 font-semibold uppercase">Target Domain & URL</th>
                      <th className="py-3.5 px-4 font-semibold uppercase">Category</th>
                      <th className="py-3.5 px-4 font-semibold uppercase">Submission Date</th>
                      <th className="py-3.5 px-4 font-semibold uppercase">Moderation Status</th>
                      <th className="py-3.5 px-4 font-semibold uppercase">Confirmations</th>
                      <th className="py-3.5 px-4 font-semibold uppercase text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1A1A1A]">
                    {items.map((rep) => {
                      const createdDate = new Date(rep.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      });

                      return (
                        <tr key={rep.id} className="hover:bg-[#121212] transition-colors">
                          {/* Domain & URL */}
                          <td className="py-3.5 px-4 max-w-xs sm:max-w-md">
                            <div className="space-y-1">
                              <span className="font-semibold text-[#F5F5F5] block truncate">
                                {rep.domain || rep.normalized_url}
                              </span>
                              <span className="text-[11px] text-[#666666] block truncate">
                                {rep.submitted_url}
                              </span>
                              <div className="flex items-center space-x-1.5 text-[10px] text-[#555555]">
                                <span>ID:</span>
                                <span className="font-mono">{rep.id.slice(0, 8)}...</span>
                                <button
                                  onClick={() => handleCopyId(rep.id)}
                                  className="text-[#888888] hover:text-[#F5F5F5] transition-colors"
                                  title="Copy full Report ID"
                                >
                                  {copiedId === rep.id ? (
                                    <Check className="w-3 h-3 text-[#4ADE80]" />
                                  ) : (
                                    <Copy className="w-3 h-3" />
                                  )}
                                </button>
                              </div>
                            </div>
                          </td>

                          {/* Threat Category */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <Badge variant="subtle" size="xs">
                              {rep.category.replace(/_/g, ' ')}
                            </Badge>
                          </td>

                          {/* Submission Date */}
                          <td className="py-3.5 px-4 whitespace-nowrap text-[#888888]">
                            {createdDate}
                          </td>

                          {/* Moderation Status */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <div className="space-y-1">
                              {getStatusBadge(rep.moderation_status)}
                              {rep.moderation_notes && (
                                <div className="p-2 bg-[#141414] border border-[#222222] text-[10.5px] text-[#A1A1A1] max-w-xs flex items-start space-x-1.5">
                                  <MessageSquare className="w-3 h-3 text-[#A1A1A1] shrink-0 mt-0.5" />
                                  <span>{rep.moderation_notes}</span>
                                </div>
                              )}
                            </div>
                          </td>

                          {/* Confirmations */}
                          <td className="py-3.5 px-4 whitespace-nowrap text-[#F5F5F5] font-semibold">
                            {rep.upvotes}
                          </td>

                          {/* Actions */}
                          <td className="py-3.5 px-4 text-right whitespace-nowrap">
                            <div className="flex items-center justify-end space-x-2">
                              {rep.scan_id ? (
                                <Link to={`/report/${rep.scan_id}`}>
                                  <Button
                                    variant="secondary"
                                    size="sm"
                                    rightIcon={<ExternalLink className="w-3 h-3" />}
                                  >
                                    REPORT
                                  </Button>
                                </Link>
                              ) : (
                                <Link to={`/scan?url=${encodeURIComponent(rep.submitted_url)}`}>
                                  <Button
                                    variant="secondary"
                                    size="sm"
                                    rightIcon={<Search className="w-3 h-3" />}
                                  >
                                    SCAN
                                  </Button>
                                </Link>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination Toolbar */}
            {totalPages > 1 && (
              <div className="p-4 bg-[#0A0A0A] border-t border-[#222222] flex items-center justify-between text-xs text-[#888888]">
                <span>
                  Showing {Math.min((currentPage - 1) * pageSize + 1, totalItems)} to{' '}
                  {Math.min(currentPage * pageSize, totalItems)} of {totalItems} total submissions
                </span>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage <= 1 || isLoading}
                    leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
                  >
                    PREV
                  </Button>
                  <span className="px-2 text-[#F5F5F5] font-semibold">
                    {currentPage} / {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage >= totalPages || isLoading}
                    rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
                  >
                    NEXT
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      </Container>
    </div>
  );
};

export default MyReportsPage;
