import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  KeyRound,
  Lock,
  Save,
  Settings,
  ShieldCheck,
  Sliders,
  User,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { adminService } from '../../services/adminService';
import { SystemSettingsConfig, SystemSettingsUpdate } from '../../types/admin';

export const AdminSettingsPage: React.FC = () => {
  const { adminUser: admin, refreshAdmin } = useAdminAuth();

  const [activeTab, setActiveTab] = useState<'branding' | 'security'>('branding');

  // Platform Branding & Announcement State
  const [settingsData, setSettingsData] = useState<SystemSettingsConfig | null>(null);
  const [isLoadingSettings, setIsLoadingSettings] = useState(true);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [settingsFeedback, setSettingsFeedback] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmittingPassword, setIsSubmittingPassword] = useState(false);
  const [passwordFeedback, setPasswordFeedback] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await adminService.getSystemSettings();
        setSettingsData(data);
      } catch (err) {
        console.error('Failed fetching platform settings:', err);
      } finally {
        setIsLoadingSettings(false);
      }
    };
    fetchSettings();
  }, []);

  const handleSavePlatformSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settingsData) return;
    setIsSavingSettings(true);
    setSettingsFeedback(null);
    try {
      const updatePayload: SystemSettingsUpdate = {
        site_name: settingsData.site_name,
        site_tagline: settingsData.site_tagline,
        site_description: settingsData.site_description,
        logo_url: settingsData.logo_url || undefined,
        favicon_url: settingsData.favicon_url || undefined,
        announcement_enabled: settingsData.announcement_enabled,
        announcement_message: settingsData.announcement_message || undefined,
        announcement_type: settingsData.announcement_type,
        announcement_link: settingsData.announcement_link || undefined,
        allow_registration: settingsData.allow_registration,
        allow_guest_scans: settingsData.allow_guest_scans,
        allow_community_reports: settingsData.allow_community_reports,
      };
      const updated = await adminService.updateSystemSettings(updatePayload);
      setSettingsData(updated);
      setSettingsFeedback({
        type: 'success',
        message: 'Platform branding and announcement configuration updated.',
      });
    } catch (err: any) {
      setSettingsFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed updating system settings.',
      });
    } finally {
      setIsSavingSettings(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordFeedback(null);

    if (newPassword.length < 8) {
      setPasswordFeedback({
        type: 'error',
        message: 'New password must be at least 8 characters long.',
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordFeedback({
        type: 'error',
        message: 'New password and confirmation password do not match.',
      });
      return;
    }

    setIsSubmittingPassword(true);
    try {
      await adminService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordFeedback({
        type: 'success',
        message: 'Administrator password successfully updated with Argon2id hashing.',
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      await refreshAdmin();
    } catch (err: any) {
      console.error('Password change failed:', err);
      setPasswordFeedback({
        type: 'error',
        message:
          err.response?.data?.detail || 'Failed to update administrator password. Verify current password.',
      });
    } finally {
      setIsSubmittingPassword(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#222222] pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white font-mono uppercase">
              System Settings & Security
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium tracking-wide border bg-[#111111] text-[#a0a0a0] border-[#333333]">
              ARGON2ID • RBAC
            </span>
          </div>
          <p className="text-xs text-[#737373] mt-1 font-mono">
            CONFIGURE PLATFORM BRANDING, ANNOUNCEMENTS, FEATURE TOGGLES AND ADMINISTRATOR CREDENTIALS
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-[#222222]">
        <button
          onClick={() => setActiveTab('branding')}
          className={`px-4 py-2 text-xs font-mono tracking-wider transition-colors border-b-2 -mb-px flex items-center space-x-2 ${
            activeTab === 'branding'
              ? 'border-white text-white font-semibold'
              : 'border-transparent text-[#777777] hover:text-[#CCCCCC]'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>BRANDING & ANNOUNCEMENTS</span>
        </button>
        <button
          onClick={() => setActiveTab('security')}
          className={`px-4 py-2 text-xs font-mono tracking-wider transition-colors border-b-2 -mb-px flex items-center space-x-2 ${
            activeTab === 'security'
              ? 'border-white text-white font-semibold'
              : 'border-transparent text-[#777777] hover:text-[#CCCCCC]'
          }`}
        >
          <KeyRound className="w-3.5 h-3.5" />
          <span>ADMIN CREDENTIALS & SECURITY</span>
        </button>
      </div>

      {activeTab === 'branding' ? (
        isLoadingSettings ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <PixelSpinner size={32} />
            <p className="text-xs font-mono text-[#888888]">Loading settings...</p>
          </div>
        ) : (
          <div className="space-y-6 max-w-3xl">
            {settingsFeedback && (
              <div
                className={`p-3 rounded text-xs font-mono border ${
                  settingsFeedback.type === 'success'
                    ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
                    : 'bg-rose-950/40 text-rose-300 border-rose-800/60'
                }`}
              >
                {settingsFeedback.message}
              </div>
            )}

            <form onSubmit={handleSavePlatformSettings} className="space-y-6">
              {/* Branding Section */}
              <Card pixelFrame className="p-6 bg-[#0E0E0E] border-[#222222] space-y-4">
                <h3 className="text-sm font-mono font-semibold uppercase text-white flex items-center space-x-2">
                  <Settings className="w-4 h-4 text-cyan-400" />
                  <span>Platform Branding</span>
                </h3>

                <div className="space-y-3 font-mono text-xs">
                  <div>
                    <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                      Site Name
                    </label>
                    <input
                      type="text"
                      value={settingsData?.site_name || ''}
                      onChange={(e) =>
                        setSettingsData(
                          settingsData ? { ...settingsData, site_name: e.target.value } : null
                        )
                      }
                      className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                      Site Tagline
                    </label>
                    <input
                      type="text"
                      value={settingsData?.site_tagline || ''}
                      onChange={(e) =>
                        setSettingsData(
                          settingsData ? { ...settingsData, site_tagline: e.target.value } : null
                        )
                      }
                      className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                    />
                  </div>

                  <div>
                    <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                      Platform Meta Description
                    </label>
                    <textarea
                      value={settingsData?.site_description || ''}
                      onChange={(e) =>
                        setSettingsData(
                          settingsData ? { ...settingsData, site_description: e.target.value } : null
                        )
                      }
                      rows={2}
                      className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                    />
                  </div>
                </div>
              </Card>

              {/* Announcement Banner Section */}
              <Card pixelFrame className="p-6 bg-[#0E0E0E] border-[#222222] space-y-4">
                <h3 className="text-sm font-mono font-semibold uppercase text-white flex items-center space-x-2">
                  <Bell className="w-4 h-4 text-amber-400" />
                  <span>Public Announcement Banner</span>
                </h3>

                <div className="space-y-3 font-mono text-xs">
                  <label className="flex items-center space-x-2 cursor-pointer pb-2 border-b border-[#1C1C1C]">
                    <input
                      type="checkbox"
                      checked={settingsData?.announcement_enabled ?? false}
                      onChange={(e) =>
                        setSettingsData(
                          settingsData
                            ? { ...settingsData, announcement_enabled: e.target.checked }
                            : null
                        )
                      }
                      className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0 w-4 h-4"
                    />
                    <span className="text-white font-semibold">Enable Global Announcement Banner</span>
                  </label>

                  <div>
                    <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                      Announcement Message
                    </label>
                    <input
                      type="text"
                      value={settingsData?.announcement_message || ''}
                      onChange={(e) =>
                        setSettingsData(
                          settingsData
                            ? { ...settingsData, announcement_message: e.target.value }
                            : null
                        )
                      }
                      placeholder="e.g. TrustGuard AI 2.0 Released: Real-time ML inspection is live."
                      className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                        Banner Type
                      </label>
                      <select
                        value={settingsData?.announcement_type || 'info'}
                        onChange={(e) =>
                          setSettingsData(
                            settingsData
                              ? {
                                  ...settingsData,
                                  announcement_type: e.target.value as 'info' | 'warning' | 'critical',
                                }
                              : null
                          )
                        }
                        className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                      >
                        <option value="info">Information (Blue/Cyan)</option>
                        <option value="warning">Warning (Amber)</option>
                        <option value="critical">Critical Alert (Red)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                        Action Link (Optional)
                      </label>
                      <input
                        type="text"
                        value={settingsData?.announcement_link || ''}
                        onChange={(e) =>
                          setSettingsData(
                            settingsData
                              ? { ...settingsData, announcement_link: e.target.value }
                              : null
                          )
                        }
                        placeholder="/contributors or https://..."
                        className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                      />
                    </div>
                  </div>
                </div>
              </Card>

              {/* Feature Toggles */}
              <Card pixelFrame className="p-6 bg-[#0E0E0E] border-[#222222] space-y-3 font-mono text-xs">
                <h3 className="text-sm font-semibold uppercase text-white pb-2 border-b border-[#1C1C1C]">
                  Platform Feature Toggles
                </h3>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settingsData?.allow_registration ?? true}
                    onChange={(e) =>
                      setSettingsData(
                        settingsData
                          ? { ...settingsData, allow_registration: e.target.checked }
                          : null
                      )
                    }
                    className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0 w-4 h-4"
                  />
                  <span className="text-white">Allow Public User Registrations</span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settingsData?.allow_guest_scans ?? true}
                    onChange={(e) =>
                      setSettingsData(
                        settingsData
                          ? { ...settingsData, allow_guest_scans: e.target.checked }
                          : null
                      )
                    }
                    className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0 w-4 h-4"
                  />
                  <span className="text-white">Allow Guest / Unauthenticated URL Scans</span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settingsData?.allow_community_reports ?? true}
                    onChange={(e) =>
                      setSettingsData(
                        settingsData
                          ? { ...settingsData, allow_community_reports: e.target.checked }
                          : null
                      )
                    }
                    className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0 w-4 h-4"
                  />
                  <span className="text-white">Allow Community Threat Submissions</span>
                </label>
              </Card>

              <div className="flex justify-end pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSavingSettings}
                  leftIcon={<Save className="w-3.5 h-3.5" />}
                >
                  SAVE PLATFORM SETTINGS
                </Button>
              </div>
            </form>
          </div>
        )
      ) : (
        /* Security Tab */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Profile Overview */}
          <div className="lg:col-span-5 space-y-6">
            <Card className="bg-[#111111] border-[#222222] p-6 space-y-5">
              <div className="flex items-center gap-3 pb-4 border-b border-[#222222]">
                <div className="w-12 h-12 rounded bg-[#1c1c1c] border border-[#2e2e2e] flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-mono text-base font-bold text-white">
                    {admin?.full_name || admin?.username || 'Administrator'}
                  </h3>
                  <span className="inline-block mt-0.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[#1f1f1f] text-[#4ade80] border border-[#2e4d2e]">
                    {admin?.role?.toUpperCase() || 'SUPER_ADMIN'}
                  </span>
                </div>
              </div>

              <div className="space-y-3 text-xs font-mono">
                <div className="flex items-center justify-between py-1.5 border-b border-[#1c1c1c]">
                  <span className="text-[#737373]">Admin ID</span>
                  <span className="text-white select-all text-[11px]">{admin?.id}</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-[#1c1c1c]">
                  <span className="text-[#737373]">Username</span>
                  <span className="text-white">{admin?.username}</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-[#1c1c1c]">
                  <span className="text-[#737373]">Contact Email</span>
                  <span className="text-white">{admin?.email || 'admin@trustguard.ai'}</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-[#1c1c1c]">
                  <span className="text-[#737373]">Account Status</span>
                  <span className="text-[#4ade80] flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Active / Authorized
                  </span>
                </div>
              </div>
            </Card>

            <Card className="bg-[#111111] border-[#222222] p-6 space-y-4">
              <div className="flex items-center gap-2 text-xs font-mono font-semibold text-[#a0a0a0] uppercase tracking-wider">
                <ShieldCheck className="w-4 h-4 text-[#4ade80]" />
                <span>Cryptographic Session Guarantee</span>
              </div>

              <div className="space-y-2.5 text-xs font-mono text-[#737373]">
                <div className="flex items-center justify-between">
                  <span>Password Hashing</span>
                  <span className="text-white">Argon2id (RFC 9106)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Session Claim</span>
                  <span className="text-white">type: "admin_session"</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Session Duration</span>
                  <span className="text-white">8 Hours</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Isolation Boundary</span>
                  <span className="text-white">RBAC / Isolated from User Space</span>
                </div>
              </div>
            </Card>
          </div>

          {/* Change Password Form */}
          <div className="lg:col-span-7">
            <Card className="bg-[#111111] border-[#222222] p-6">
              <div className="flex items-center gap-2 pb-4 border-b border-[#222222] mb-6">
                <KeyRound className="w-4 h-4 text-white" />
                <h3 className="font-mono text-sm font-semibold text-white uppercase tracking-wider">
                  Change Administrator Password
                </h3>
              </div>

              {passwordFeedback && (
                <div
                  className={`p-4 rounded border text-xs font-mono mb-6 ${
                    passwordFeedback.type === 'success'
                      ? 'bg-[#112411] border-[#254d25] text-[#86efac]'
                      : 'bg-[#261111] border-[#4d2525] text-[#fca5a5]'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {passwordFeedback.type === 'success' ? (
                      <CheckCircle2 className="w-4 h-4 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 shrink-0" />
                    )}
                    <span>{passwordFeedback.message}</span>
                  </div>
                </div>
              )}

              <form onSubmit={handleChangePassword} className="space-y-5">
                <div className="space-y-2">
                  <label className="text-xs font-mono font-semibold text-white uppercase tracking-wider block">
                    Current Administrator Password *
                  </label>
                  <div className="relative">
                    <Lock className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#737373]" />
                    <input
                      type="password"
                      required
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="Enter current password..."
                      className="w-full pl-9 pr-3 py-2 bg-[#0c0c0c] border border-[#262626] rounded text-xs font-mono text-white placeholder-[#525252] focus:outline-none focus:border-[#404040]"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-mono font-semibold text-white uppercase tracking-wider block">
                    New Administrator Password *
                  </label>
                  <div className="relative">
                    <KeyRound className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#737373]" />
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Minimum 8 characters with numbers & symbols..."
                      className="w-full pl-9 pr-3 py-2 bg-[#0c0c0c] border border-[#262626] rounded text-xs font-mono text-white placeholder-[#525252] focus:outline-none focus:border-[#404040]"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-mono font-semibold text-white uppercase tracking-wider block">
                    Confirm New Password *
                  </label>
                  <div className="relative">
                    <KeyRound className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#737373]" />
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-type new password..."
                      className="w-full pl-9 pr-3 py-2 bg-[#0c0c0c] border border-[#262626] rounded text-xs font-mono text-white placeholder-[#525252] focus:outline-none focus:border-[#404040]"
                    />
                  </div>
                </div>

                <div className="pt-4 border-t border-[#222222] flex justify-end">
                  <Button
                    type="submit"
                    disabled={isSubmittingPassword}
                    className="bg-white hover:bg-[#e5e5e5] text-black font-mono text-xs font-semibold px-5 py-2.5"
                  >
                    {isSubmittingPassword ? 'Updating Password...' : 'Update Password (Argon2id)'}
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
