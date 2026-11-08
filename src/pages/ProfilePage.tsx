import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  User as UserIcon,
  Mail,
  Shield,
  Activity,
  Calendar,
  LogOut,
  Save,
  CheckCircle2,
  AlertTriangle,
  History,
  Lock,
  Bell,
  Info,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Container } from '../components/common/Container';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { formatApiError } from '../services/api';
import authService from '../services/authService';

export const ProfilePage: React.FC = () => {
  const { user, profile, updateProfile, refreshProfile, logout } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState(user?.full_name || profile?.full_name || '');
  const [isUpdating, setIsUpdating] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  // Email Notification Preferences State
  const [threatDigestEnabled, setThreatDigestEnabled] = useState<boolean>(
    profile?.threat_digest_enabled ?? false
  );
  const [providerConfigured, setProviderConfigured] = useState<boolean>(false);
  const [isLoadingNotifications, setIsLoadingNotifications] = useState<boolean>(false);
  const [isSavingNotifications, setIsSavingNotifications] = useState<boolean>(false);
  const [notifSuccess, setNotifSuccess] = useState<string | null>(null);
  const [notifError, setNotifError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.full_name) setFullName(user.full_name);
    else if (profile?.full_name) setFullName(profile.full_name);
  }, [user?.full_name, profile?.full_name]);

  useEffect(() => {
    let isMounted = true;
    const fetchNotificationPreferences = async () => {
      setIsLoadingNotifications(true);
      try {
        const prefs = await authService.getNotificationPreferences();
        if (isMounted) {
          setThreatDigestEnabled(prefs.threat_digest_enabled);
          setProviderConfigured(prefs.provider_configured);
        }
      } catch (err) {
        // Fall back to profile cache if backend notification service is unavailable
        if (isMounted && profile?.threat_digest_enabled !== undefined) {
          setThreatDigestEnabled(profile.threat_digest_enabled);
        }
      } finally {
        if (isMounted) setIsLoadingNotifications(false);
      }
    };

    fetchNotificationPreferences();
    return () => {
      isMounted = false;
    };
  }, [profile?.threat_digest_enabled]);

  const handleSaveNotifications = async () => {
    setNotifSuccess(null);
    setNotifError(null);
    setIsSavingNotifications(true);

    try {
      const updated = await authService.updateNotificationPreferences(threatDigestEnabled);
      setThreatDigestEnabled(updated.threat_digest_enabled);
      setProviderConfigured(updated.provider_configured);
      await refreshProfile();
      setNotifSuccess('Email notification preferences saved successfully.');
      setTimeout(() => setNotifSuccess(null), 4000);
    } catch (err: any) {
      const formatted = formatApiError(err);
      setNotifError(
        formatted.message || 'Failed to update email notification preferences. Please try again.'
      );
    } finally {
      setIsSavingNotifications(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);

    const trimmed = fullName.trim();
    if (trimmed.length < 2) {
      setErrorMessage('Full name must contain at least 2 characters.');
      return;
    }

    setIsUpdating(true);
    try {
      await updateProfile({ full_name: trimmed });
      setSuccessMessage('Profile identity details successfully updated.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      const formatted = formatApiError(err);
      setErrorMessage(formatted.message || 'Unable to update profile. Please verify server connectivity.');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/', { replace: true });
  };

  const createdDate = profile?.created_at
    ? new Date(profile.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'Authenticated Active Session';

  return (
    <div className="flex-1 py-12 md:py-20 px-4">
      <Container size="md">
        <div className="space-y-8">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[#222222]">
            <div className="space-y-1">
              <h1 className="text-2xl sm:text-3xl font-light tracking-tight text-[#F5F5F5]">
                Security Analyst Profile
              </h1>
              <p className="text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                AUTHENTICATED IDENTITY & PLATFORM CLEARANCE
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Link to="/history">
                <Button variant="secondary" size="sm" leftIcon={<History className="w-3.5 h-3.5" />}>
                  SCAN HISTORY
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowLogoutConfirm(true)}
                leftIcon={<LogOut className="w-3.5 h-3.5 text-[#F87171]" />}
              >
                SIGN OUT
              </Button>
            </div>
          </div>

          {/* Logout Confirmation Banner */}
          {showLogoutConfirm && (
            <div className="p-4 bg-[#141414] border border-[#F87171]/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs">
              <div className="flex items-center space-x-2.5 text-[#FCA5A5]">
                <AlertTriangle className="w-4 h-4 shrink-0 text-[#F87171]" />
                <span>Terminate active session on this device?</span>
              </div>
              <div className="flex items-center space-x-2">
                <Button size="sm" variant="secondary" onClick={() => setShowLogoutConfirm(false)}>
                  CANCEL
                </Button>
                <Button size="sm" variant="primary" onClick={handleLogout}>
                  CONFIRM SIGN OUT
                </Button>
              </div>
            </div>
          )}

          {/* Success Banner */}
          {successMessage && (
            <div className="p-3 bg-[#0F1710] border border-[#4ADE80]/30 flex items-center space-x-2.5 text-xs text-[#4ADE80] font-mono">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Error Banner */}
          {errorMessage && (
            <div className="p-3 bg-[#1C1212] border border-[#F87171]/40 flex items-center space-x-2.5 text-xs text-[#FCA5A5] font-mono">
              <AlertTriangle className="w-4 h-4 shrink-0 text-[#F87171]" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Profile Overview Card */}
          <Card pixelFrame className="p-6 md:p-8 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#222222]">
              <div className="flex items-center space-x-4">
                <div className="w-14 h-14 bg-[#101010] border border-[#292929] flex items-center justify-center text-[#F5F5F5]">
                  <UserIcon className="w-7 h-7 text-[#A1A1A1]" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <h2 className="text-lg font-mono font-bold text-[#F5F5F5]">
                      {fullName || user?.email?.split('@')[0] || 'Authenticated Analyst'}
                    </h2>
                    <Badge variant="safe" size="xs">
                      {profile?.is_active !== false ? 'ACTIVE' : 'SUSPENDED'}
                    </Badge>
                  </div>
                  <p className="text-xs font-mono text-[#666666] flex items-center space-x-2">
                    <span>ROLE: {user?.role?.toUpperCase() || 'USER'}</span>
                    <span>•</span>
                    <span className="truncate max-w-[200px]" title={user?.id}>
                      UID: {user?.id}
                    </span>
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="p-3 bg-[#101010] border border-[#1F1F1F] text-center min-w-[90px]">
                  <span className="block text-[10px] font-mono text-[#666666] uppercase">
                    Scans Run
                  </span>
                  <span className="text-lg font-mono font-bold text-[#F5F5F5]">
                    {profile?.scan_count ?? 0}
                  </span>
                </div>
              </div>
            </div>

            {/* Editable Information */}
            <form onSubmit={handleUpdate} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="FULL NAME (EDITABLE)"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Your Full Name"
                  leftElement={<UserIcon className="w-4 h-4" />}
                  disabled={isUpdating}
                />

                <Input
                  label="EMAIL ADDRESS (IDENTITY)"
                  type="email"
                  value={user?.email || profile?.email || ''}
                  disabled
                  leftElement={<Mail className="w-4 h-4" />}
                  hint="Email is bound to your authentication provider."
                />
              </div>

              <div className="flex justify-end pt-2">
                <Button
                  type="submit"
                  size="sm"
                  isLoading={isUpdating}
                  disabled={isUpdating}
                  rightIcon={<Save className="w-3.5 h-3.5" />}
                >
                  {isUpdating ? 'SAVING...' : 'SAVE CHANGES'}
                </Button>
              </div>
            </form>
          </Card>

          {/* Email Notification Preferences Card */}
          <Card pixelFrame className="p-6 md:p-8 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#222222]">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <Bell className="w-4 h-4 text-[#A1A1A1]" />
                  <h3 className="text-sm font-mono font-semibold uppercase text-[#F5F5F5]">
                    EMAIL NOTIFICATION PREFERENCES
                  </h3>
                </div>
                <p className="text-xs font-mono text-[#666666]">
                  AUTOMATED THREAT INTEL DIGESTS & SECURITY NOTIFICATIONS
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <Badge
                  variant={threatDigestEnabled ? 'safe' : 'subtle'}
                  size="xs"
                >
                  {threatDigestEnabled ? 'DIGEST ACTIVE' : 'DIGEST DISABLED'}
                </Badge>
              </div>
            </div>

            <div className="space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-[#101010] border border-[#1F1F1F]">
                <div className="space-y-1 max-w-xl">
                  <span className="text-xs font-mono font-medium text-[#F5F5F5] block">
                    Periodic Threat Digest & Security Summaries
                  </span>
                  <p className="text-[11px] font-mono text-[#A1A1A1] leading-relaxed">
                    Receive periodic email summaries about relevant security threats, verified community reports, and important TrustGuard AI security updates.
                  </p>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <span className="text-[11px] font-mono text-[#666666] uppercase">
                    {threatDigestEnabled ? 'ENABLED' : 'DISABLED'}
                  </span>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={threatDigestEnabled}
                    disabled={isLoadingNotifications || isSavingNotifications}
                    onClick={() => setThreatDigestEnabled(!threatDigestEnabled)}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-1 focus:ring-[#F5F5F5] ${
                      threatDigestEnabled ? 'bg-[#F5F5F5]' : 'bg-[#262626]'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-[#0A0A0A] shadow transform ring-0 transition duration-200 ease-in-out ${
                        threatDigestEnabled ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Provider Status Callout */}
              {!providerConfigured && (
                <div className="p-3 bg-[#141414] border border-[#222222] flex items-start space-x-2.5 text-[11px] text-[#A1A1A1] font-mono">
                  <Info className="w-4 h-4 shrink-0 text-[#666666] mt-0.5" />
                  <div className="space-y-0.5">
                    <span className="text-[#888888] font-medium block">
                      OUTBOUND DISPATCH STATUS: STANDBY
                    </span>
                    <p className="text-[#666666]">
                      Outbound email delivery is currently in maintenance or unconfigured mode. Your preference is securely persisted in your telemetry profile and will apply automatically once outbound dispatch is active.
                    </p>
                  </div>
                </div>
              )}

              {/* Feedback Banners */}
              {notifSuccess && (
                <div className="p-3 bg-[#0F1710] border border-[#4ADE80]/30 flex items-center space-x-2.5 text-xs text-[#4ADE80] font-mono">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{notifSuccess}</span>
                </div>
              )}

              {notifError && (
                <div className="p-3 bg-[#1C1212] border border-[#F87171]/40 flex items-center space-x-2.5 text-xs text-[#FCA5A5] font-mono">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-[#F87171]" />
                  <span>{notifError}</span>
                </div>
              )}

              <div className="flex justify-end pt-2">
                <Button
                  type="button"
                  size="sm"
                  onClick={handleSaveNotifications}
                  isLoading={isSavingNotifications}
                  disabled={isSavingNotifications || isLoadingNotifications}
                  rightIcon={<Save className="w-3.5 h-3.5" />}
                >
                  {isSavingNotifications ? 'SAVING...' : 'SAVE PREFERENCES'}
                </Button>
              </div>
            </div>
          </Card>

          {/* Telemetry & Identity Meta Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card variant="standard" className="p-4 space-y-2">
              <div className="flex items-center space-x-2 text-[#A1A1A1] text-xs font-mono uppercase">
                <Calendar className="w-3.5 h-3.5" />
                <span>Account Created</span>
              </div>
              <p className="text-xs font-mono text-[#F5F5F5]">{createdDate}</p>
            </Card>

            <Card variant="standard" className="p-4 space-y-2">
              <div className="flex items-center space-x-2 text-[#A1A1A1] text-xs font-mono uppercase">
                <Shield className="w-3.5 h-3.5" />
                <span>Access Clearance</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono text-[#F5F5F5]">
                  {user?.role === 'admin' ? 'Level 4 (Administrator)' : 'Level 2 (Security Analyst)'}
                </span>
              </div>
            </Card>

            <Card variant="standard" className="p-4 space-y-2">
              <div className="flex items-center space-x-2 text-[#A1A1A1] text-xs font-mono uppercase">
                <Activity className="w-3.5 h-3.5" />
                <span>Session Integrity</span>
              </div>
              <p className="text-xs font-mono text-[#4ADE80]">
                JWT Active • Bearer Verified
              </p>
            </Card>
          </div>

          {/* Capabilities Comparison: Guest vs Authenticated User */}
          <Card variant="standard" className="p-6 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#222222]">
              <div className="flex items-center space-x-2">
                <Lock className="w-4 h-4 text-[#A1A1A1]" />
                <h3 className="text-xs font-mono font-semibold uppercase text-[#F5F5F5]">
                  AUTHENTICATED ACCESS CAPABILITIES
                </h3>
              </div>
              <span className="text-[11px] font-mono text-[#4ADE80]">ENABLED FOR YOUR ACCOUNT</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono text-[#A1A1A1]">
              <div className="p-3 bg-[#101010] border border-[#1F1F1F] space-y-1">
                <span className="text-[#F5F5F5] font-semibold block">PERSISTENT SCAN HISTORY</span>
                <p className="text-[11px] text-[#666666] leading-relaxed">
                  Every audited domain is cryptographically cataloged in your private database telemetry.
                </p>
              </div>

              <div className="p-3 bg-[#101010] border border-[#1F1F1F] space-y-1">
                <span className="text-[#F5F5F5] font-semibold block">COMMUNITY THREAT REPORTING</span>
                <p className="text-[11px] text-[#666666] leading-relaxed">
                  Submit threat investigations, upvote security advisories, and contribute threat feeds.
                </p>
              </div>

              <div className="p-3 bg-[#101010] border border-[#1F1F1F] space-y-1">
                <span className="text-[#F5F5F5] font-semibold block">ELEVATED RATE LIMITS</span>
                <p className="text-[11px] text-[#666666] leading-relaxed">
                  Authenticated users receive prioritized queue allocations for deep multi-engine heuristics.
                </p>
              </div>

              <div className="p-3 bg-[#101010] border border-[#1F1F1F] space-y-1">
                <span className="text-[#F5F5F5] font-semibold block">AUDIT DOSSIER EXPORT</span>
                <p className="text-[11px] text-[#666666] leading-relaxed">
                  Export machine-readable JSON logs and print-ready executive security dossiers.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </Container>
    </div>
  );
};

export default ProfilePage;
