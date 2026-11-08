import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  RotateCcw,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Clock,
  Trash2,
  X,
  SlidersHorizontal,
  Download,
  CheckCircle2,
  FileText,
} from 'lucide-react';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { Skeleton } from '../components/common/Skeleton';
import { scanService } from '../services/scanService';
import { formatApiError } from '../services/api';
import {
  PaginatedScanHistoryResponse,
  ScanHistoryFilterParams,
  ScanHistorySummary,
} from '../types/scan';

export const HistoryPage: React.FC = () => {
  // Search & Filter State
  const [searchInput, setSearchInput] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'trust_score'>('newest');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  // Data & Lifecycle State
  const [historyData, setHistoryData] = useState<PaginatedScanHistoryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [deletingScanId, setDeletingScanId] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Bulk CSV Export State
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [exportFeedback, setExportFeedback] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Debounced search input handler
  useEffect(() => {
    const handler = setTimeout(() => {
      setAppliedSearch(searchInput.trim());
      setCurrentPage(1); // Reset to page 1 on new search
    }, 350);

    return () => clearTimeout(handler);
  }, [searchInput]);

  const fetchHistory = useCallback(
    async (signal?: AbortSignal) => {
      setIsLoading(true);
      setErrorMessage(null);

      const params: ScanHistoryFilterParams = {
        page: currentPage,
        page_size: pageSize,
      };

      if (appliedSearch) {
        params.search = appliedSearch;
      }

      if (riskFilter !== 'ALL') {
        params.risk_level = riskFilter;
      }

      if (statusFilter !== 'ALL') {
        params.assessment_status = statusFilter.toUpperCase();
      }

      if (sortBy === 'trust_score') {
        params.sort_by = 'trust_score';
        params.sort_order = sortOrder;
      } else if (sortBy === 'oldest') {
        params.sort_by = 'created_at';
        params.sort_order = 'asc';
      } else {
        params.sort_by = 'created_at';
        params.sort_order = 'desc';
      }

      try {
        const response = await scanService.getHistory(params, signal);
        setHistoryData(response);
      } catch (err: any) {
        if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') {
          return;
        }
        const formatted = formatApiError(err);
        setErrorMessage(
          formatted.message || 'Unable to load scan history records from the server.'
        );
      } finally {
        setIsLoading(false);
      }
    },
    [currentPage, pageSize, appliedSearch, riskFilter, statusFilter, sortBy, sortOrder]
  );

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    fetchHistory(controller.signal);

    return () => {
      controller.abort();
    };
  }, [fetchHistory]);

  const handleClearFilters = () => {
    setSearchInput('');
    setAppliedSearch('');
    setRiskFilter('ALL');
    setStatusFilter('ALL');
    setSortBy('newest');
    setSortOrder('desc');
    setCurrentPage(1);
  };

  const handleDeleteScan = async (scanId: string) => {
    setDeletingScanId(scanId);
    try {
      await scanService.deleteScan(scanId);
      setDeleteConfirmId(null);
      // Refresh list
      fetchHistory();
    } catch (err: any) {
      const formatted = formatApiError(err);
      alert(`Deletion failed: ${formatted.message}`);
    } finally {
      setDeletingScanId(null);
    }
  };

  const handleExportCsv = async () => {
    if (isExporting) return;
    setExportFeedback(null);

    // If known to have zero items
    if (historyData && historyData.total_items === 0) {
      setExportFeedback({
        type: 'info',
        message: 'No scan history records available to export. Run a scan to populate your audit dossier.',
      });
      return;
    }

    setIsExporting(true);
    try {
      const { blob, filename } = await scanService.exportHistoryCsv();

      if (blob.size === 0) {
        setExportFeedback({
          type: 'info',
          message: 'No scan history records available to export.',
        });
        return;
      }

      // Create download trigger
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      setExportFeedback({
        type: 'success',
        message: `Scan history successfully exported as ${filename}.`,
      });
      setTimeout(() => setExportFeedback(null), 5000);
    } catch (err: any) {
      const formatted = formatApiError(err);
      setExportFeedback({
        type: 'error',
        message: formatted.message || 'Failed to export scan history CSV. Please verify server connectivity.',
      });
    } finally {
      setIsExporting(false);
    }
  };

  const hasActiveFilters =
    Boolean(appliedSearch) || riskFilter !== 'ALL' || statusFilter !== 'ALL' || sortBy !== 'newest';

  const totalItems = historyData?.total_items ?? 0;
  const totalPages = historyData?.total_pages ?? 0;
  const items = historyData?.items ?? [];

  return (
    <div className="flex-1 py-10 md:py-16 px-4">
      <Container size="xl">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#222222]">
            <div className="space-y-1">
              <h1 className="text-2xl sm:text-3xl font-light tracking-tight text-[#F5F5F5]">
                Scan History & Security Audits
              </h1>
              <p className="text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                PERSISTED THREAT TELEMETRY & AUDIT DOSSIERS
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportCsv}
                leftIcon={<Download className="w-3.5 h-3.5" />}
                isLoading={isExporting}
                disabled={isExporting || isLoading}
                title="Export complete scan history as RFC-4180 CSV"
              >
                {isExporting ? 'EXPORTING...' : 'EXPORT CSV'}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => fetchHistory()}
                leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                disabled={isLoading || isExporting}
              >
                REFRESH
              </Button>
              <Link to="/scan">
                <Button variant="primary" size="sm">
                  NEW SCAN
                </Button>
              </Link>
            </div>
          </div>

          {/* Export Feedback Banner */}
          {exportFeedback && (
            <div
              className={`p-3 border flex items-center justify-between text-xs font-mono ${
                exportFeedback.type === 'success'
                  ? 'bg-[#0F1710] border-[#4ADE80]/30 text-[#4ADE80]'
                  : exportFeedback.type === 'error'
                  ? 'bg-[#1C1212] border-[#F87171]/40 text-[#FCA5A5]'
                  : 'bg-[#141414] border-[#2A2A2A] text-[#A1A1A1]'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                {exportFeedback.type === 'success' && <CheckCircle2 className="w-4 h-4 shrink-0" />}
                {exportFeedback.type === 'error' && (
                  <AlertTriangle className="w-4 h-4 shrink-0 text-[#F87171]" />
                )}
                {exportFeedback.type === 'info' && <FileText className="w-4 h-4 shrink-0" />}
                <span>{exportFeedback.message}</span>
              </div>
              <button
                type="button"
                onClick={() => setExportFeedback(null)}
                className="text-[#666666] hover:text-[#F5F5F5] ml-2"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Search & Filter Toolbar */}
          <Card variant="standard" className="p-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
              {/* Search Bar */}
              <div className="md:col-span-5">
                <Input
                  placeholder="Search past scans by domain or URL..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  leftElement={<Search className="w-4 h-4" />}
                  mono
                  size="sm"
                />
              </div>

              {/* Risk Level Filter */}
              <div className="md:col-span-3 flex items-center space-x-2">
                <label className="text-[11px] font-mono text-[#666666] uppercase whitespace-nowrap">
                  Risk:
                </label>
                <select
                  value={riskFilter}
                  onChange={(e) => {
                    setRiskFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full bg-[#101010] border border-[#292929] text-xs font-mono text-[#F5F5F5] h-8 px-2.5 focus:border-[#F5F5F5] outline-none"
                >
                  <option value="ALL">ALL RISK LEVELS</option>
                  <option value="CRITICAL">CRITICAL RISK</option>
                  <option value="HIGH">HIGH RISK</option>
                  <option value="MEDIUM">MODERATE RISK</option>
                  <option value="LOW">LOW / SAFE</option>
                  <option value="UNKNOWN">UNKNOWN / INCONCLUSIVE</option>
                </select>
              </div>

              {/* Status Filter */}
              <div className="md:col-span-2 flex items-center space-x-2">
                <label className="text-[11px] font-mono text-[#666666] uppercase whitespace-nowrap">
                  Status:
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full bg-[#101010] border border-[#292929] text-xs font-mono text-[#F5F5F5] h-8 px-2.5 focus:border-[#F5F5F5] outline-none"
                >
                  <option value="ALL">ALL STATUSES</option>
                  <option value="COMPLETE">COMPLETED</option>
                  <option value="PROCESSING">PROCESSING</option>
                  <option value="ERROR">FAILED / ERROR</option>
                </select>
              </div>

              {/* Sort Order */}
              <div className="md:col-span-2 flex items-center space-x-2">
                <label className="text-[11px] font-mono text-[#666666] uppercase whitespace-nowrap">
                  Sort:
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => {
                    setSortBy(e.target.value as any);
                    if (e.target.value === 'oldest') {
                      setSortOrder('asc');
                    } else {
                      setSortOrder('desc');
                    }
                    setCurrentPage(1);
                  }}
                  className="w-full bg-[#101010] border border-[#292929] text-xs font-mono text-[#F5F5F5] h-8 px-2.5 focus:border-[#F5F5F5] outline-none"
                >
                  <option value="newest">NEWEST FIRST</option>
                  <option value="oldest">OLDEST FIRST</option>
                  <option value="trust_score">BY TRUST SCORE</option>
                </select>
              </div>
            </div>

            {/* Active Filter Indicators */}
            {hasActiveFilters && (
              <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#1F1F1F] text-xs font-mono">
                <div className="flex flex-wrap items-center gap-1.5 text-[#A1A1A1]">
                  <SlidersHorizontal className="w-3.5 h-3.5 mr-1" />
                  <span>Active Filters:</span>
                  {appliedSearch && (
                    <span className="px-2 py-0.5 bg-[#141414] border border-[#292929] text-[#F5F5F5]">
                      query: "{appliedSearch}"
                    </span>
                  )}
                  {riskFilter !== 'ALL' && (
                    <span className="px-2 py-0.5 bg-[#141414] border border-[#292929] text-[#F5F5F5]">
                      risk: {riskFilter}
                    </span>
                  )}
                  {statusFilter !== 'ALL' && (
                    <span className="px-2 py-0.5 bg-[#141414] border border-[#292929] text-[#F5F5F5]">
                      status: {statusFilter}
                    </span>
                  )}
                  {sortBy !== 'newest' && (
                    <span className="px-2 py-0.5 bg-[#141414] border border-[#292929] text-[#F5F5F5]">
                      sort: {sortBy}
                    </span>
                  )}
                </div>

                <button
                  onClick={handleClearFilters}
                  className="text-xs font-mono text-[#A1A1A1] hover:text-[#F87171] flex items-center space-x-1"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>CLEAR ALL FILTERS</span>
                </button>
              </div>
            )}
          </Card>

          {/* Error Banner */}
          {errorMessage && (
            <div className="p-4 bg-[#1C1212] border border-[#F87171]/40 flex items-center justify-between gap-3 text-xs font-mono text-[#FCA5A5]">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-[#F87171] shrink-0" />
                <span>{errorMessage}</span>
              </div>
              <Button size="sm" variant="secondary" onClick={() => fetchHistory()}>
                RETRY
              </Button>
            </div>
          )}

          {/* Delete Confirmation Modal Overlay */}
          {deleteConfirmId && (
            <div className="p-4 bg-[#141414] border border-[#F87171]/40 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono">
              <div className="flex items-center space-x-2.5 text-[#FCA5A5]">
                <AlertTriangle className="w-4 h-4 text-[#F87171] shrink-0" />
                <span>
                  Permanently delete scan record <span className="text-[#F5F5F5] font-bold">{deleteConfirmId.slice(0, 8)}...</span>? This cannot be undone.
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <Button size="sm" variant="secondary" onClick={() => setDeleteConfirmId(null)}>
                  CANCEL
                </Button>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => handleDeleteScan(deleteConfirmId)}
                  isLoading={deletingScanId === deleteConfirmId}
                >
                  CONFIRM DELETION
                </Button>
              </div>
            </div>
          )}

          {/* Table Container */}
          <Card pixelFrame className="p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#101010] border-b border-[#292929] text-[#666666] select-none">
                  <tr>
                    <th className="py-3.5 px-4 font-semibold uppercase">Target Domain & URL</th>
                    <th className="py-3.5 px-4 font-semibold uppercase">Scan Date</th>
                    <th className="py-3.5 px-4 font-semibold uppercase">Trust Score</th>
                    <th className="py-3.5 px-4 font-semibold uppercase">Risk Level</th>
                    <th className="py-3.5 px-4 font-semibold uppercase">Status</th>
                    <th className="py-3.5 px-4 text-right font-semibold uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#222222] text-[#A1A1A1]">
                  {isLoading ? (
                    Array.from({ length: pageSize }).map((_, idx) => (
                      <tr key={idx}>
                        <td className="py-4 px-4">
                          <Skeleton className="h-4 w-44 mb-1" />
                          <Skeleton className="h-3 w-64" />
                        </td>
                        <td className="py-4 px-4">
                          <Skeleton className="h-3 w-28" />
                        </td>
                        <td className="py-4 px-4">
                          <Skeleton className="h-4 w-16" />
                        </td>
                        <td className="py-4 px-4">
                          <Skeleton className="h-4 w-20" />
                        </td>
                        <td className="py-4 px-4">
                          <Skeleton className="h-4 w-20" />
                        </td>
                        <td className="py-4 px-4 text-right">
                          <Skeleton className="h-7 w-20 ml-auto" />
                        </td>
                      </tr>
                    ))
                  ) : items.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-16 px-4 text-center">
                        <div className="flex flex-col items-center justify-center space-y-3">
                          <Clock className="w-8 h-8 text-[#555555]" />
                          <div className="space-y-1">
                            <h3 className="text-sm font-semibold uppercase text-[#F5F5F5]">
                              {hasActiveFilters ? 'NO MATCHING AUDITS FOUND' : 'NO SCAN HISTORY RECORDED'}
                            </h3>
                            <p className="text-xs text-[#666666] max-w-sm">
                              {hasActiveFilters
                                ? 'No records match your active query and filter criteria. Clear filters to view all entries.'
                                : 'You have not conducted any security scans with this account. Submit a URL to begin automated threat detection.'}
                            </p>
                          </div>
                          {hasActiveFilters ? (
                            <Button size="sm" variant="secondary" onClick={handleClearFilters}>
                              CLEAR FILTERS
                            </Button>
                          ) : (
                            <Link to="/scan">
                              <Button size="sm" variant="primary">
                                RUN FIRST SCAN
                              </Button>
                            </Link>
                          )}
                        </div>
                      </td>
                    </tr>
                  ) : (
                    items.map((scan: ScanHistorySummary) => {
                      const createdDate = new Date(scan.created_at).toLocaleDateString('en-US', {
                        year: 'numeric',
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
                        <tr
                          key={scan.scan_id}
                          className="hover:bg-[#121212] transition-colors group"
                        >
                          {/* Domain & URL */}
                          <td className="py-3.5 px-4">
                            <div className="space-y-0.5">
                              <div className="flex items-center space-x-2">
                                {isThreat ? (
                                  <ShieldAlert className="w-3.5 h-3.5 text-[#F87171] shrink-0" />
                                ) : isSafe ? (
                                  <ShieldCheck className="w-3.5 h-3.5 text-[#4ADE80] shrink-0" />
                                ) : (
                                  <AlertTriangle className="w-3.5 h-3.5 text-[#FBBF24] shrink-0" />
                                )}
                                <span className="font-semibold text-[#F5F5F5] group-hover:underline">
                                  <Link to={`/report/${scan.scan_id}`}>
                                    {scan.domain || scan.normalized_url}
                                  </Link>
                                </span>
                              </div>
                              <p className="text-[11px] text-[#666666] truncate max-w-xs md:max-w-md">
                                {scan.submitted_url}
                              </p>
                            </div>
                          </td>

                          {/* Timestamp */}
                          <td className="py-3.5 px-4 text-[#888888] whitespace-nowrap">
                            {createdDate}
                          </td>

                          {/* Trust Score */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <span
                              className={`font-bold ${
                                scan.digital_trust_score !== null &&
                                scan.digital_trust_score !== undefined
                                  ? scan.digital_trust_score >= 80
                                    ? 'text-[#4ADE80]'
                                    : scan.digital_trust_score >= 50
                                    ? 'text-[#FBBF24]'
                                    : 'text-[#F87171]'
                                  : 'text-[#666666]'
                              }`}
                            >
                              {scan.digital_trust_score !== null &&
                              scan.digital_trust_score !== undefined
                                ? `${scan.digital_trust_score} / 100`
                                : 'N/A'}
                            </span>
                          </td>

                          {/* Risk Classification */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <Badge
                              variant={
                                isThreat
                                  ? 'malicious'
                                  : isSafe
                                  ? 'safe'
                                  : scan.risk_level === 'MEDIUM' || scan.risk_level === 'MODERATE_RISK'
                                  ? 'suspicious'
                                  : 'unknown'
                              }
                              size="xs"
                            >
                              {scan.risk_label || scan.risk_level || 'UNKNOWN'}
                            </Badge>
                          </td>

                          {/* Status */}
                          <td className="py-3.5 px-4 whitespace-nowrap">
                            <span className="text-[11px] uppercase text-[#888888]">
                              {scan.scan_status}
                            </span>
                          </td>

                          {/* Actions */}
                          <td className="py-3.5 px-4 text-right whitespace-nowrap">
                            <div className="flex items-center justify-end space-x-2">
                              <Link to={`/report/${scan.scan_id}`}>
                                <Button
                                  variant="secondary"
                                  size="sm"
                                  rightIcon={<ExternalLink className="w-3 h-3" />}
                                >
                                  REPORT
                                </Button>
                              </Link>
                              <button
                                onClick={() => setDeleteConfirmId(scan.scan_id)}
                                className="p-1.5 text-[#666666] hover:text-[#F87171] transition-colors"
                                title="Delete historical audit"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Toolbar */}
            {totalPages > 0 && (
              <div className="p-4 bg-[#0D0D0D] border-t border-[#222222] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-[#A1A1A1]">
                <div className="flex items-center space-x-2">
                  <span>
                    Showing {Math.min((currentPage - 1) * pageSize + 1, totalItems)} to{' '}
                    {Math.min(currentPage * pageSize, totalItems)} of {totalItems} total audits
                  </span>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-1.5">
                    <span className="text-[#666666]">Per Page:</span>
                    <select
                      value={pageSize}
                      onChange={(e) => {
                        setPageSize(Number(e.target.value));
                        setCurrentPage(1);
                      }}
                      className="bg-[#101010] border border-[#292929] text-xs font-mono text-[#F5F5F5] h-7 px-2"
                    >
                      <option value={10}>10</option>
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                    </select>
                  </div>

                  <div className="flex items-center space-x-1">
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
              </div>
            )}
          </Card>
        </div>
      </Container>
    </div>
  );
};

export default HistoryPage;
