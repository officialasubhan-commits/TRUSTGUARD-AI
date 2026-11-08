import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Copy,
  Check,
  Printer,
  RotateCcw,
  Shield,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { DetailedSecurityReport } from '../../types/scan';

interface ReportHeaderProps {
  report: DetailedSecurityReport;
}

export const ReportHeader: React.FC<ReportHeaderProps> = ({ report }) => {
  const navigate = useNavigate();
  const [copiedUrl, setCopiedUrl] = useState<boolean>(false);
  const [copiedLink, setCopiedLink] = useState<boolean>(false);

  const handleCopyUrl = async () => {
    try {
      await navigator.clipboard.writeText(report.original_url);
      setCopiedUrl(true);
      setTimeout(() => setCopiedUrl(false), 2000);
    } catch {
      // ignore clipboard error
    }
  };

  const handleCopyReportLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    } catch {
      // ignore clipboard error
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const formatTimestamp = (iso?: string | null) => {
    if (!iso) return 'N/A';
    try {
      const dt = new Date(iso);
      return dt.toUTCString();
    } catch {
      return iso;
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Navigation & Action Row (Hidden during Print) */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#292929] no-print">
        <button
          type="button"
          onClick={() => navigate('/scan')}
          className="inline-flex items-center space-x-2 text-xs font-mono text-[#A1A1A1] hover:text-[#F5F5F5] transition-colors focus-ring"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>RETURN TO SCANNER</span>
        </button>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCopyUrl}
            leftIcon={copiedUrl ? <Check className="w-3.5 h-3.5 text-[#4ADE80]" /> : <Copy className="w-3.5 h-3.5" />}
          >
            {copiedUrl ? 'URL COPIED' : 'COPY URL'}
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={handleCopyReportLink}
            leftIcon={copiedLink ? <Check className="w-3.5 h-3.5 text-[#4ADE80]" /> : <ExternalLink className="w-3.5 h-3.5" />}
          >
            {copiedLink ? 'LINK COPIED' : 'COPY REPORT LINK'}
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={handlePrint}
            leftIcon={<Printer className="w-3.5 h-3.5" />}
          >
            PRINT / PDF
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/scan')}
            leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            SCAN ANOTHER
          </Button>
        </div>
      </div>

      {/* Report Identity Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-[#F5F5F5]" />
            <span className="text-xs font-mono tracking-widest uppercase text-[#A1A1A1]">
              TRUSTGUARD AI • CYBERSECURITY AUDIT
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-light tracking-tight text-[#F5F5F5]">
            Website Security Report
          </h1>
        </div>

        {/* Scan Status & ID */}
        <div className="text-left sm:text-right font-mono space-y-1">
          <div className="flex items-center sm:justify-end space-x-2">
            <span className="text-xs text-[#666666]">SCAN ID:</span>
            <span className="text-xs text-[#F5F5F5] font-semibold">{report.scan_id}</span>
          </div>
          <div className="flex items-center sm:justify-end space-x-2 text-[11px] text-[#888888]">
            <Clock className="w-3 h-3 text-[#666666]" />
            <span>{formatTimestamp(report.completed_at || report.submitted_at)}</span>
          </div>
        </div>
      </div>

      {/* Target URL Display with Untrusted Safety Container */}
      <div className="p-3 bg-[#101010] border border-[#222222] text-xs font-mono flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-0.5 overflow-hidden">
          <span className="text-[10px] text-[#666666] uppercase block tracking-wider">
            ANALYZED DESTINATION (SAFE LITERAL RENDERING)
          </span>
          <span className="text-[#F5F5F5] break-all select-all font-mono">
            {report.original_url}
          </span>
        </div>

        <Badge variant={report.scan_status === 'complete' ? 'safe' : 'unknown'} size="sm" dot>
          {report.scan_status}
        </Badge>
      </div>
    </div>
  );
};

