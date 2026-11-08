import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Eye,
  FileText,
  RefreshCw,
  Search,
  Shield,
  X,
  XCircle,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import { AdminAuditLogItem, PaginatedAdminAuditLogs } from '../../types/admin';

export const AdminAuditLogsPage: React.FC = () => {
  const [logsData, setLogsData] = useState<PaginatedAdminAuditLogs | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [adminFilter, setAdminFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AdminAuditLogItem | null>(null);

  const fetchLogs = async (page: number = currentPage) => {
    try {
      const data = await adminService.getAuditLogs(
        page,
        20,
        actionFilter || undefined,
        adminFilter || undefined,
        searchQuery || undefined
      );
      setLogsData(data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLogs(currentPage);
  }, [currentPage, actionFilter, adminFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchLogs(1);
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchLogs(currentPage);
  };

  const getOutcomeBadge = (outcome: AdminAuditLogItem['outcome']) => {
    switch (outcome) {
      case 'SUCCESS':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-[#132413] text-[#4ade80] border border-[#234d23]">
            <CheckCircle2 className="w-3 h-3 text-[#4ade80]" />
            SUCCESS
          </span>
        );
      case 'FAILURE':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-[#291313] text-[#f87171] border border-[#4d2323]">
            <XCircle className="w-3 h-3 text-[#f87171]" />
            FAILURE
          </span>
        );
      case 'DENIED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-[#292212] text-[#fbbf24] border border-[#4d3f1e]">
            <AlertCircle className="w-3 h-3 text-[#fbbf24]" />
            DENIED
          </span>
        );
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#222222] pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono uppercase">
              Administrator Audit Logs
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium tracking-wide border bg-[#111111] text-[#a0a0a0] border-[#333333]">
              IMMUTABLE
            </span>
          </div>
          <p className="text-sm text-[#737373] mt-1 font-mono">
            Cryptographically timestamped audit records of all administrative actions and security state transitions
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="border-[#333333] hover:bg-[#1c1c1c] text-[#e5e5e5] font-mono text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh Logs
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#737373]" />
          <input
            type="text"
            placeholder="Search action, target resource or metadata..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-[#0c0c0c] border border-[#262626] rounded text-xs font-mono text-white placeholder-[#525252] focus:outline-none focus:border-[#404040]"
          />
        </form>

        <div className="flex items-center gap-2">
          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-3 py-2 bg-[#0c0c0c] border border-[#262626] rounded text-xs font-mono text-[#e5e5e5] focus:outline-none focus:border-[#404040]"
          >
            <option value="">All Actions</option>
            <option value="ADMIN_LOGIN">Admin Login</option>
            <option value="USER_SUSPEND">User Suspend</option>
            <option value="USER_RESTORE">User Restore</option>
            <option value="REPORT_MODERATION">Report Moderation</option>
            <option value="BULK_REPORT_MODERATION">Bulk Report Moderation</option>
            <option value="MAINTENANCE_TOGGLE">Maintenance Toggle</option>
            <option value="PASSWORD_CHANGE">Password Change</option>
          </select>

          <input
            type="text"
            placeholder="Filter admin username..."
            value={adminFilter}
            onChange={(e) => {
              setAdminFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-3 py-2 bg-[#0c0c0c] border border-[#262626] rounded text-xs font-mono text-white placeholder-[#525252] focus:outline-none focus:border-[#404040] w-48"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="py-24 flex flex-col items-center justify-center space-y-4">
          <PixelSpinner />
          <p className="text-xs font-mono text-[#737373] tracking-widest uppercase">
            Loading Cryptographic Audit Trail...
          </p>
        </div>
      ) : !logsData ? (
        <Card className="bg-[#111111] border-[#222222] p-8 text-center text-[#737373] font-mono text-xs">
          Failed to load audit logs.
        </Card>
      ) : (
        <>
          {/* Logs Table */}
          <Card className="bg-[#111111] border-[#222222] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0a0a0a] border-b border-[#222222] text-[#737373] uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Timestamp (UTC)</th>
                    <th className="py-3 px-4">Administrator</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Target Resource</th>
                    <th className="py-3 px-4">Outcome</th>
                    <th className="py-3 px-4">IP Address</th>
                    <th className="py-3 px-4 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1a1a1a]">
                  {logsData.items.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-[#737373]">
                        No audit events recorded matching current filters.
                      </td>
                    </tr>
                  ) : (
                    logsData.items.map((log) => (
                      <tr key={log.id} className="hover:bg-[#141414] transition-colors">
                        <td className="py-3 px-4 text-[#a0a0a0] whitespace-nowrap">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="py-3 px-4 font-semibold text-white">
                          <span className="flex items-center gap-1.5">
                            <Shield className="w-3.5 h-3.5 text-[#737373]" />
                            {log.admin_username}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-white">
                          <span className="px-2 py-0.5 rounded bg-[#1c1c1c] text-[#d4d4d4] border border-[#2a2a2a] text-[11px]">
                            {log.action}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-[#8a8a8a] max-w-xs truncate">
                          {log.target_resource || '—'}
                        </td>
                        <td className="py-3 px-4">{getOutcomeBadge(log.outcome)}</td>
                        <td className="py-3 px-4 text-[#666666] font-mono">
                          {log.ip_address || '127.0.0.1'}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => setSelectedLog(log)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#191919] hover:bg-[#262626] text-white border border-[#333333] transition-colors text-[11px]"
                          >
                            <Eye className="w-3 h-3" />
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {logsData.total_pages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-[#1a1a1a] bg-[#0c0c0c] text-xs font-mono text-[#737373]">
                <div>
                  Showing page {logsData.page} of {logsData.total_pages} ({logsData.total} total log entries)
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="border-[#262626] text-white font-mono text-xs px-2.5 py-1"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage((p) => Math.min(logsData.total_pages, p + 1))}
                    disabled={currentPage >= logsData.total_pages}
                    className="border-[#262626] text-white font-mono text-xs px-2.5 py-1"
                  >
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            )}
          </Card>

          {/* Detailed Log Inspection Modal */}
          {selectedLog && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
              <div className="bg-[#0f0f0f] border border-[#2a2a2a] rounded-lg max-w-2xl w-full p-6 space-y-5 shadow-2xl">
                <div className="flex items-center justify-between pb-3 border-b border-[#222222]">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-white" />
                    <h3 className="font-mono text-sm font-semibold text-white uppercase tracking-wider">
                      Audit Log Entry Details
                    </h3>
                  </div>
                  <button
                    onClick={() => setSelectedLog(null)}
                    className="text-[#737373] hover:text-white transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                  <div className="p-3 bg-[#080808] border border-[#1c1c1c] rounded">
                    <span className="text-[#666666] block">Log ID</span>
                    <span className="text-white font-mono text-[11px] select-all">{selectedLog.id}</span>
                  </div>
                  <div className="p-3 bg-[#080808] border border-[#1c1c1c] rounded">
                    <span className="text-[#666666] block">Action</span>
                    <span className="text-white font-semibold">{selectedLog.action}</span>
                  </div>
                  <div className="p-3 bg-[#080808] border border-[#1c1c1c] rounded">
                    <span className="text-[#666666] block">Admin Operator</span>
                    <span className="text-white">{selectedLog.admin_username}</span>
                  </div>
                  <div className="p-3 bg-[#080808] border border-[#1c1c1c] rounded">
                    <span className="text-[#666666] block">Outcome</span>
                    <span className="mt-1 block">{getOutcomeBadge(selectedLog.outcome)}</span>
                  </div>
                  <div className="p-3 bg-[#080808] border border-[#1c1c1c] rounded">
                    <span className="text-[#666666] block">Target Resource</span>
                    <span className="text-white select-all">{selectedLog.target_resource || 'None'}</span>
                  </div>
                  <div className="p-3 bg-[#080808] border border-[#1c1c1c] rounded">
                    <span className="text-[#666666] block">Timestamp</span>
                    <span className="text-white">{new Date(selectedLog.created_at).toISOString()}</span>
                  </div>
                </div>

                {/* Structured Payload / Metadata Details */}
                <div className="space-y-2">
                  <span className="text-xs font-mono font-semibold text-[#a0a0a0] uppercase tracking-wider block">
                    Structured Audit Payload (JSON)
                  </span>
                  <div className="p-4 bg-[#050505] border border-[#1a1a1a] rounded max-h-60 overflow-y-auto">
                    <pre className="text-[11px] font-mono text-[#4ade80] whitespace-pre-wrap">
                      {JSON.stringify(selectedLog.details || {}, null, 2)}
                    </pre>
                  </div>
                </div>

                <div className="flex justify-end pt-3 border-t border-[#222222]">
                  <Button
                    size="sm"
                    onClick={() => setSelectedLog(null)}
                    className="bg-white hover:bg-[#e5e5e5] text-black font-mono text-xs px-4"
                  >
                    Close Log Inspector
                  </Button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
