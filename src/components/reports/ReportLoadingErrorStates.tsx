import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  RotateCcw,
  AlertTriangle,
  ArrowLeft,
  Clock,
  ShieldAlert,
  ServerCrash,
  Lock,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';

interface ReportErrorStateProps {
  code: string;
  message: string;
  onRetry?: () => void;
}

export const ReportErrorState: React.FC<ReportErrorStateProps> = ({ code, message, onRetry }) => {
  const navigate = useNavigate();

  const getErrorIcon = () => {
    switch (code) {
      case 'SCAN_NOT_FOUND':
        return <ShieldAlert className="w-8 h-8 text-[#FBBF24]" />;
      case 'UNAUTHORIZED':
      case 'FORBIDDEN':
        return <Lock className="w-8 h-8 text-[#FBBF24]" />;
      case 'NETWORK_ERROR':
      case 'TIMEOUT_ERROR':
        return <ServerCrash className="w-8 h-8 text-[#F87171]" />;
      default:
        return <AlertTriangle className="w-8 h-8 text-[#F87171]" />;
    }
  };

  return (
    <Card pixelFrame className="p-8 sm:p-12 text-center space-y-6 max-w-xl mx-auto my-12">
      <div className="flex justify-center">{getErrorIcon()}</div>

      <div className="space-y-2">
        <h2 className="text-xl font-light text-[#F5F5F5] font-mono uppercase tracking-wide">
          SECURITY REPORT UNAVAILABLE
        </h2>
        <div className="text-xs font-mono text-[#F87171] uppercase tracking-wider">
          ERROR CODE: [{code}]
        </div>
        <p className="text-xs font-mono text-[#A1A1A1] leading-relaxed max-w-md mx-auto pt-2">
          {message}
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
        {onRetry && (
          <Button
            variant="secondary"
            size="sm"
            onClick={onRetry}
            leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            RETRY AUDIT LOOKUP
          </Button>
        )}

        <Button
          variant="primary"
          size="sm"
          onClick={() => navigate('/scan')}
          leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}
        >
          RETURN TO SCANNER
        </Button>
      </div>
    </Card>
  );
};

interface ReportProcessingStateProps {
  elapsedSeconds: number;
  onCancel?: () => void;
}

export const ReportProcessingState: React.FC<ReportProcessingStateProps> = ({
  elapsedSeconds,
  onCancel,
}) => {
  return (
    <Card pixelFrame className="p-8 sm:p-12 text-center space-y-6 max-w-xl mx-auto my-12">
      <div className="flex justify-center">
        <div className="w-12 h-12 border-2 border-[#292929] border-t-[#F5F5F5] rounded-none animate-spin" />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-center space-x-2 text-xs font-mono text-[#4ADE80]">
          <span className="w-2 h-2 bg-[#4ADE80] animate-ping" />
          <span className="font-semibold uppercase tracking-wider">
            ANALYSIS PIPELINE ACTIVE
          </span>
        </div>
        <h2 className="text-xl font-light text-[#F5F5F5] font-mono">
          Security Engines Evaluating Target
        </h2>
        <p className="text-xs font-mono text-[#A1A1A1] leading-relaxed max-w-md mx-auto">
          Synchronizing multi-vendor threat intelligence, executing machine learning feature extraction,
          and inspecting TLS certificate chains.
        </p>
      </div>

      <div className="flex items-center justify-center space-x-2 text-xs font-mono text-[#666666]">
        <Clock className="w-3.5 h-3.5" />
        <span>ELAPSED: {elapsedSeconds}s</span>
      </div>

      {onCancel && (
        <div className="pt-2">
          <Button variant="secondary" size="sm" onClick={onCancel}>
            CANCEL POLLING
          </Button>
        </div>
      )}
    </Card>
  );
};

export const ReportLoadingSkeleton: React.FC = () => {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 bg-[#141414] border border-[#222222] w-1/3" />
      <div className="h-40 bg-[#101010] border border-[#292929]" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="h-48 bg-[#141414] border border-[#222222]" />
        <div className="h-48 bg-[#141414] border border-[#222222]" />
        <div className="h-48 bg-[#141414] border border-[#222222]" />
        <div className="h-48 bg-[#141414] border border-[#222222]" />
      </div>
      <div className="h-32 bg-[#101010] border border-[#222222]" />
    </div>
  );
};

