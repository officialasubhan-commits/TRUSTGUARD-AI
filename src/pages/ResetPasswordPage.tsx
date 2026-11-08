import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, ArrowRight, Shield, CheckCircle2, AlertTriangle, Check, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { formatApiError } from '../services/api';

export const ResetPasswordPage: React.FC = () => {
  const { resetPassword } = useAuth();
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const hasMinLength = newPassword.length >= 8;
  const hasLetter = /[a-zA-Z]/.test(newPassword);
  const hasNumberOrSymbol = /[\d\W_]/.test(newPassword);
  const passwordsMatch = newPassword.length > 0 && newPassword === confirmNewPassword;

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    if (!newPassword) {
      errors.newPassword = 'New password is required.';
    } else if (!hasMinLength || !hasLetter || !hasNumberOrSymbol) {
      errors.newPassword = 'Password does not meet required complexity standards.';
    }

    if (!confirmNewPassword) {
      errors.confirmNewPassword = 'Confirm your new password.';
    } else if (newPassword !== confirmNewPassword) {
      errors.confirmNewPassword = 'Passwords do not match.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await resetPassword({
        new_password: newPassword,
        confirm_new_password: confirmNewPassword,
      });
      setSuccess(true);
      setTimeout(() => {
        navigate('/login', { replace: true });
      }, 3000);
    } catch (err: any) {
      const formatted = formatApiError(err);
      if (formatted.status === 401) {
        setErrorMessage('Password reset link is expired or invalid. Please request a new link.');
      } else {
        setErrorMessage(formatted.message || 'Unable to update password. Please try again.');
      }
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
                Set New Password
              </h1>
              <p className="text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                ESTABLISH REPLACEMENT ACCESS CREDENTIALS
              </p>
            </div>
          </div>

          {success ? (
            <div className="space-y-4 text-center">
              <div className="p-4 bg-[#0F1710] border border-[#4ADE80]/30 space-y-2 text-xs font-mono">
                <div className="flex items-center justify-center space-x-2 text-[#4ADE80]">
                  <CheckCircle2 className="w-4 h-4" />
                  <span className="font-semibold uppercase tracking-wider">
                    Password Updated Successfully
                  </span>
                </div>
                <p className="text-[#A1A1A1] leading-relaxed">
                  Your credentials have been securely refreshed. Redirecting you to the authentication portal...
                </p>
              </div>

              <div className="pt-2">
                <Link to="/login">
                  <Button className="w-full" rightIcon={<ArrowRight className="w-4 h-4" />}>
                    PROCEED TO SIGN IN
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

              <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                <Input
                  label="NEW PASSWORD"
                  type="password"
                  placeholder="••••••••••••"
                  value={newPassword}
                  onChange={(e) => {
                    setNewPassword(e.target.value);
                    if (fieldErrors.newPassword) {
                      setFieldErrors((prev) => ({ ...prev, newPassword: '' }));
                    }
                  }}
                  error={fieldErrors.newPassword}
                  leftElement={<Lock className="w-4 h-4" />}
                  autoComplete="new-password"
                  disabled={isSubmitting}
                  autoFocus
                />

                {/* Password Criteria */}
                <div className="p-3 bg-[#0D0D0D] border border-[#222222] space-y-1.5 text-[11px] font-mono">
                  <span className="text-[#666666] uppercase block mb-1">PASSWORD REQUIREMENTS:</span>
                  <div className="flex items-center space-x-2">
                    {hasMinLength ? (
                      <Check className="w-3.5 h-3.5 text-[#4ADE80]" />
                    ) : (
                      <X className="w-3.5 h-3.5 text-[#666666]" />
                    )}
                    <span className={hasMinLength ? 'text-[#F5F5F5]' : 'text-[#666666]'}>
                      Minimum 8 characters
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {hasLetter ? (
                      <Check className="w-3.5 h-3.5 text-[#4ADE80]" />
                    ) : (
                      <X className="w-3.5 h-3.5 text-[#666666]" />
                    )}
                    <span className={hasLetter ? 'text-[#F5F5F5]' : 'text-[#666666]'}>
                      Contains at least one letter
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {hasNumberOrSymbol ? (
                      <Check className="w-3.5 h-3.5 text-[#4ADE80]" />
                    ) : (
                      <X className="w-3.5 h-3.5 text-[#666666]" />
                    )}
                    <span className={hasNumberOrSymbol ? 'text-[#F5F5F5]' : 'text-[#666666]'}>
                      Contains at least one number or symbol
                    </span>
                  </div>
                </div>

                <Input
                  label="CONFIRM NEW PASSWORD"
                  type="password"
                  placeholder="••••••••••••"
                  value={confirmNewPassword}
                  onChange={(e) => {
                    setConfirmNewPassword(e.target.value);
                    if (fieldErrors.confirmNewPassword) {
                      setFieldErrors((prev) => ({ ...prev, confirmNewPassword: '' }));
                    }
                  }}
                  error={fieldErrors.confirmNewPassword}
                  leftElement={<Lock className="w-4 h-4" />}
                  autoComplete="new-password"
                  disabled={isSubmitting}
                />

                {confirmNewPassword.length > 0 && (
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

                <Button
                  type="submit"
                  className="w-full"
                  isLoading={isSubmitting}
                  disabled={isSubmitting}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  {isSubmitting ? 'UPDATING PASSWORD...' : 'SET NEW PASSWORD'}
                </Button>
              </form>
            </>
          )}
        </Card>
      </Container>
    </div>
  );
};

export default ResetPasswordPage;

