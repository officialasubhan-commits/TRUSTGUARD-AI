import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Info,
  Send,
} from 'lucide-react';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { communityService } from '../services/communityService';
import { CommunityReportUserItem, ThreatCategory } from '../types/community';
import { formatApiError } from '../services/api';

export const SubmitReportPage: React.FC = () => {
  // Form State
  const [submittedUrl, setSubmittedUrl] = useState<string>('');
  const [category, setCategory] = useState<ThreatCategory>('PHISHING');
  const [targetBrand, setTargetBrand] = useState<string>('');
  const [attackVector, setAttackVector] = useState<string>('EMAIL');
  const [description, setDescription] = useState<string>('');
  const [evidenceUrl, setEvidenceUrl] = useState<string>('');

  // Lifecycle State
  const [urlError, setUrlError] = useState<string | null>(null);
  const [descError, setDescError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [submittedReport, setSubmittedReport] = useState<CommunityReportUserItem | null>(null);

  // Validate URL Format
  const validateUrl = (url: string): boolean => {
    const trimmed = url.trim();
    if (!trimmed) {
      setUrlError('Website URL is required.');
      return false;
    }
    if (!/^https?:\/\//i.test(trimmed)) {
      setUrlError('URL must begin with http:// or https://');
      return false;
    }
    try {
      const parsed = new URL(trimmed);
      if (!parsed.hostname || parsed.hostname.length < 3) {
        setUrlError('Please provide a valid destination domain or hostname.');
        return false;
      }
    } catch {
      setUrlError('URL string is malformed or unparseable.');
      return false;
    }
    setUrlError(null);
    return true;
  };

  // Validate Description
  const validateDescription = (desc: string): boolean => {
    const trimmed = desc.trim();
    if (!trimmed) {
      setDescError('Please provide an explanation of the suspicious behavior.');
      return false;
    }
    if (trimmed.length < 20) {
      setDescError('Explanation must be at least 20 characters.');
      return false;
    }
    setDescError(null);
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(null);

    const isUrlValid = validateUrl(submittedUrl);
    const isDescValid = validateDescription(description);

    if (!isUrlValid || !isDescValid) return;

    setIsSubmitting(true);
    try {
      const result = await communityService.submitReport({
        submitted_url: submittedUrl.trim(),
        category,
        description: description.trim(),
        target_brand: targetBrand.trim() || undefined,
        attack_vector: attackVector || undefined,
        evidence_url: evidenceUrl.trim() || undefined,
      });
      setSubmittedReport(result);
    } catch (err: any) {
      const formatted = formatApiError(err);
      setServerError(formatted.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetForm = () => {
    setSubmittedUrl('');
    setCategory('PHISHING');
    setTargetBrand('');
    setAttackVector('EMAIL');
    setDescription('');
    setEvidenceUrl('');
    setSubmittedReport(null);
    setUrlError(null);
    setDescError(null);
    setServerError(null);
  };

  return (
    <div className="flex-1 py-8 md:py-12 animate-fade-in font-mono">
      <Container size="lg">
        <div className="space-y-6">
          {/* Back Nav */}
          <Link
            to="/community"
            className="inline-flex items-center space-x-2 text-xs text-[#888888] hover:text-[#F5F5F5] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>BACK TO COMMUNITY FEED</span>
          </Link>

          {/* Submission Success Screen */}
          {submittedReport ? (
            <Card pixelFrame className="p-6 sm:p-8 bg-[#101010] border border-[#292929] space-y-6 text-xs">
              <div className="space-y-2 text-center">
                <div className="w-12 h-12 bg-[#052E16] text-[#4ADE80] border border-[#166534] rounded-full mx-auto flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h2 className="text-xl font-bold uppercase text-[#F5F5F5]">
                  Threat Report Submitted
                </h2>
                <p className="text-xs text-[#888888] max-w-md mx-auto">
                  Your report has been queued for administrative moderation. Thank you for contributing
                  to collaborative web security intelligence.
                </p>
              </div>

              {/* Submitted Metadata Summary */}
              <div className="p-4 bg-[#0A0A0A] border border-[#1F1F1F] space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-[#1A1A1A]">
                  <span className="text-[#666666] uppercase">Reference ID:</span>
                  <span className="text-[#F5F5F5] font-bold select-all">{submittedReport.id}</span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-[#1A1A1A]">
                  <span className="text-[#666666] uppercase">Target Domain / URL:</span>
                  <span className="text-[#F5F5F5] truncate max-w-xs">{submittedReport.submitted_url}</span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-[#1A1A1A]">
                  <span className="text-[#666666] uppercase">Category:</span>
                  <Badge variant="malicious" size="xs">
                    {submittedReport.category}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#666666] uppercase">Initial Status:</span>
                  <Badge variant="suspicious" size="xs">
                    {submittedReport.moderation_status}
                  </Badge>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                <Button variant="secondary" size="sm" onClick={handleResetForm}>
                  SUBMIT ANOTHER URL
                </Button>
                <Link to="/community/my-reports">
                  <Button variant="primary" size="sm" rightIcon={<ExternalLink className="w-3.5 h-3.5" />}>
                    VIEW MY SUBMISSIONS
                  </Button>
                </Link>
                <Link to="/community">
                  <Button variant="ghost" size="sm">
                    RETURN TO COMMUNITY
                  </Button>
                </Link>
              </div>
            </Card>
          ) : (
            /* Submission Form */
            <div className="space-y-6">
              <div className="space-y-1">
                <h1 className="text-2xl font-bold tracking-tight text-[#F5F5F5] uppercase">
                  Report Suspicious Website
                </h1>
                <p className="text-xs text-[#888888]">
                  CONTRIBUTE TO TRUSTGUARD AI THREAT INTELLIGENCE AND SAFEGUARD THE COMMUNITY
                </p>
              </div>

              {/* Security Warning Callout */}
              <div className="p-4 bg-[#141414] border border-[#222222] flex items-start space-x-3 text-xs">
                <Info className="w-4 h-4 text-[#A1A1A1] shrink-0 mt-0.5" />
                <div className="space-y-1 text-[#888888] leading-relaxed">
                  <p>
                    <strong className="text-[#F5F5F5]">Responsible Disclosure Notice:</strong> Submitted
                    URLs are processed by static parsers and verified by security reviewers. TrustGuard
                    AI will never execute remote JavaScript or fetch active malware binaries from untrusted sources.
                  </p>
                  <p>
                    Community reports do not unilaterally determine automated ML risk verdicts.
                  </p>
                </div>
              </div>

              <Card pixelFrame className="p-6 sm:p-8 bg-[#101010] border border-[#292929]">
                <form onSubmit={handleSubmit} className="space-y-5 text-xs">
                  {serverError && (
                    <div className="p-3 bg-[#1C1212] border border-[#F87171]/40 flex items-center space-x-2 text-[#FCA5A5]">
                      <AlertTriangle className="w-4 h-4 shrink-0" />
                      <span>{serverError}</span>
                    </div>
                  )}

                  {/* Website URL */}
                  <div className="space-y-1.5">
                    <label className="text-[11px] text-[#A1A1A1] uppercase font-semibold block">
                      Target Website URL (Required)
                    </label>
                    <Input
                      value={submittedUrl}
                      onChange={(e) => {
                        setSubmittedUrl(e.target.value);
                        if (urlError) validateUrl(e.target.value);
                      }}
                      onBlur={() => validateUrl(submittedUrl)}
                      placeholder="https://suspicious-login-portal.example.com"
                      error={urlError || undefined}
                      disabled={isSubmitting}
                    />
                    <span className="text-[10px] text-[#555555] block">
                      Must begin with http:// or https://. Public domain or IP address only.
                    </span>
                  </div>

                  {/* Threat Category & Attack Vector */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[11px] text-[#A1A1A1] uppercase font-semibold block">
                        Threat Category (Required)
                      </label>
                      <select
                        value={category}
                        onChange={(e) => setCategory(e.target.value as ThreatCategory)}
                        className="w-full bg-[#121212] border border-[#292929] text-[#F5F5F5] h-10 px-3 text-xs outline-none focus:border-[#F5F5F5]"
                        disabled={isSubmitting}
                      >
                        <option value="PHISHING">Phishing / Credential Harvesting</option>
                        <option value="MALWARE_DISTRIBUTION">Malware Distribution / Dropper</option>
                        <option value="FRAUD_OR_SCAM">Financial Fraud / Crypto Scam</option>
                        <option value="SUSPICIOUS_REDIRECT">Deceptive URL Redirect</option>
                        <option value="IMPERSONATION">Brand / Corporate Impersonation</option>
                        <option value="OTHER">Other Suspicious Activity</option>
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[11px] text-[#A1A1A1] uppercase font-semibold block">
                        Observed Delivery Vector (Optional)
                      </label>
                      <select
                        value={attackVector}
                        onChange={(e) => setAttackVector(e.target.value)}
                        className="w-full bg-[#121212] border border-[#292929] text-[#F5F5F5] h-10 px-3 text-xs outline-none focus:border-[#F5F5F5]"
                        disabled={isSubmitting}
                      >
                        <option value="EMAIL">Email Phishing</option>
                        <option value="SMS">SMS Smishing</option>
                        <option value="SOCIAL_MEDIA">Social Media Link</option>
                        <option value="SEARCH_AD">Search Engine Ad (Malvertising)</option>
                        <option value="DIRECT_MESSAGE">Direct Messaging (Discord/Telegram/WhatsApp)</option>
                        <option value="WEB_REDIRECT">Infected Website Redirect</option>
                        <option value="UNKNOWN">Unknown / Other</option>
                      </select>
                    </div>
                  </div>

                  {/* Target Brand */}
                  <div className="space-y-1.5">
                    <label className="text-[11px] text-[#A1A1A1] uppercase font-semibold block">
                      Target Brand or Entity Being Impersonated (Optional)
                    </label>
                    <Input
                      value={targetBrand}
                      onChange={(e) => setTargetBrand(e.target.value)}
                      placeholder="e.g. PayPal, Microsoft, Ledger, Binance"
                      maxLength={255}
                      disabled={isSubmitting}
                    />
                  </div>

                  {/* Reason & Detailed Evidence */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-[11px] text-[#A1A1A1] uppercase font-semibold">
                        Explanation of Suspicious Indicators (Required)
                      </label>
                      <span className="text-[10px] text-[#555555]">
                        {description.length} / 1500 (Min 20 chars)
                      </span>
                    </div>
                    <textarea
                      value={description}
                      onChange={(e) => {
                        setDescription(e.target.value);
                        if (descError && e.target.value.length >= 20) setDescError(null);
                      }}
                      onBlur={() => validateDescription(description)}
                      rows={4}
                      maxLength={1500}
                      placeholder="Describe the suspicious behavior: fake login form, spoofed certificates, urgent verification demands, suspicious obfuscated scripts..."
                      className={`w-full bg-[#121212] border ${
                        descError ? 'border-[#F87171]' : 'border-[#292929]'
                      } text-[#F5F5F5] p-3 text-xs outline-none focus:border-[#F5F5F5] resize-none placeholder:text-[#555555]`}
                      disabled={isSubmitting}
                    />
                    {descError && <span className="text-[10px] text-[#F87171]">{descError}</span>}
                  </div>

                  {/* Evidence Link */}
                  <div className="space-y-1.5">
                    <label className="text-[11px] text-[#A1A1A1] uppercase font-semibold block">
                      Public Evidence / Reference Link (Optional)
                    </label>
                    <Input
                      value={evidenceUrl}
                      onChange={(e) => setEvidenceUrl(e.target.value)}
                      placeholder="https://twitter.com/threat_intel/status/... or public paste"
                      maxLength={2048}
                      disabled={isSubmitting}
                    />
                    <span className="text-[10px] text-[#555555] block">
                      Do not link to credentials, internal tokens, or executable payloads.
                    </span>
                  </div>

                  {/* Submit Action */}
                  <div className="pt-4 border-t border-[#222222] flex items-center justify-between">
                    <Link to="/community">
                      <Button type="button" variant="ghost" size="sm" disabled={isSubmitting}>
                        CANCEL
                      </Button>
                    </Link>

                    <Button
                      type="submit"
                      variant="primary"
                      size="sm"
                      isLoading={isSubmitting}
                      rightIcon={<Send className="w-3.5 h-3.5" />}
                    >
                      SUBMIT FOR REVIEW
                    </Button>
                  </div>
                </form>
              </Card>
            </div>
          )}
        </div>
      </Container>
    </div>
  );
};

export default SubmitReportPage;
