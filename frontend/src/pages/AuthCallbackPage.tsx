import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, AlertTriangle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { formatApiError } from '../services/api';

export const AuthCallbackPage: React.FC = () => {
  const { handleOAuthCallback } = useAuth();
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const processedRef = useRef(false);

  useEffect(() => {
    if (processedRef.current) return;
    processedRef.current = true;

    const processAuth = async () => {
      // 1. Inspect Search Query Parameters (PKCE flow or direct OAuth errors)
      const searchParams = new URLSearchParams(window.location.search);
      const code = searchParams.get('code');
      const error = searchParams.get('error');
      const errorDescription = searchParams.get('error_description');

      // 2. Inspect Hash Fragment Parameters (Implicit token flow)
      const rawHash = window.location.hash.startsWith('#')
        ? window.location.hash.substring(1)
        : window.location.hash;
      const hashParams = new URLSearchParams(rawHash);
      const accessToken = hashParams.get('access_token');
      const refreshToken = hashParams.get('refresh_token');
      const hashError = hashParams.get('error');
      const hashErrorDescription = hashParams.get('error_description');

      // Handle Provider Cancellation or Denials
      const authError = error || hashError;
      const authErrorDesc = errorDescription || hashErrorDescription;

      if (authError) {
        let msg = 'Google authentication was cancelled or could not be completed.';
        if (authErrorDesc) {
          msg = authErrorDesc.replace(/\+/g, ' ');
        }
        navigate('/login', { state: { errorMessage: msg }, replace: true });
        return;
      }

      // Check if credentials exist
      if (!code && !accessToken) {
        navigate('/login', {
          state: { errorMessage: 'No authorization credentials received from identity provider.' },
          replace: true,
        });
        return;
      }

      try {
        await handleOAuthCallback({
          code: code || undefined,
          access_token: accessToken || undefined,
          refresh_token: refreshToken || undefined,
        });

        // Clean URL fragment and redirect to dashboard
        window.history.replaceState(null, '', window.location.pathname);
        navigate('/dashboard', { replace: true });
      } catch (err: any) {
        const formatted = formatApiError(err);
        setErrorMessage(
          formatted.message || 'Failed to complete Google authentication. Please try again.'
        );
        setTimeout(() => {
          navigate('/login', {
            state: {
              errorMessage:
                formatted.message || 'Google session establishment failed. Please try again.',
            },
            replace: true,
          });
        }, 3000);
      }
    };

    processAuth();
  }, [handleOAuthCallback, navigate]);

  return (
    <div className="flex-1 flex items-center justify-center py-16 md:py-24 px-4 bg-[#080808]">
      <Container size="sm">
        <Card pixelFrame className="p-8 text-center space-y-6">
          <div className="w-12 h-12 mx-auto bg-[#121212] border border-[#292929] flex items-center justify-center">
            {errorMessage ? (
              <AlertTriangle className="w-6 h-6 text-[#F87171]" />
            ) : (
              <Shield className="w-6 h-6 text-[#F5F5F5] animate-pulse" />
            )}
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-mono uppercase tracking-wider text-[#F5F5F5]">
              {errorMessage ? 'AUTHENTICATION FAILED' : 'AUTHENTICATING IDENTITY'}
            </h2>
            <p className="text-xs font-mono text-[#A1A1A1] leading-relaxed">
              {errorMessage || 'Establishing secure session with TrustGuard AI threat intelligence engine...'}
            </p>
          </div>

          {!errorMessage && (
            <div className="pt-2 flex justify-center">
              <div className="inline-flex items-center space-x-1.5 px-3 py-1 bg-[#141414] border border-[#222222] text-[11px] font-mono text-[#4ADE80]">
                <span className="w-2 h-2 rounded-full bg-[#4ADE80] animate-ping" />
                <span>EXCHANGING SECURITY TOKENS</span>
              </div>
            </div>
          )}
        </Card>
      </Container>
    </div>
  );
};

export default AuthCallbackPage;

