import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, Send, Shield, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { formatApiError } from '../services/api';

export const ForgotPasswordPage: React.FC = () => {
  const { forgotPassword } = useAuth();

  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setEmailError(null);

    const emailTrimmed = email.trim();
    if (!emailTrimmed) {
      setEmailError('Email address is required.');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrimmed)) {
      setEmailError('Please provide a valid email format.');
      return;
    }

    setIsSubmitting(true);
    try {
      await forgotPassword(emailTrimmed.toLowerCase());
      setSubmittedEmail(emailTrimmed.toLowerCase());
    } catch (err: any) {
      const formatted = formatApiError(err);
      setErrorMessage(formatted.message || 'Unable to request password recovery. Check network connectivity.');
    } finally {
      setIsSubmitting(false);
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
                Account Recovery
              </h1>
              <p className="text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                RESET ACCESS CREDENTIALS
              </p>
            </div>
          </div>

          {submittedEmail ? (
            <div className="space-y-5 text-center">
              <div className="p-4 bg-[#0F1710] border border-[#4ADE80]/30 space-y-2 text-xs font-mono">
                <div className="flex items-center justify-center space-x-2 text-[#4ADE80]">
                  <CheckCircle2 className="w-4 h-4" />
                  <span className="font-semibold uppercase tracking-wider">
                    Recovery Instructions Dispatched
                  </span>
                </div>
                <p className="text-[#A1A1A1] leading-relaxed">
                  If <span className="text-[#F5F5F5] font-semibold">{submittedEmail}</span> matches a registered TrustGuard AI account,
                  you will receive recovery instructions shortly.
                </p>
              </div>

              <p className="text-[11px] font-mono text-[#666666] leading-relaxed">
                To prevent account enumeration, we do not indicate whether an email is registered in our records.
                Check your spam folder if the link does not appear within 5 minutes.
              </p>

              <div className="pt-2">
                <Link to="/login">
                  <Button variant="secondary" className="w-full" leftIcon={<ArrowLeft className="w-4 h-4" />}>
                    RETURN TO AUTHENTICATION
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <>
              {errorMessage && (
                <div
                  className="p-3 bg-[#1C1212] border border-[#F87171]/40 flex items-start space-x-2.5 text-xs text-[#FCA5A5] font-mono leading-relaxed"
                  role="alert"
                >
                  <AlertTriangle className="w-4 h-4 text-[#F87171] shrink-0 mt-0.5" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <p className="text-xs text-[#A1A1A1] leading-relaxed">
                Provide your registered analyst email address. If verified, a secure time-limited password reset link
                will be generated.
              </p>

              <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                <Input
                  label="REGISTERED EMAIL"
                  type="email"
                  placeholder="analyst@domain.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (emailError) setEmailError(null);
                  }}
                  error={emailError || undefined}
                  leftElement={<Mail className="w-4 h-4" />}
                  autoComplete="email"
                  disabled={isSubmitting}
                  autoFocus
                />

                <Button
                  type="submit"
                  className="w-full"
                  isLoading={isSubmitting}
                  disabled={isSubmitting}
                  rightIcon={<Send className="w-4 h-4" />}
                >
                  {isSubmitting ? 'DISPATCHING...' : 'DISPATCH RECOVERY LINK'}
                </Button>
              </form>

              <div className="pt-3 border-t border-[#292929] text-center text-xs font-mono text-[#666666]">
                <Link to="/login" className="inline-flex items-center space-x-1.5 text-[#A1A1A1] hover:text-[#F5F5F5] transition-colors">
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>BACK TO SIGN IN</span>
                </Link>
              </div>
            </>
          )}
        </Card>
      </Container>
    </div>
  );
};

export default ForgotPasswordPage;

