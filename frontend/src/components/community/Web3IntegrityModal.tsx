import React, { useState, useEffect } from 'react';
import {
  X,
  ShieldCheck,
  Cpu,
  Copy,
  Check,
  Layers,
  FileCheck2,
  AlertCircle,
} from 'lucide-react';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { communityService } from '../../services/communityService';
import { Web3IntegrityProof } from '../../types/community';
import { formatApiError } from '../../services/api';

interface Web3IntegrityModalProps {
  reportId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const Web3IntegrityModal: React.FC<Web3IntegrityModalProps> = ({
  reportId,
  isOpen,
  onClose,
}) => {
  const [proof, setProof] = useState<Web3IntegrityProof | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [copiedPayload, setCopiedPayload] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen || !reportId) return;

    let isMounted = true;
    setIsLoading(true);
    setErrorMessage(null);

    communityService
      .getIntegrityProof(reportId)
      .then((data) => {
        if (isMounted) setProof(data);
      })
      .catch((err) => {
        if (isMounted) setErrorMessage(formatApiError(err).message);
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [reportId, isOpen]);

  if (!isOpen) return null;

  const handleCopyHash = () => {
    if (!proof?.canonical_hash) return;
    navigator.clipboard.writeText(proof.canonical_hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleCopyPayload = () => {
    if (!proof?.canonical_payload) return;
    navigator.clipboard.writeText(JSON.stringify(proof.canonical_payload, null, 2));
    setCopiedPayload(true);
    setTimeout(() => setCopiedPayload(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-2xl bg-[#0D0D0D] border border-[#292929] shadow-2xl p-6 font-mono text-xs relative max-h-[90vh] flex flex-col"
        role="dialog"
        aria-modal="true"
        aria-labelledby="web3-integrity-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#222222] shrink-0">
          <div className="flex items-center space-x-2.5">
            <div className="p-1.5 bg-[#141414] border border-[#292929]">
              <Cpu className="w-4 h-4 text-[#F5F5F5]" />
            </div>
            <div>
              <h3 id="web3-integrity-title" className="text-sm font-semibold text-[#F5F5F5] uppercase">
                Web3 Proof of Record Integrity
              </h3>
              <p className="text-[11px] text-[#666666]">
                CRYPTOGRAPHIC VERIFICATION OF CANONICAL THREAT RECORD
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[#666666] hover:text-[#F5F5F5] hover:bg-[#1A1A1A] transition-colors"
            aria-label="Close dialog"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="py-4 space-y-4 overflow-y-auto flex-1">
          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center space-y-3 text-center">
              <div className="w-6 h-6 border-2 border-[#555555] border-t-[#F5F5F5] rounded-full animate-spin" />
              <span className="text-[#A1A1A1]">GENERATING CANONICAL INTEGRITY PROOF...</span>
            </div>
          ) : errorMessage ? (
            <div className="p-4 bg-[#1C1212] border border-[#F87171]/40 flex items-center space-x-3 text-[#FCA5A5]">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          ) : proof ? (
            <>
              {/* Verification Status Banner */}
              <div className="p-3.5 bg-[#052E16]/40 border border-[#166534] flex items-center justify-between gap-3">
                <div className="flex items-center space-x-2.5 text-[#4ADE80]">
                  <ShieldCheck className="w-4 h-4 shrink-0" />
                  <span className="font-semibold text-xs tracking-wider">
                    CRYPTOGRAPHICALLY VERIFIED ON RECORD
                  </span>
                </div>
                <Badge variant="safe" size="xs">
                  {proof.algorithm}
                </Badge>
              </div>

              {/* Informational Guidance */}
              <p className="text-[11px] text-[#888888] leading-relaxed">
                This proof demonstrates that the verified community report payload has remained
                strictly immutable since its administrative verification timestamp. Personal submitter
                information is zero-knowledge redacted.
              </p>

              {/* Cryptographic Hash */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-[#888888]">
                  <span className="uppercase flex items-center space-x-1.5">
                    <FileCheck2 className="w-3.5 h-3.5 text-[#A1A1A1]" />
                    <span>Canonical Record Digest (SHA-256)</span>
                  </span>
                  <button
                    onClick={handleCopyHash}
                    className="flex items-center space-x-1 text-[#F5F5F5] hover:text-[#4ADE80] transition-colors"
                  >
                    {copiedHash ? <Check className="w-3 h-3 text-[#4ADE80]" /> : <Copy className="w-3 h-3" />}
                    <span className="text-[10px]">{copiedHash ? 'COPIED' : 'COPY HASH'}</span>
                  </button>
                </div>
                <div className="p-2.5 bg-[#121212] border border-[#222222] text-[#F5F5F5] break-all select-all font-mono">
                  {proof.canonical_hash}
                </div>
              </div>

              {/* Merkle Commitment & Network Specs */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 bg-[#101010] border border-[#222222] space-y-1">
                  <span className="text-[10px] text-[#666666] uppercase block">
                    Target Blockchain Network
                  </span>
                  <span className="text-[#F5F5F5] font-semibold block">{proof.network}</span>
                </div>
                <div className="p-3 bg-[#101010] border border-[#222222] space-y-1">
                  <span className="text-[10px] text-[#666666] uppercase block">
                    Proof Commitment Type
                  </span>
                  <span className="text-[#F5F5F5] font-semibold block">{proof.proof_type}</span>
                </div>
              </div>

              {/* Merkle Root */}
              <div className="space-y-1">
                <span className="text-[10px] text-[#666666] uppercase flex items-center space-x-1">
                  <Layers className="w-3 h-3 text-[#666666]" />
                  <span>Merkle Leaf Root Hash</span>
                </span>
                <div className="p-2 bg-[#121212] border border-[#222222] text-[#A1A1A1] break-all select-all text-[11px]">
                  {proof.merkle_root}
                </div>
              </div>

              {/* Canonical Payload Viewer */}
              <div className="space-y-1.5 pt-2">
                <div className="flex items-center justify-between text-[#888888]">
                  <span className="uppercase text-[11px]">Canonical Sanitized Payload</span>
                  <button
                    onClick={handleCopyPayload}
                    className="flex items-center space-x-1 text-[#F5F5F5] hover:text-[#4ADE80] transition-colors"
                  >
                    {copiedPayload ? <Check className="w-3 h-3 text-[#4ADE80]" /> : <Copy className="w-3 h-3" />}
                    <span className="text-[10px]">{copiedPayload ? 'COPIED' : 'COPY JSON'}</span>
                  </button>
                </div>
                <pre className="p-3 bg-[#080808] border border-[#222222] text-[#A1A1A1] text-[10.5px] overflow-x-auto max-h-40 font-mono">
                  {JSON.stringify(proof.canonical_payload, null, 2)}
                </pre>
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-[#222222] flex items-center justify-between shrink-0">
          <span className="text-[10px] text-[#555555]">
            TRUSTGUARD AI PROTOCOL v1.0
          </span>
          <Button variant="secondary" size="sm" onClick={onClose}>
            CLOSE AUDIT
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Web3IntegrityModal;
