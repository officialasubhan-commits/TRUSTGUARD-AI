import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus,
  Search,
  RotateCcw,
  UserCheck,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Radio,
  FileQuestion,
} from 'lucide-react';
import { Container } from '../components/common/Container';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Skeleton } from '../components/common/Skeleton';
import {
  CommunityStatisticsCards,
  CommunityReportCard,
} from '../components/community';
import { communityService } from '../services/communityService';
import {
  CommunityReportItem,
  CommunityStatistics,
  PaginatedCommunityResponse,
} from '../types/community';
import { formatApiError } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const CommunityPage: React.FC = () => {
  const { isAuthenticated } = useAuth();

  // Telemetry & Feed State
  const [statistics, setStatistics] = useState<CommunityStatistics | null>(null);
  const [reportsData, setReportsData] = useState<PaginatedCommunityResponse<CommunityReportItem> | null>(null);
  const [isStatsLoading, setIsStatsLoading] = useState<boolean>(true);
  const [isFeedLoading, setIsFeedLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Filters State
  const [searchInput, setSearchInput] = useState<string>('');
  const [appliedSearch, setAppliedSearch] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'newest' | 'most_confirmed'>('newest');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 10;

  const abortControllerRef = useRef<AbortController | null>(null);

  // Debounced search input handler
  useEffect(() => {
    const handler = setTimeout(() => {
      setAppliedSearch(searchInput.trim());
      setCurrentPage(1);
    }, 350);
    return () => clearTimeout(handler);
  }, [searchInput]);

  // Fetch Community Overview Statistics
  const fetchStatistics = useCallback(async () => {
    setIsStatsLoading(true);
    try {
      const stats = await communityService.getStatistics();
      setStatistics(stats);
    } catch (err) {
      console.warn('Could not load community statistics:', err);
    } finally {
      setIsStatsLoading(false);
    }
  }, []);

  // Fetch Community Reports Feed
  const fetchReports = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setIsFeedLoading(true);
    setErrorMessage(null);

    try {
      const res = await communityService.getReports(
        {
          search: appliedSearch || undefined,
          category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
          status: selectedStatus !== 'ALL' ? selectedStatus : undefined,
          sort_by: sortBy,
          page: currentPage,
          page_size: pageSize,
        },
        abortControllerRef.current.signal
      );
      setReportsData(res);
    } catch (err: any) {
      if (err.name === 'CanceledError' || err.name === 'AbortError') return;
      setErrorMessage(formatApiError(err).message);
    } finally {
      setIsFeedLoading(false);
    }
  }, [appliedSearch, selectedCategory, selectedStatus, sortBy, currentPage]);

  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const handleClearFilters = () => {
    setSearchInput('');
    setAppliedSearch('');
    setSelectedCategory('ALL');
    setSelectedStatus('ALL');
    setSortBy('newest');
    setCurrentPage(1);
  };

  const categories = [
    { id: 'ALL', label: 'All Threats' },
    { id: 'PHISHING', label: 'Phishing' },
    { id: 'MALWARE_DISTRIBUTION', label: 'Malware' },
    { id: 'FRAUD_OR_SCAM', label: 'Scam / Fraud' },
    { id: 'SUSPICIOUS_REDIRECT', label: 'Redirects' },
    { id: 'IMPERSONATION', label: 'Impersonation' },
    { id: 'OTHER', label: 'Other' },
  ];

  const statuses = [
    { id: 'ALL', label: 'All Statuses' },
    { id: 'VERIFIED', label: 'Verified' },
    { id: 'UNDER_REVIEW', label: 'Under Review' },
    { id: 'RESOLVED', label: 'Resolved' },
    { id: 'REJECTED', label: 'Rejected' },
  ];

  const totalPages = reportsData?.total_pages || 0;
  const totalItems = reportsData?.total || 0;
  const items = reportsData?.items || [];
  const hasActiveFilters =
    appliedSearch !== '' || selectedCategory !== 'ALL' || selectedStatus !== 'ALL' || sortBy !== 'newest';

  return (
    <div className="flex-1 py-8 md:py-12 animate-fade-in font-mono">
      <Container size="xl">
        <div className="space-y-8">
          {/* Header & Quick Actions */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#222222]">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <Radio className="w-4 h-4 text-[#4ADE80] animate-pulse" />
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#F5F5F5] uppercase">
                  Community Threat Intelligence
                </h1>
              </div>
              <p className="text-xs text-[#888888]">
                COLLABORATIVE REPUTATION CONSENSUS & DECENTRALIZED THREAT ANNOTATIONS
              </p>
            </div>

            <div className="flex items-center space-x-2.5">
              {isAuthenticated && (
                <Link to="/community/my-reports">
                  <Button variant="secondary" size="sm" leftIcon={<UserCheck className="w-3.5 h-3.5" />}>
                    MY REPORTS
                  </Button>
                </Link>
              )}
              <Link to="/community/report">
                <Button variant="primary" size="sm" leftIcon={<Plus className="w-4 h-4" />}>
                  REPORT SUSPICIOUS URL
                </Button>
              </Link>
            </div>
          </div>

          {/* Overview Statistics */}
          <CommunityStatisticsCards statistics={statistics} isLoading={isStatsLoading} />

          {/* Filter & Search Bar */}
          <div className="p-4 bg-[#101010] border border-[#222222] space-y-4 text-xs">
            {/* Search and Sort Row */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1">
                <Input
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="SEARCH TARGET DOMAIN, URL, OR IMPERSONATED BRAND..."
                  leftElement={<Search className="w-4 h-4 text-[#666666]" />}
                  size="sm"
                />
              </div>

              <div className="flex items-center space-x-2 shrink-0">
                <span className="text-[#666666] uppercase text-[11px]">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => {
                    setSortBy(e.target.value as 'newest' | 'most_confirmed');
                    setCurrentPage(1);
                  }}
                  className="bg-[#141414] border border-[#292929] text-xs font-mono text-[#F5F5F5] h-8 px-2.5 outline-none focus:border-[#F5F5F5]"
                >
                  <option value="newest">Newest Submissions</option>
                  <option value="most_confirmed">Most Confirmed</option>
                </select>

                {hasActiveFilters && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearFilters}
                    leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                  >
                    RESET
                  </Button>
                )}
              </div>
            </div>

            {/* Category Filter Pills */}
            <div className="space-y-1.5 pt-1 border-t border-[#1C1C1C]">
              <span className="text-[10px] text-[#666666] uppercase block">
                Threat Classification
              </span>
              <div className="flex flex-wrap gap-1.5">
                {categories.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => {
                      setSelectedCategory(cat.id);
                      setCurrentPage(1);
                    }}
                    className={`px-2.5 py-1 text-[11px] border transition-colors uppercase ${
                      selectedCategory === cat.id
                        ? 'bg-[#F5F5F5] text-[#080808] border-[#F5F5F5] font-bold'
                        : 'bg-[#141414] text-[#888888] border-[#292929] hover:text-[#F5F5F5] hover:border-[#444444]'
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Status Filter Pills */}
            <div className="space-y-1.5 pt-1 border-t border-[#1C1C1C]">
              <span className="text-[10px] text-[#666666] uppercase block">
                Moderation Status
              </span>
              <div className="flex flex-wrap gap-1.5">
                {statuses.map((st) => (
                  <button
                    key={st.id}
                    onClick={() => {
                      setSelectedStatus(st.id);
                      setCurrentPage(1);
                    }}
                    className={`px-2.5 py-1 text-[11px] border transition-colors uppercase ${
                      selectedStatus === st.id
                        ? 'bg-[#F5F5F5] text-[#080808] border-[#F5F5F5] font-bold'
                        : 'bg-[#141414] text-[#888888] border-[#292929] hover:text-[#F5F5F5] hover:border-[#444444]'
                    }`}
                  >
                    {st.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="p-4 bg-[#1C1212] border border-[#F87171]/40 flex items-center justify-between gap-3 text-xs font-mono text-[#FCA5A5]">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-[#F87171] shrink-0" />
                <span>{errorMessage}</span>
              </div>
              <Button size="sm" variant="secondary" onClick={() => fetchReports()}>
                RETRY
              </Button>
            </div>
          )}

          {/* Threat Feed List */}
          <div className="space-y-3.5">
            {isFeedLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((n) => (
                  <div key={n} className="p-5 bg-[#101010] border border-[#222222] space-y-3">
                    <div className="flex justify-between items-center">
                      <Skeleton className="h-5 w-28" />
                      <Skeleton className="h-4 w-32" />
                    </div>
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-12 w-full" />
                  </div>
                ))}
              </div>
            ) : items.length === 0 ? (
              <div className="py-16 bg-[#101010] border border-dashed border-[#222222] flex flex-col items-center justify-center space-y-3 text-center p-6">
                <FileQuestion className="w-8 h-8 text-[#555555]" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold uppercase text-[#F5F5F5]">
                    No Threat Reports Found
                  </h4>
                  <p className="text-xs text-[#888888] max-w-sm">
                    {hasActiveFilters
                      ? 'No community submissions match your active filter criteria. Try resetting your search or filter selections.'
                      : 'No public threat submissions are currently listed. Submit the first community report to flag suspicious websites.'}
                  </p>
                </div>
                {hasActiveFilters ? (
                  <Button size="sm" variant="secondary" onClick={handleClearFilters}>
                    CLEAR ALL FILTERS
                  </Button>
                ) : (
                  <Link to="/community/report">
                    <Button size="sm" variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
                      SUBMIT FIRST REPORT
                    </Button>
                  </Link>
                )}
              </div>
            ) : (
              items.map((report) => (
                <CommunityReportCard
                  key={report.id}
                  report={report}
                  onRefresh={fetchReports}
                />
              ))
            )}
          </div>

          {/* Pagination Toolbar */}
          {totalPages > 1 && (
            <div className="p-4 bg-[#101010] border border-[#222222] flex items-center justify-between text-xs text-[#888888]">
              <span>
                Showing {Math.min((currentPage - 1) * pageSize + 1, totalItems)} to{' '}
                {Math.min(currentPage * pageSize, totalItems)} of {totalItems} reports
              </span>

              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage <= 1 || isFeedLoading}
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
                  disabled={currentPage >= totalPages || isFeedLoading}
                  rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
                >
                  NEXT
                </Button>
              </div>
            </div>
          )}
        </div>
      </Container>
    </div>
  );
};

export default CommunityPage;
