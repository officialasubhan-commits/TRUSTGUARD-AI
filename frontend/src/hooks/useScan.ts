import { useState, useCallback, useRef, useEffect } from 'react';
import { scanService, ScanApiError } from '../services/scanService';
import { ScanResult } from '../types/scan';
import { validateAndNormalizeUrl } from '../utils/validators';

export type ScanStep =
  | 'IDLE'
  | 'VALIDATING'
  | 'INITIALIZING'
  | 'ANALYSING_STRUCTURE'
  | 'QUERYING_THREAT_FEEDS'
  | 'EVALUATING_ML_MODEL'
  | 'AUDITING_SSL_CERT'
  | 'SYNTHESIZING_TRUST_SCORE'
  | 'COMPLETE'
  | 'ERROR';

export interface UseScanReturn {
  scanResult: ScanResult | null;
  isLoading: boolean;
  error: ScanApiError | null;
  scanStep: ScanStep;
  statusMessage: string;
  startScan: (rawUrl: string) => Promise<ScanResult | null>;
  cancelScan: () => void;
  resetScan: () => void;
  clearError: () => void;
}

export function useScan(): UseScanReturn {
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ScanApiError | null>(null);
  const [scanStep, setScanStep] = useState<ScanStep>('IDLE');
  const [statusMessage, setStatusMessage] = useState<string>('Ready for analysis.');

  const abortControllerRef = useRef<AbortController | null>(null);
  const stepTimerRef = useRef<number[]>([]);

  const clearStepTimers = () => {
    stepTimerRef.current.forEach((t) => window.clearTimeout(t));
    stepTimerRef.current = [];
  };

  useEffect(() => {
    return () => {
      // Abort in-flight requests and clear timers on component unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      clearStepTimers();
    };
  }, []);

  const cancelScan = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    clearStepTimers();
    setIsLoading(false);
    setScanStep('IDLE');
    setStatusMessage('Analysis cancelled by user.');
  }, []);

  const resetScan = useCallback(() => {
    cancelScan();
    setScanResult(null);
    setError(null);
    setScanStep('IDLE');
    setStatusMessage('Ready for analysis.');
  }, [cancelScan]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const startScan = useCallback(
    async (rawUrl: string): Promise<ScanResult | null> => {
      // 1. Client-side pre-flight validation
      const validation = validateAndNormalizeUrl(rawUrl);
      if (!validation.isValid) {
        const clientError: ScanApiError = {
          code: 'INVALID_URL',
          message: validation.error || 'Please enter a valid website address.',
          status: 400,
        };
        setError(clientError);
        setScanStep('ERROR');
        setStatusMessage(clientError.message);
        return null;
      }

      // Reset state and setup abort controller
      setError(null);
      setScanResult(null);
      setIsLoading(true);
      clearStepTimers();

      const controller = new AbortController();
      abortControllerRef.current = controller;

      setScanStep('INITIALIZING');
      setStatusMessage(`Initiating multi-layer analysis for ${validation.normalizedUrl}...`);

      // Progress status steps during backend request
      const timer1 = window.setTimeout(() => {
        setScanStep('ANALYSING_STRUCTURE');
        setStatusMessage('Extracting URL lexical anomalies & path entropy...');
      }, 350);

      const timer2 = window.setTimeout(() => {
        setScanStep('QUERYING_THREAT_FEEDS');
        setStatusMessage('Evaluating VirusTotal multi-vendor consensus & reputation feeds...');
      }, 750);

      const timer3 = window.setTimeout(() => {
        setScanStep('EVALUATING_ML_MODEL');
        setStatusMessage('Executing Random Forest v1 phishing classification model...');
      }, 1200);

      const timer4 = window.setTimeout(() => {
        setScanStep('AUDITING_SSL_CERT');
        setStatusMessage('Performing cryptographic TLS handshake & certificate trust audit...');
      }, 1600);

      const timer5 = window.setTimeout(() => {
        setScanStep('SYNTHESIZING_TRUST_SCORE');
        setStatusMessage('Synthesizing evidence-based Digital Trust Score & overrides...');
      }, 2000);

      stepTimerRef.current = [timer1, timer2, timer3, timer4, timer5];

      try {
        const result = await scanService.submitScan(validation.normalizedUrl, controller.signal);
        clearStepTimers();

        setScanResult(result);
        setScanStep('COMPLETE');
        setStatusMessage('Analysis complete. Security telemetry synthesized.');
        setIsLoading(false);
        return result;
      } catch (err: any) {
        clearStepTimers();
        setIsLoading(false);

        if (err?.code === 'SCAN_CANCELLED') {
          setScanStep('IDLE');
          setStatusMessage('Analysis cancelled by user.');
          return null;
        }

        const formattedError: ScanApiError = {
          code: err?.code || 'SCAN_FAILED',
          message:
            err?.message ||
            'Unable to complete security assessment. Please check target URL and backend connection.',
          status: err?.status || 500,
        };

        setError(formattedError);
        setScanStep('ERROR');
        setStatusMessage(formattedError.message);
        return null;
      }
    },
    []
  );

  return {
    scanResult,
    isLoading,
    error,
    scanStep,
    statusMessage,
    startScan,
    cancelScan,
    resetScan,
    clearError,
  };
}

export default useScan;

