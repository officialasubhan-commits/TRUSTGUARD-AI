import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail, User as UserIcon, ArrowRight, Shield, AlertTriangle, Check, X } from 'lucide-react';
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

export const RegisterPage: React.FC = () => {
  const { register, loginWithGoogle } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Real-time password requirement metrics matching backend validation
  const hasMinLength = password.length >= 8;
  const hasLetter = /[a-zA-Z]/.test(password);
  const hasNumberOrSymbol = /[\d\W_]/.test(password);
  const passwordsMatch = password.length > 0 && password === confirmPassword;

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    const nameTrimmed = fullName.trim();
    const emailTrimmed = email.trim();

    if (!nameTrimmed) {
      errors.fullName = 'Full name is required.';
    } else if (nameTrimmed.length < 2) {
      errors.fullName = 'Full name must be at least 2 characters.';
    }

    if (!emailTrimmed) {
      errors.email = 'Email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrimmed)) {
      errors.email = 'Please provide a valid email format.';
    }

    if (!password) {
      errors.password = 'Password is required.';
    } else if (!hasMinLength || !hasLetter || !hasNumberOrSymbol) {
      errors.password = 'Password does not meet required security criteria.';
    }

    if (!confirmPassword) {
      errors.confirmPassword = 'Confirmation password is required.';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
    }

    if (!acceptTerms) {
      errors.terms = 'You must accept the terms of service and privacy agreement to register.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        email: email.trim().toLowerCase(),
        full_name: fullName.trim(),
        password,
        confirm_password: confirmPassword,
      });

      // Navigate to dashboard upon registration
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      const formatted = formatApiError(err);
      if (formatted.code === 'USER_ALREADY_EXISTS') {
        setErrorMessage('A user with this email address already exists. Please log in or use a different address.');
      } else if (formatted.code === 'VALIDATION_ERROR') {
        setErrorMessage(formatted.message || 'Validation error. Please check your form input.');
      } else {
        setErrorMessage(formatted.message || 'Registration failed. Please check network connectivity.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleSignUp = async () => {
    setErrorMessage(null);
    setIsGoogleLoading(true);
    try {
      const redirectUri = `${window.location.origin}/auth/callback`;
      await loginWithGoogle(redirectUri);
    } catch (err: any) {
      const formatted = formatApiError(err);
      setErrorMessage(
        formatted.message || 'Unable to initiate Google registration. Please verify provider configuration.'
      );
      setIsGoogleLoading(false);
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
                Register Account
              </h1>
              <p className="text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                CREATE SECURITY ANALYST CREDENTIALS
              </p>
            </div>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div
              className="p-3 bg-[#1C1212] border border-[#F87171]/40 flex items-start space-x-2.5 text-xs text-[#FCA5A5] font-mono leading-relaxed"
              role="alert"
            >
              <AlertTriangle className="w-4 h-4 text-[#F87171] shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <Input
              label="FULL NAME"
              type="text"
              placeholder="Alice Analyst"
              value={fullName}
              onChange={(e) => {
                setFullName(e.target.value);
                if (fieldErrors.fullName) {
                  setFieldErrors((prev) => ({ ...prev, fullName: '' }));
                }
              }}
              error={fieldErrors.fullName}
              leftElement={<UserIcon className="w-4 h-4" />}
              autoComplete="name"
              disabled={isSubmitting || isGoogleLoading}
              autoFocus
            />

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
              autoComplete="new-password"
              disabled={isSubmitting || isGoogleLoading}
              hint="Minimum 8 characters with at least 1 letter and 1 number/symbol."
            />

            {/* Visual Password Strength Indicators */}
            <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
              <div
                className={`px-2 py-1 border flex items-center justify-center space-x-1 ${
                  hasMinLength
                    ? 'border-[#4ADE80]/40 text-[#4ADE80] bg-[#0E1E12]'
                    : 'border-[#292929] text-[#666666] bg-[#121212]'
                }`}
              >
                {hasMinLength ? <Check className="w-3 h-3" /> : <span>•</span>}
                <span>8+ CHARS</span>
              </div>

              <div
                className={`px-2 py-1 border flex items-center justify-center space-x-1 ${
                  hasLetter
                    ? 'border-[#4ADE80]/40 text-[#4ADE80] bg-[#0E1E12]'
                    : 'border-[#292929] text-[#666666] bg-[#121212]'
                }`}
              >
                {hasLetter ? <Check className="w-3 h-3" /> : <span>•</span>}
                <span>1+ LETTER</span>
              </div>

              <div
                className={`px-2 py-1 border flex items-center justify-center space-x-1 ${
                  hasNumberOrSymbol
                    ? 'border-[#4ADE80]/40 text-[#4ADE80] bg-[#0E1E12]'
                    : 'border-[#292929] text-[#666666] bg-[#121212]'
                }`}
              >
                {hasNumberOrSymbol ? <Check className="w-3 h-3" /> : <span>•</span>}
                <span>NUM / SYMBOL</span>
              </div>
            </div>

            <Input
              label="CONFIRM PASSWORD"
              type="password"
              placeholder="••••••••••••"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (fieldErrors.confirmPassword) {
                  setFieldErrors((prev) => ({ ...prev, confirmPassword: '' }));
                }
              }}
              error={fieldErrors.confirmPassword}
              leftElement={<Lock className="w-4 h-4" />}
              autoComplete="new-password"
              disabled={isSubmitting || isGoogleLoading}
            />

            {/* Match status helper if user started typing confirm password */}
            {confirmPassword.length > 0 && (
              <div className="flex items-center space-x-2 text-[11px] font-mono">
                {passwordsMatch ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-[#4ADE80]" />
                    <span className="text-[#4ADE80]">Passwords match</span>
                  </>
                ) : (
                  <>
                    <X className="w-3.5 h-3.5 text-[#F87171]" />
                    <span className="text-[#F87171]">Passwords do not match</span>
                  </>
                )}
              </div>
            )}

            {/* Terms Acceptance */}
            <div className="pt-1">
              <label className="flex items-start space-x-2.5 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={acceptTerms}
                  onChange={(e) => {
                    setAcceptTerms(e.target.checked);
                    if (fieldErrors.terms) {
                      setFieldErrors((prev) => ({ ...prev, terms: '' }));
                    }
                  }}
                  disabled={isSubmitting || isGoogleLoading}
                  className="w-4 h-4 mt-0.5 rounded-none bg-[#101010] border-[#292929] text-[#F5F5F5] focus:ring-0 focus:ring-offset-0"
                />
                <span className="text-xs font-mono text-[#A1A1A1] leading-relaxed">
                  I accept the security policies and terms governing automated threat telemetry analysis.
                </span>
              </label>
              {fieldErrors.terms && (
                <p className="text-xs font-mono text-[#F87171] mt-1 pl-6">{fieldErrors.terms}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              isLoading={isSubmitting}
              disabled={isSubmitting || isGoogleLoading}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              {isSubmitting ? 'CREATING ACCOUNT...' : 'CREATE ACCOUNT'}
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
              onClick={handleGoogleSignUp}
              disabled={isSubmitting || isGoogleLoading}
              className="w-full h-10 px-4 flex items-center justify-center space-x-3 bg-[#101010] hover:bg-[#161616] border border-[#292929] hover:border-[#383838] text-xs font-mono font-medium text-[#F5F5F5] transition-colors focus:outline-none focus:ring-1 focus:ring-[#F5F5F5] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <GoogleIcon className="w-4 h-4 shrink-0" />
              <span>{isGoogleLoading ? 'CONNECTING TO GOOGLE...' : 'Continue with Google'}</span>
            </button>
          </div>

          {/* Navigation & Login Link */}
          <div className="pt-3 border-t border-[#222222] text-center text-xs font-mono text-[#666666]">
            <span>ALREADY REGISTERED? </span>
            <Link to="/login" className="text-[#F5F5F5] hover:underline font-semibold ml-1">
              AUTHENTICATE HERE
            </Link>
          </div>
        </Card>
      </Container>
    </div>
  );
};

export default RegisterPage;
