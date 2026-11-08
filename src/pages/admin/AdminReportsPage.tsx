import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Eye,
  Paperclip,
  RefreshCw,
  Search,
  ShieldAlert,
  ThumbsUp,
  XCircle,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import { AdminReportListItem } from '../../types/admin';

export const AdminReportsPage: React.FC = () => {
  const [reports, setReports] = useState<AdminReportListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Bulk Selection State
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkActionTarget, setBulkActionTarget] = useState<string | null>(null);
  const [bulkReason, setBulkReason] = useState('');
  const [isSubmittingBulk, setIsSubmittingBulk] = useState(false);
  const [bulkError, setBulkError] = useState<string | null>(null);

  const navigate = useNavigate();

  const loadReports = async () => {
    setIsLoading(true);
    try {
      const statusParam = statusFilter === 'all' ? undefined : statusFilter;
      const catParam = categoryFilter === 'all' ? undefined : categoryFilter;
      const res = await adminService.getReports(page, pageSize, statusParam, catParam, search);
      setReports(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
      setSelectedIds([]);
    } catch (err) {
      console.error('Failed fetching reports:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [page, statusFilter, categoryFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadReports();
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === reports.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(reports.map((r) => r.id));
    }
  };

  const toggleSelectOne = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((item) => item !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleExecuteBulk = async () => {
    if (!bulkActionTarget || selectedIds.length === 0) return;
    if (!bulkReason.trim()) {
      setBulkError('A mandatory administrative rationale is required for bulk actions.');
      return;
    }

    setIsSubmittingBulk(true);
    setBulkError(null);

    try {
      await adminService.bulkModerateReports(selectedIds, bulkActionTarget, bulkReason.trim());
      setBulkActionTarget(null);
      setBulkReason('');
      setSelectedIds([]);
      loadReports();
    } catch (err: any) {
      setBulkError(err.response?.data?.message || 'Bulk moderation failed.');
    } finally {
      setIsSubmittingBulk(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    if (s === 'APPROVED' || s === 'VERIFIED') {
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/40 text-emerald-400 border border-emerald-800/60">
          <CheckCircle2 className="w-3 h-3" />
          <span>VERIFIED</span>
        </span>
      );
    }
    if (s === 'REJECTED') {
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-950/40 text-rose-400 border border-rose-800/60">
          <XCircle className="w-3 h-3" />
          <span>REJECTED</span>
        </span>
      );
    }
    if (s === 'UNDER_REVIEW') {
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-950/40 text-blue-400 border border-blue-800/60">
          <Clock className="w-3 h-3" />
          <span>UNDER REVIEW</span>
        </span>
      );
    }
    if (s === 'RESOLVED') {
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-950/40 text-purple-400 border border-purple-800/60">
          <span>RESOLVED</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-950/40 text-amber-400 border border-amber-800/60">
        <Clock className="w-3 h-3" />
        <span>PENDING</span>
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1E1E1E]">
        <div>
          <h1 className="text-xl sm:text-2xl font-light tracking-tight text-white flex items-center space-x-2">
            <span>Community Threat Moderation Queue</span>
          </h1>
          <p className="text-xs font-mono text-[#888888] mt-1">
            REVIEW COMMUNITY-REPORTED URLS, VERIFY THREAT EVIDENCE & ISSUE VERDICTS
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-[#888888]">
            QUEUE: <strong className="text-white">{total}</strong>
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={loadReports}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            REFRESH
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card pixelFrame className="p-4 bg-[#0E0E0E] border-[#222222] space-y-3">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Search form */}
          <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[#555555] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by URL, domain, or report ID..."
                className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded pl-9 pr-3 py-2 text-xs text-white placeholder-[#555555] font-mono focus:outline-none transition-colors"
              />
            </div>
            <Button type="submit" variant="outline" size="sm" className="shrink-0 font-mono text-xs">
              FILTER
            </Button>
          </form>

          {/* Status filters */}
          <div className="flex items-center space-x-2 overflow-x-auto text-xs font-mono">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="bg-[#141414] border border-[#282828] text-white rounded px-3 py-2 text-xs font-mono focus:outline-none"
            >
              <option value="all">ALL STATUSES</option>
              <option value="PENDING">PENDING</option>
              <option value="UNDER_REVIEW">UNDER REVIEW</option>
              <option value="APPROVED">VERIFIED (APPROVED)</option>
              <option value="REJECTED">REJECTED</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>

            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setPage(1);
              }}
              className="bg-[#141414] border border-[#282828] text-white rounded px-3 py-2 text-xs font-mono focus:outline-none"
            >
              <option value="all">ALL CATEGORIES</option>
              <option value="PHISHING">PHISHING</option>
              <option value="MALWARE">MALWARE</option>
              <option value="SUSPICIOUS">SUSPICIOUS</option>
              <option value="SCAM">SCAM / FRAUD</option>
            </select>
          </div>
        </div>

        {/* Bulk Actions Bar (appears when items selected) */}
        {selectedIds.length > 0 && (
          <div className="p-3 bg-[#161616] border border-[#333333] rounded flex items-center justify-between gap-4 text-xs font-mono">
            <span className="text-white font-medium">
              {selectedIds.length} REPORT{selectedIds.length > 1 ? 'S' : ''} SELECTED
            </span>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setBulkActionTarget('UNDER_REVIEW')}
                className="text-[11px] font-mono"
              >
                MARK UNDER REVIEW
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setBulkActionTarget('APPROVE')}
                className="text-[11px] font-mono text-emerald-400 hover:text-emerald-300"
              >
                BULK APPROVE
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => setBulkActionTarget('REJECT')}
                className="text-[11px] font-mono"
              >
                BULK REJECT
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Reports Table */}
      <Card pixelFrame className="p-0 bg-[#0E0E0E] border-[#222222] overflow-hidden">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <PixelSpinner size={32} />
            <p className="text-xs font-mono text-[#888888]">Loading moderation queue...</p>
          </div>
        ) : reports.length === 0 ? (
          <div className="py-16 text-center space-y-2">
            <ShieldAlert className="w-8 h-8 text-[#444444] mx-auto" />
            <p className="text-xs font-mono text-[#777777]">NO THREAT REPORTS IN THIS QUEUE.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#121212] border-b border-[#222222] text-[#888888] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4 w-10">
                    <input
                      type="checkbox"
                      checked={selectedIds.length === reports.length && reports.length > 0}
                      onChange={toggleSelectAll}
                      className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0"
                    />
                  </th>
                  <th className="py-3 px-4">Target URL / Domain</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Confirmations</th>
                  <th className="py-3 px-4">Submitted</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#181818]">
                {reports.map((r) => {
                  const isSelected = selectedIds.includes(r.id);
                  return (
                    <tr
                      key={r.id}
                      className={`hover:bg-[#121212] transition-colors ${
                        isSelected ? 'bg-[#151515]' : ''
                      }`}
                    >
                      <td className="py-3 px-4">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectOne(r.id)}
                          className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0"
                        />
                      </td>
                      <td className="py-3 px-4 max-w-sm">
                        <div className="font-medium text-white truncate">{r.submitted_url}</div>
                        <div className="text-[10px] text-[#555555] truncate">{r.domain || r.id}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-[#CCCCCC]">{r.threat_type || r.report_reason}</span>
                        {r.target_brand && (
                          <span className="block text-[10px] text-[#777777]">
                            Target: {r.target_brand}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">{getStatusBadge(r.moderation_status)}</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center space-x-1 text-[#AAAAAA]">
                          <ThumbsUp className="w-3 h-3 text-[#666666]" />
                          <span>{r.upvotes}</span>
                        </span>
                        {r.attachments_count > 0 && (
                          <span className="inline-flex items-center space-x-0.5 ml-3 text-[#777777]">
                            <Paperclip className="w-3 h-3" />
                            <span>{r.attachments_count}</span>
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-[#888888]">
                        {new Date(r.created_at).toLocaleDateString([], {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate(`/admin/reports/${r.id}`)}
                          className="text-[11px] font-mono py-1 px-2.5 space-x-1"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>MODERATE</span>
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-[#202020] flex items-center justify-between text-xs font-mono text-[#888888]">
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* ------------------------------------------------------------- */}
      {/* Bulk Moderation Confirmation Dialog                           */}
      {/* ------------------------------------------------------------- */}
      {bulkActionTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <Card pixelFrame className="max-w-md w-full p-6 bg-[#0E0E0E] border-[#2A2A2A] space-y-4">
            <div>
              <h3 className="text-sm font-mono font-semibold uppercase text-white">
                Confirm Bulk Action: {bulkActionTarget}
              </h3>
              <p className="text-xs font-mono text-[#888888] mt-1">
                You are about to moderate <span className="text-white font-bold">{selectedIds.length}</span> threat reports simultaneously.
              </p>
            </div>

            {bulkError && (
              <p className="text-xs font-mono text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-900/50">
                {bulkError}
              </p>
            )}

            <div className="space-y-1.5">
              <label className="block text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                Mandatory Bulk Rationale
              </label>
              <textarea
                value={bulkReason}
                onChange={(e) => setBulkReason(e.target.value)}
                placeholder="Reason applied to all selected reports..."
                rows={3}
                className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2.5 text-xs text-white placeholder-[#555555] font-mono focus:outline-none transition-colors"
                required
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setBulkActionTarget(null);
                  setBulkReason('');
                  setBulkError(null);
                }}
                disabled={isSubmittingBulk}
              >
                CANCEL
              </Button>
              <Button
                variant={bulkActionTarget === 'REJECT' ? 'danger' : 'primary'}
                size="sm"
                onClick={handleExecuteBulk}
                isLoading={isSubmittingBulk}
                className="font-mono text-xs uppercase"
              >
                APPLY BULK {bulkActionTarget}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
