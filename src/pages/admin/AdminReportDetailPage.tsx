import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  ArrowLeft,
  Check,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileText,
  Lock,
  Paperclip,
  Shield,
  X,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import { AdminReportDetail } from '../../types/admin';

export const AdminReportDetailPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<AdminReportDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Decision Form
  const [selectedAction, setSelectedAction] = useState<
    'APPROVE' | 'REJECT' | 'UNDER_REVIEW' | 'RESOLVED' | 'DUPLICATE' | 'REQUEST_EVIDENCE'
  >('APPROVE');
  const [decisionReason, setDecisionReason] = useState('');
  const [internalNotes, setInternalNotes] = useState('');
  const [duplicateId, setDuplicateId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId) return;
    const fetchReport = async () => {
      setIsLoading(true);
      try {
        const data = await adminService.getReportDetail(reportId);
        setReport(data);
      } catch (err: any) {
        setError(err.response?.data?.message || 'Threat report could not be loaded.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchReport();
  }, [reportId]);

  const handleSubmitDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reportId) return;
    if (!decisionReason.trim()) {
      setSubmitError('A mandatory review rationale is required.');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(null);

    try {
      await adminService.moderateReport(
        reportId,
        selectedAction,
        decisionReason.trim(),
        internalNotes.trim() || undefined,
        selectedAction === 'DUPLICATE' && duplicateId.trim() ? duplicateId.trim() : undefined
      );
      setSubmitSuccess(`Report verdict '${selectedAction}' successfully recorded and audited.`);
      // Reload report detail
      const refreshed = await adminService.getReportDetail(reportId);
      setReport(refreshed);
    } catch (err: any) {
      setSubmitError(err.response?.data?.message || 'Moderation decision could not be recorded.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-3">
        <PixelSpinner size={36} />
        <p className="text-xs font-mono text-[#888888]">Loading comprehensive report evidence...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="py-16 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
        <h2 className="text-lg font-mono text-white">REPORT NOT FOUND</h2>
        <p className="text-xs font-mono text-[#777777]">{error || 'Requested report ID does not exist.'}</p>
        <Button variant="outline" size="sm" onClick={() => navigate('/admin/reports')}>
          ← Return to Queue
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Back button and breadcrumbs */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/admin/reports')}
          className="inline-flex items-center space-x-2 text-xs font-mono text-[#888888] hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>BACK TO MODERATION QUEUE</span>
        </button>

        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="text-[#666666]">REPORT ID:</span>
          <span className="text-white font-medium">{report.id}</span>
        </div>
      </div>

      {/* Main Grid: Left = Report Evidence, Right = Decision Desk */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* ----------------------------------------------------------- */}
        {/* Left 2 Columns: Evidence & Threat Details                   */}
        {/* ----------------------------------------------------------- */}
        <div className="lg:col-span-2 space-y-6">
          {/* Target URL Header Card */}
          <Card pixelFrame className="p-6 bg-[#0E0E0E] border-[#222222] space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1">
                <span className="text-[10px] font-mono text-[#888888] uppercase tracking-wider">
                  SUSPICIOUS TARGET IDENTIFIER
                </span>
                <p className="text-base sm:text-lg font-mono text-white break-all font-semibold">
                  {report.submitted_url}
                </p>
                {report.domain && (
                  <p className="text-xs font-mono text-[#A1A1A1]">DOMAIN: {report.domain}</p>
                )}
              </div>

              <div className="shrink-0 text-right">
                <span className="px-2.5 py-1 rounded text-[11px] font-mono font-bold bg-[#181818] text-white border border-[#333333]">
                  {report.moderation_status}
                </span>
              </div>
            </div>

            <div className="pt-3 border-t border-[#1C1C1C] grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div>
                <span className="text-[#666666] text-[10px] uppercase block">Threat Category</span>
                <span className="text-white font-medium">{report.threat_type || report.report_reason}</span>
              </div>
              <div>
                <span className="text-[#666666] text-[10px] uppercase block">Target Brand</span>
                <span className="text-white font-medium">{report.target_brand || 'None specified'}</span>
              </div>
              <div>
                <span className="text-[#666666] text-[10px] uppercase block">Attack Vector</span>
                <span className="text-white font-medium">{report.attack_vector || 'Web Form'}</span>
              </div>
              <div>
                <span className="text-[#666666] text-[10px] uppercase block">Confirmations</span>
                <span className="text-white font-medium">{report.upvotes} Community Votes</span>
              </div>
            </div>
          </Card>

          {/* User Submitted Description & Notes */}
          <Card pixelFrame className="p-6 bg-[#0E0E0E] border-[#222222] space-y-3">
            <div className="flex items-center space-x-2 text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
              <FileText className="w-4 h-4 text-white" />
              <span>Submitter Threat Narrative</span>
            </div>
            <div className="p-4 bg-[#121212] border border-[#222222] rounded text-xs text-[#E0E0E0] font-mono whitespace-pre-wrap leading-relaxed">
              {report.description || report.notes || 'No extended narrative provided by the submitter.'}
            </div>
            <div className="flex items-center justify-between text-[11px] font-mono text-[#666666] pt-1">
              <span>Submitted by: {report.submitter_email || 'Community Contributor'}</span>
              <span>Timestamp: {new Date(report.created_at).toLocaleString()}</span>
            </div>
          </Card>

          {/* Evidence Attachments */}
          <Card pixelFrame className="p-6 bg-[#0E0E0E] border-[#222222] space-y-4">
            <div className="flex items-center justify-between border-b border-[#202020] pb-3">
              <div className="flex items-center space-x-2 text-xs font-mono text-white">
                <Paperclip className="w-4 h-4" />
                <span>ATTACHED EVIDENCE FILES ({report.evidence_items.length})</span>
              </div>
              <span className="text-[10px] font-mono text-[#777777]">ISOLATED PREVIEW</span>
            </div>

            {report.evidence_items.length === 0 ? (
              <p className="text-xs font-mono text-[#666666] py-4 text-center">
                NO EVIDENCE SCREENSHOTS OR ATTACHMENTS SUBMITTED WITH THIS REPORT.
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {report.evidence_items.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-3 bg-[#121212] border border-[#262626] rounded space-y-2 text-xs font-mono"
                  >
                    {/* Safe Image Preview if image */}
                    {ev.file_type.startsWith('image/') ? (
                      <div className="h-40 bg-[#080808] border border-[#1E1E1E] rounded overflow-hidden flex items-center justify-center">
                        <img
                          src={ev.url}
                          alt={ev.filename}
                          className="max-h-full max-w-full object-contain"
                          onError={(e) => {
                            (e.target as any).style.display = 'none';
                          }}
                        />
                      </div>
                    ) : (
                      <div className="h-40 bg-[#080808] border border-[#1E1E1E] rounded flex flex-col items-center justify-center space-y-2 text-[#777777]">
                        <FileText className="w-8 h-8" />
                        <span className="text-[11px]">{ev.file_type}</span>
                      </div>
                    )}

                    <div className="space-y-1 pt-1">
                      <p className="text-white font-medium truncate">{ev.filename}</p>
                      <p className="text-[10px] text-[#666666]">
                        {(ev.file_size_bytes / 1024).toFixed(1)} KB | {ev.file_type}
                      </p>
                      {ev.sha256_hash && (
                        <p className="text-[9px] text-[#555555] font-mono truncate" title={ev.sha256_hash}>
                          SHA-256: {ev.sha256_hash}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Associated Scan Details (if linked) */}
          {report.associated_scan && (
            <Card pixelFrame className="p-6 bg-[#0E0E0E] border-[#222222] space-y-3">
              <div className="flex items-center justify-between border-b border-[#202020] pb-2 text-xs font-mono">
                <span className="text-white font-medium flex items-center space-x-1.5">
                  <Shield className="w-4 h-4 text-emerald-400" />
                  <span>ASSOCIATED AUTOMATED SECURITY SCAN</span>
                </span>
                <span className="text-[#888888]">
                  SCORE: <strong className="text-white">{report.associated_scan.trust_score ?? 'N/A'}</strong>
                </span>
              </div>
              <div className="text-xs font-mono text-[#CCCCCC] space-y-1">
                <p>Status: {report.associated_scan.scan_status}</p>
                <p>Risk Classification: {report.associated_scan.risk_level || 'UNKNOWN'}</p>
                <a
                  href={`/report/${report.associated_scan.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1 text-xs text-white underline mt-2"
                >
                  <span>Open Full Security Report</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </Card>
          )}
        </div>

        {/* ----------------------------------------------------------- */}
        {/* Right Column: Moderation Decision Desk                     */}
        {/* ----------------------------------------------------------- */}
        <div className="space-y-6">
          <Card pixelFrame className="p-6 bg-[#0E0E0E] border-[#222222] space-y-5 sticky top-6">
            <div className="border-b border-[#202020] pb-3">
              <h2 className="text-sm font-mono font-semibold text-white uppercase tracking-wider">
                Moderation Verdict Console
              </h2>
              <p className="text-[11px] font-mono text-[#777777] mt-0.5">
                Issue an authoritative administrative decision
              </p>
            </div>

            {submitSuccess && (
              <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded text-xs font-mono text-emerald-300 flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>{submitSuccess}</span>
              </div>
            )}

            {submitError && (
              <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded text-xs font-mono text-rose-300 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{submitError}</span>
              </div>
            )}

            <form onSubmit={handleSubmitDecision} className="space-y-4">
              {/* Verdict Buttons */}
              <div className="space-y-1.5">
                <label className="block text-[11px] font-mono text-[#888888] uppercase tracking-wider">
                  Moderation Verdict
                </label>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <button
                    type="button"
                    onClick={() => setSelectedAction('APPROVE')}
                    className={`p-2.5 rounded border text-left flex items-center space-x-2 transition-colors ${
                      selectedAction === 'APPROVE'
                        ? 'bg-emerald-950/50 border-emerald-500 text-emerald-300 font-bold'
                        : 'bg-[#141414] border-[#262626] text-[#888888] hover:text-white'
                    }`}
                  >
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span>VERIFY / APPROVE</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedAction('REJECT')}
                    className={`p-2.5 rounded border text-left flex items-center space-x-2 transition-colors ${
                      selectedAction === 'REJECT'
                        ? 'bg-rose-950/50 border-rose-500 text-rose-300 font-bold'
                        : 'bg-[#141414] border-[#262626] text-[#888888] hover:text-white'
                    }`}
                  >
                    <X className="w-3.5 h-3.5 text-rose-400" />
                    <span>REJECT</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedAction('UNDER_REVIEW')}
                    className={`p-2.5 rounded border text-left flex items-center space-x-2 transition-colors ${
                      selectedAction === 'UNDER_REVIEW'
                        ? 'bg-blue-950/50 border-blue-500 text-blue-300 font-bold'
                        : 'bg-[#141414] border-[#262626] text-[#888888] hover:text-white'
                    }`}
                  >
                    <Clock className="w-3.5 h-3.5 text-blue-400" />
                    <span>UNDER REVIEW</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setSelectedAction('RESOLVED')}
                    className={`p-2.5 rounded border text-left flex items-center space-x-2 transition-colors ${
                      selectedAction === 'RESOLVED'
                        ? 'bg-purple-950/50 border-purple-500 text-purple-300 font-bold'
                        : 'bg-[#141414] border-[#262626] text-[#888888] hover:text-white'
                    }`}
                  >
                    <Shield className="w-3.5 h-3.5 text-purple-400" />
                    <span>RESOLVED</span>
                  </button>
                </div>
              </div>

              {/* Duplicate Target ID input if duplicate */}
              {selectedAction === 'DUPLICATE' && (
                <div className="space-y-1">
                  <label className="block text-[11px] font-mono text-[#888888] uppercase">
                    Canonical Report ID
                  </label>
                  <input
                    type="text"
                    value={duplicateId}
                    onChange={(e) => setDuplicateId(e.target.value)}
                    placeholder="UUID of original report..."
                    className="w-full bg-[#141414] border border-[#282828] rounded p-2 text-xs text-white font-mono"
                    required
                  />
                </div>
              )}

              {/* Mandatory Reason */}
              <div className="space-y-1.5">
                <label className="block text-[11px] font-mono text-[#A1A1A1] uppercase tracking-wider">
                  Mandatory Review Rationale *
                </label>
                <textarea
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                  placeholder="Document specific threat evidence, domain indicators, or justification..."
                  rows={3}
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2.5 text-xs text-white placeholder-[#555555] font-mono focus:outline-none transition-colors"
                  required
                />
              </div>

              {/* Private Internal Notes */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="block text-[11px] font-mono text-[#A1A1A1] uppercase tracking-wider flex items-center space-x-1">
                    <Lock className="w-3 h-3 text-amber-400" />
                    <span>Private Internal Notes</span>
                  </label>
                  <span className="text-[10px] font-mono text-[#666666]">ADMIN ONLY</span>
                </div>
                <textarea
                  value={internalNotes}
                  onChange={(e) => setInternalNotes(e.target.value)}
                  placeholder="Private moderator notes (hidden from ordinary visitors)..."
                  rows={2}
                  className="w-full bg-[#141414] border border-[#282828] focus:border-amber-500 rounded p-2.5 text-xs text-white placeholder-[#555555] font-mono focus:outline-none transition-colors"
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={isSubmitting}
                className="w-full font-mono text-xs font-semibold py-3"
              >
                RECORD AUTHORITATIVE DECISION
              </Button>
            </form>

            {/* Previous Moderation History */}
            {report.reviewed_at && (
              <div className="pt-4 border-t border-[#1C1C1C] space-y-1 text-xs font-mono text-[#777777]">
                <p>Reviewed At: {new Date(report.reviewed_at).toLocaleString()}</p>
                {report.moderation_notes && (
                  <div className="p-2 bg-[#121212] border border-[#222222] rounded text-[11px] text-[#A1A1A1] mt-1 whitespace-pre-wrap">
                    {report.moderation_notes}
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
