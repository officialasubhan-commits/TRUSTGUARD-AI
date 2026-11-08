import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';
import { validateAndNormalizeUrl } from '../../utils/validators';
import { Button } from '../common/Button';
import { Card } from '../common/Card';

export const HomepageScanner: React.FC = () => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleScanSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const validation = validateAndNormalizeUrl(url);
    if (!validation.isValid) {
      setError(validation.error || 'Please enter a valid URL.');
      return;
    }

    setIsLoading(true);

    // Navigate to dedicated scanner route passing the normalized target URL
    navigate(`/scan?url=${encodeURIComponent(validation.normalizedUrl)}`);
  };

  return (
    <Card
      id="scanner"
      variant="elevated"
      pixelFrame
      className="w-full max-w-3xl mx-auto p-6 md:p-8 space-y-4 border border-[#383838]"
    >
      <div className="flex items-center justify-between text-xs font-mono text-[#666666] pb-2 border-b border-[#292929]">
        <span className="flex items-center space-x-1.5 text-[#A1A1A1]">
          <ShieldCheck className="w-3.5 h-3.5 text-[#F5F5F5]" />
          <span>INSTANT WEB THREAT INSPECTION</span>
        </span>
        <span className="text-[10px] tracking-wider uppercase">GUEST OR AUTHENTICATED ACCESS</span>
      </div>

      <form onSubmit={handleScanSubmit} className="space-y-3">
        <div className="flex flex-col sm:flex-row items-stretch gap-2">
          <div className="relative flex-1">
            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none text-[#666666]">
              <Search className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                if (error) setError(null);
              }}
              placeholder="Enter a website URL to analyse..."
              aria-label="Website URL to analyse"
              className="w-full h-12 pl-10 pr-4 bg-[#101010] border border-[#292929] hover:border-[#383838] focus:border-[#F5F5F5] text-sm text-[#F5F5F5] font-mono placeholder-[#666666] transition-colors focus:outline-none"
            />
          </div>

          <Button
            type="submit"
            size="lg"
            isLoading={isLoading}
            rightIcon={<ArrowRight className="w-4 h-4" />}
            className="h-12 px-8 shrink-0"
          >
            ANALYSE URL
          </Button>
        </div>

        {error && (
          <div className="flex items-start space-x-2 p-3 bg-[#450A0A]/30 border border-[#991B1B]/60 text-xs font-mono text-[#F87171]">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </form>

      {/* Trust & Capability Assurance Ticker */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-[#292929] text-[10px] font-mono text-[#666666]">
        <div>• SSRF DEFENSE ACTIVE</div>
        <div>• VIRUSTOTAL V3 TELEMETRY</div>
        <div>• RF MACHINE LEARNING</div>
        <div>• SSL/TLS CERT AUDIT</div>
      </div>
    </Card>
  );
};

