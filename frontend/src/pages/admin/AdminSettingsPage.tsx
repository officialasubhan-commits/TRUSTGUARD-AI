import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  KeyRound,
  Lock,
  ShieldCheck,
  User,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { adminService } from '../../services/adminService';

export const AdminSettingsPage: React.FC = () => {
  const { adminUser: admin, refreshAdmin } = useAdminAuth();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);

    if (newPassword.length < 8) {
      setFeedback({
        type: 'error',
        message: 'New password must be at least 8 characters long.',
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      setFeedback({
        type: 'error',
        message: 'New password and confirmation password do not match.',
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await adminService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setFeedback({
        type: 'success',
        message: 'Administrator password successfully updated with Argon2id hashing.',
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      await refreshAdmin();
    } catch (err: any) {
      console.error('Password change failed:', err);
      setFeedback({
        type: 'error',
        message:
          err.response?.data?.detail || 'Failed to update administrator password. Verify current password.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#222222] pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono uppercase">
              Administrator Settings & Security
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium tracking-wide border bg-[#111111] text-[#a0a0a0] border-[#333333]">
              ARGON2ID
            </span>
          </div>
          <p className="text-sm text-[#737373] mt-1 font-mono">
            Manage your administrative credentials, active security token parameters and session profiles
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Profile and Session Overview */}
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
                <span className="text-white">RBAC / Non-User Isolated</span>
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

            {feedback && (
              <div
                className={`p-4 rounded border text-xs font-mono mb-6 ${
                  feedback.type === 'success'
                    ? 'bg-[#112411] border-[#254d25] text-[#86efac]'
                    : 'bg-[#261111] border-[#4d2525] text-[#fca5a5]'
                }`}
              >
                <div className="flex items-center gap-2">
                  {feedback.type === 'success' ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                  )}
                  <span>{feedback.message}</span>
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
                  disabled={isSubmitting}
                  className="bg-white hover:bg-[#e5e5e5] text-black font-mono text-xs font-semibold px-5 py-2.5"
                >
                  {isSubmitting ? 'Updating Password...' : 'Update Password (Argon2id)'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
};
