import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Lock, Mail, ArrowRight, Shield, AlertTriangle, CheckCircle2, RotateCw } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { formatApiError } from '../services/api';

const GoogleIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none">
    <path
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      fill="#4285F4"
    />
    <path
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      fill="#34A853"
    />
    <path
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      fill="#FBBC05"
    />
    <path
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      fill="#EA4335"
    />
  </svg>
);

export const LoginPage: React.FC = () => {
  const { login, loginWithGoogle, resendVerification } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState(() => localStorage.getItem('trustguard_remembered_email') || '');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [isUnconfirmed, setIsUnconfirmed] = useState(false);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Parse state passed from redirect or callback
  useEffect(() => {
    const state = location.state as { from?: { pathname: string }; errorMessage?: string; infoMessage?: string } | null;
    if (state?.errorMessage) {
      setErrorMessage(state.errorMessage);
    }
    if (state?.infoMessage) {
      setSuccessMessage(state.infoMessage);
    }
  }, [location.state]);

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    const emailTrimmed = email.trim();

    if (!emailTrimmed) {
      errors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrimmed)) {
      errors.email = 'Please provide a valid email format.';
    }

    if (!password) {
      errors.password = 'Password is required.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsUnconfirmed(false);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await login({
        email: email.trim().toLowerCase(),
        password,
      });

      if (rememberMe) {
        localStorage.setItem('trustguard_remembered_email', email.trim().toLowerCase());
      } else {
        localStorage.removeItem('trustguard_remembered_email');
      }

      // Return user to intended destination or default to dashboard
      const intendedDestination = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';
      navigate(intendedDestination, { replace: true });
    } catch (err: any) {
      const formatted = formatApiError(err);
      if (formatted.code === 'INVALID_CREDENTIALS') {
        setErrorMessage('Invalid email or password. Please verify your credentials and try again.');
      } else if (formatted.code === 'EMAIL_NOT_CONFIRMED') {
        setIsUnconfirmed(true);
        setErrorMessage('Email verification required before signing in. Please check your inbox or request a new verification link.');
      } else if (formatted.code === 'RATE_LIMIT_EXCEEDED') {
        setErrorMessage('Too many login attempts. Please wait a few moments before trying again.');
      } else if (formatted.code === 'NETWORK_ERROR') {
        setErrorMessage('Unable to connect to the TrustGuard AI backend server. Please verify network status.');
      } else {
        setErrorMessage(formatted.message || 'Authentication failed. Please verify your credentials.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsGoogleLoading(true);
    try {
      const redirectUri = `${window.location.origin}/auth/callback`;
      await loginWithGoogle(redirectUri);
    } catch (err: any) {
      const formatted = formatApiError(err);
      setErrorMessage(
        formatted.message || 'Unable to initiate Google sign-in. Please verify provider configuration.'
      );
      setIsGoogleLoading(false);
    }
  };

  const handleResend = async () => {
    const trimmed = email.trim().toLowerCase();
    if (!trimmed) {
      setErrorMessage('Please enter your email address to receive a new verification link.');
      return;
    }

    setIsResending(true);
    try {
      const msg = await resendVerification(trimmed);
      setSuccessMessage(msg || 'Confirmation email dispatched. Please check your inbox.');
      setErrorMessage(null);
    } catch (err: any) {
      const formatted = formatApiError(err);
      setErrorMessage(formatted.message || 'Failed to dispatch verification email. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center py-12 md:py-20 px-4">
      <Container size="sm">
        <Card pixelFrame className="p-6 md:p-8 space-y-6">
          {/* Header & Branding */}
          <div className="space-y-3 text-center">
            <div className="w-10 h-10 mx-auto bg-[#141414] border border-[#292929] flex items-center justify-center">
              <Shield className="w-5 h-5 text-[#F5F5F5]" />
            </div>
            <div className="space-y-1">
              <h1 className="text-2xl font-light tracking-tight text-[#F5F5F5]">
                Authentication Portal
              </h1>
              <p className="text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                SIGN IN TO ACCESS SCAN HISTORIES & TELEMETRY
              </p>
            </div>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div
              className="p-3 bg-[#1C1212] border border-[#F87171]/40 flex flex-col gap-2 text-xs text-[#FCA5A5] font-mono leading-relaxed"
              role="alert"
            >
              <div className="flex items-start space-x-2.5">
                <AlertTriangle className="w-4 h-4 text-[#F87171] shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
              {isUnconfirmed && (
                <div className="pl-6 pt-1">
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={isResending}
                    className="inline-flex items-center space-x-1.5 text-[11px] text-[#F5F5F5] underline hover:text-white"
                  >
                    <RotateCw className={`w-3 h-3 ${isResending ? 'animate-spin' : ''}`} />
                    <span>{isResending ? 'DISPATCHING EMAIL...' : 'RESEND VERIFICATION EMAIL'}</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Success Banner */}
          {successMessage && (
            <div
              className="p-3 bg-[#0F1710] border border-[#4ADE80]/30 flex items-start space-x-2.5 text-xs text-[#4ADE80] font-mono leading-relaxed"
              role="status"
            >
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Email / Password Form */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <Input
              label="EMAIL ADDRESS"
              type="email"
              placeholder="analyst@domain.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (fieldErrors.email) {
                  setFieldErrors((prev) => ({ ...prev, email: '' }));
                }
              }}
              error={fieldErrors.email}
              leftElement={<Mail className="w-4 h-4" />}
              autoComplete="email"
              disabled={isSubmitting || isGoogleLoading}
              autoFocus
            />

            <Input
              label="PASSWORD"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (fieldErrors.password) {
                  setFieldErrors((prev) => ({ ...prev, password: '' }));
                }
              }}
              error={fieldErrors.password}
              leftElement={<Lock className="w-4 h-4" />}
              autoComplete="current-password"
              disabled={isSubmitting || isGoogleLoading}
            />

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between text-xs font-mono text-[#A1A1A1] pt-1">
              <label className="flex items-center space-x-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  disabled={isSubmitting || isGoogleLoading}
                  className="w-3.5 h-3.5 rounded-none bg-[#101010] border-[#292929] text-[#F5F5F5] focus:ring-0 focus:ring-offset-0"
                />
                <span>REMEMBER EMAIL</span>
              </label>

              <Link
                to="/forgot-password"
                className="text-[#A1A1A1] hover:text-[#F5F5F5] transition-colors underline-offset-4 hover:underline"
              >
                FORGOT PASSWORD?
              </Link>
            </div>

            <Button
              type="submit"
              className="w-full"
              isLoading={isSubmitting}
              disabled={isSubmitting || isGoogleLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              {isSubmitting ? 'AUTHENTICATING...' : 'AUTHENTICATE'}
            </Button>
          </form>

          {/* OR Divider */}
          <div className="relative flex items-center justify-center py-1">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#222222]" />
            </div>
            <div className="relative px-3 bg-[#0A0A0A] text-[10px] font-mono text-[#666666] uppercase tracking-wider">
              OR
            </div>
          </div>

          {/* Google Sign-In Button */}
          <div>
            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={isSubmitting || isGoogleLoading}
              className="w-full h-10 px-4 flex items-center justify-center space-x-3 bg-[#101010] hover:bg-[#161616] border border-[#292929] hover:border-[#383838] text-xs font-mono font-medium text-[#F5F5F5] transition-colors focus:outline-none focus:ring-1 focus:ring-[#F5F5F5] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <GoogleIcon className="w-4 h-4 shrink-0" />
              <span>{isGoogleLoading ? 'CONNECTING TO GOOGLE...' : 'Continue with Google'}</span>
            </button>
          </div>

          {/* Navigation & Registration Link */}
          <div className="space-y-3 pt-3 border-t border-[#222222] text-center text-xs font-mono">
            <div className="text-[#666666]">
              <span>NO ACCOUNT? </span>
              <Link to="/register" className="text-[#F5F5F5] hover:underline font-semibold ml-1">
                REGISTER NEW ACCESS
              </Link>
            </div>

            <div className="text-[11px] text-[#555555]">
              Looking to test a URL?{' '}
              <Link to="/scan" className="text-[#888888] hover:text-[#CCCCCC] underline">
                Guest scanning
              </Link>{' '}
              is available without authentication.
            </div>
          </div>
        </Card>
      </Container>
    </div>
  );
};

export default LoginPage;
