import React, { useState } from 'react';
import { X, Flag, AlertTriangle } from 'lucide-react';
import { Button } from '../common/Button';
import { communityService } from '../../services/communityService';
import { formatApiError } from '../../services/api';

interface FlagReportModalProps {
  reportId: string;
  domain?: string | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const FlagReportModal: React.FC<FlagReportModalProps> = ({
  reportId,
  domain,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [flagReason, setFlagReason] = useState<
    'INACCURATE' | 'ABUSIVE_OR_SPAM' | 'DUPLICATE' | 'RESOLVED_SAFE' | 'OTHER'
  >('INACCURATE');
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      await communityService.flagReport(reportId, {
        flag_reason: flagReason,
        notes: notes.trim() || undefined,
      });
      setIsSuccess(true);
      setTimeout(() => {
        setIsSuccess(false);
        onClose();
        if (onSuccess) onSuccess();
      }, 1500);
    } catch (err: any) {
      setErrorMessage(formatApiError(err).message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-md bg-[#0D0D0D] border border-[#292929] shadow-2xl p-6 font-mono text-xs relative"
        role="dialog"
        aria-modal="true"
        aria-labelledby="flag-report-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#222222]">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 bg-[#1F1212] border border-[#7F1D1D]/60 text-[#F87171]">
              <Flag className="w-4 h-4" />
            </div>
            <div>
              <h3 id="flag-report-title" className="text-sm font-semibold text-[#F5F5F5] uppercase">
                Flag Threat Report
              </h3>
              <p className="text-[11px] text-[#666666] truncate max-w-xs">
                TARGET: {domain || reportId.slice(0, 8)}...
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[#666666] hover:text-[#F5F5F5] transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {isSuccess ? (
          <div className="py-8 text-center space-y-2">
            <div className="w-8 h-8 rounded-full bg-[#052E16] text-[#4ADE80] border border-[#166534] mx-auto flex items-center justify-center">
              ✓
            </div>
            <h4 className="text-sm font-semibold text-[#F5F5F5] uppercase">Flag Submitted</h4>
            <p className="text-xs text-[#888888]">
              Thank you. Our moderation team has been notified.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="py-4 space-y-4">
            {errorMessage && (
              <div className="p-3 bg-[#1C1212] border border-[#F87171]/40 flex items-center space-x-2 text-[#FCA5A5] text-[11px]">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-[11px] text-[#A1A1A1] uppercase block">
                Flag Rationale (Required)
              </label>
              <select
                value={flagReason}
                onChange={(e) =>
                  setFlagReason(
                    e.target.value as 'INACCURATE' | 'ABUSIVE_OR_SPAM' | 'DUPLICATE' | 'RESOLVED_SAFE' | 'OTHER'
                  )
                }
                className="w-full bg-[#121212] border border-[#292929] text-[#F5F5F5] p-2.5 text-xs focus:border-[#F5F5F5] outline-none"
              >
                <option value="INACCURATE">Inaccurate Information / False Claim</option>
                <option value="ABUSIVE_OR_SPAM">Abusive, Malicious, or Spam Report</option>
                <option value="DUPLICATE">Duplicate Submission</option>
                <option value="RESOLVED_SAFE">Domain Resolved / Legitimate Entity</option>
                <option value="OTHER">Other Issue</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-[11px] text-[#A1A1A1] uppercase block">
                Additional Context / Evidence (Optional)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                maxLength={500}
                rows={3}
                placeholder="Explain why this report should be reviewed or removed..."
                className="w-full bg-[#121212] border border-[#292929] text-[#F5F5F5] p-2.5 text-xs focus:border-[#F5F5F5] outline-none resize-none placeholder:text-[#555555]"
              />
              <span className="text-[10px] text-[#555555] block text-right">
                {notes.length} / 500
              </span>
            </div>

            <div className="pt-2 border-t border-[#222222] flex items-center justify-end space-x-2">
              <Button type="button" variant="secondary" size="sm" onClick={onClose} disabled={isSubmitting}>
                CANCEL
              </Button>
              <Button type="submit" variant="danger" size="sm" isLoading={isSubmitting}>
                SUBMIT FLAG
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default FlagReportModal;
