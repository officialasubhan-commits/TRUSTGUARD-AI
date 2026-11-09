import React, { useEffect, useState } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Eye,
  Globe,
  RefreshCw,
  Search,
  X,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import { AdminScanItem } from '../../types/admin';

export const AdminScansPage: React.FC = () => {
  const [scans, setScans] = useState<AdminScanItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [classificationFilter, setClassificationFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  // Inspector Modal State
  const [inspectingScan, setInspectingScan] = useState<AdminScanItem | null>(null);
  const [detailedData, setDetailedData] = useState<Record<string, any> | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const loadScans = async () => {
    setIsLoading(true);
    try {
      const classParam = classificationFilter === 'all' ? undefined : classificationFilter;
      const res = await adminService.getScans(page, pageSize, search, classParam);
      setScans(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed loading scans:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadScans();
  }, [page, classificationFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadScans();
  };

  const openInspector = async (scan: AdminScanItem) => {
    setInspectingScan(scan);
    setIsLoadingDetail(true);
    try {
      const data = await adminService.getScanDetail(scan.id);
      setDetailedData(data);
    } catch (err) {
      console.error('Failed loading scan telemetry:', err);
      setDetailedData(null);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const getBadgeStyle = (classification: string) => {
    switch (classification.toUpperCase()) {
      case 'SAFE':
      case 'LOW':
      case 'CLEAN':
        return 'bg-emerald-950/40 text-emerald-400 border-emerald-800/60';
      case 'SUSPICIOUS':
      case 'MEDIUM':
      case 'MODERATE':
        return 'bg-amber-950/40 text-amber-400 border-amber-800/60';
      case 'MALICIOUS':
      case 'HIGH':
      case 'CRITICAL':
      case 'HIGH_RISK':
      case 'CRITICAL_RISK':
        return 'bg-rose-950/40 text-rose-400 border-rose-800/60';
      default:
        return 'bg-zinc-900 text-[#888888] border-[#333333]';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1E1E1E]">
        <div>
          <h1 className="text-xl sm:text-2xl font-light tracking-tight text-white flex items-center space-x-2">
            <span>Website Scans Management</span>
          </h1>
          <p className="text-xs font-mono text-[#888888] mt-1">
            GLOBAL URL SCAN HISTORY, CLASSIFICATIONS & THREAT TELEMETRY
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-[#888888]">
            TOTAL SCANS: <strong className="text-white">{total.toLocaleString()}</strong>
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={loadScans}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            REFRESH
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card pixelFrame className="p-4 bg-[#0E0E0E] border-[#222222]">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[#555555] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search scanned URL or domain..."
                className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded pl-9 pr-3 py-2 text-xs text-white placeholder-[#555555] font-mono focus:outline-none transition-colors"
              />
            </div>
            <Button type="submit" variant="outline" size="sm" className="shrink-0 font-mono text-xs">
              SEARCH
            </Button>
          </form>

          {/* Classification Filter Buttons */}
          <div className="flex items-center space-x-1 bg-[#141414] border border-[#262626] rounded p-0.5 text-xs font-mono">
            {['all', 'safe', 'suspicious', 'malicious'].map((c) => (
              <button
                key={c}
                onClick={() => {
                  setClassificationFilter(c);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded transition-colors uppercase ${
                  classificationFilter === c
                    ? 'bg-white text-black font-semibold'
                    : 'text-[#888888] hover:text-white'
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Scans Data Table */}
      <Card pixelFrame className="p-0 bg-[#0E0E0E] border-[#222222] overflow-hidden">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <PixelSpinner size={32} />
            <p className="text-xs font-mono text-[#888888]">Loading scan telemetry...</p>
          </div>
        ) : scans.length === 0 ? (
          <div className="py-16 text-center space-y-2">
            <Globe className="w-8 h-8 text-[#444444] mx-auto" />
            <p className="text-xs font-mono text-[#777777]">NO SCAN RECORDS FOUND.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#121212] border-b border-[#222222] text-[#888888] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Target URL / Domain</th>
                  <th className="py-3 px-4">Classification</th>
                  <th className="py-3 px-4">Trust Score</th>
                  <th className="py-3 px-4">Scanned At</th>
                  <th className="py-3 px-4 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#181818]">
                {scans.map((s) => (
                  <tr key={s.id} className="hover:bg-[#121212] transition-colors">
                    <td className="py-3 px-4 max-w-md">
                      <div className="font-semibold text-white truncate">{s.url}</div>
                      <div className="text-[10px] text-[#666666] font-mono truncate">
                        Domain: {s.domain || 'N/A'} {s.ip_address ? `• IP: ${s.ip_address}` : ''}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${getBadgeStyle(
                          s.classification
                        )}`}
                      >
                        {s.classification}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-white">{s.trust_score.toFixed(1)}</span>
                      <span className="text-[#666666] text-[10px]"> / 100</span>
                    </td>
                    <td className="py-3 px-4 text-[#888888]">
                      {new Date(s.scanned_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openInspector(s)}
                        className="text-[11px] font-mono py-1 px-2"
                        title="Inspect Scan Diagnostics"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))}
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
      {/* Scan Inspector Modal                                          */}
      {/* ------------------------------------------------------------- */}
      {inspectingScan && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <Card pixelFrame className="max-w-2xl w-full p-6 bg-[#0E0E0E] border-[#2A2A2A] space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-start justify-between border-b border-[#1C1C1C] pb-3 shrink-0">
              <div>
                <h3 className="text-sm font-mono font-semibold uppercase text-white flex items-center space-x-2">
                  <span>Scan Telemetry Inspection</span>
                </h3>
                <p className="text-xs font-mono text-cyan-400 mt-1 truncate max-w-lg">
                  {inspectingScan.url}
                </p>
              </div>
              <button
                onClick={() => {
                  setInspectingScan(null);
                  setDetailedData(null);
                }}
                className="text-[#666666] hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4 font-mono text-xs flex-1 overflow-y-auto pr-1">
              {/* Summary Badges */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-[#121212] p-3 rounded border border-[#222222]">
                <div>
                  <span className="text-[10px] text-[#777777] block">CLASSIFICATION</span>
                  <span
                    className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border mt-1 ${getBadgeStyle(
                      inspectingScan.classification
                    )}`}
                  >
                    {inspectingScan.classification}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-[#777777] block">TRUST SCORE</span>
                  <span className="text-base font-bold text-white mt-0.5 block">
                    {inspectingScan.trust_score.toFixed(1)} / 100
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-[#777777] block">DOMAIN</span>
                  <span className="text-xs text-[#CCCCCC] truncate mt-1 block">
                    {inspectingScan.domain || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-[#777777] block">SCAN TIMESTAMP</span>
                  <span className="text-[11px] text-[#888888] mt-1 block">
                    {new Date(inspectingScan.scanned_at).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Technical Telemetry Payload */}
              <div className="space-y-2">
                <span className="text-[#A1A1A1] uppercase tracking-wider font-semibold block">
                  Detailed Analysis Payload
                </span>
                {isLoadingDetail ? (
                  <div className="py-8 flex flex-col items-center justify-center space-y-2">
                    <PixelSpinner size={24} />
                    <p className="text-[11px] text-[#777777]">Retrieving raw telemetry...</p>
                  </div>
                ) : (
                  <pre className="p-3 bg-[#141414] border border-[#242424] rounded text-[11px] text-emerald-400 overflow-x-auto max-h-64 font-mono">
                    {JSON.stringify(
                      detailedData || inspectingScan.details || { message: 'No extended diagnostics available' },
                      null,
                      2
                    )}
                  </pre>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-[#1C1C1C] shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setInspectingScan(null);
                  setDetailedData(null);
                }}
              >
                CLOSE
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
