import React, { useEffect, useState } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Eye,
  Info,
  RefreshCw,
  Save,
  Wrench,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import { MaintenanceConfig } from '../../types/admin';

export const AdminMaintenancePage: React.FC = () => {
  const [config, setConfig] = useState<MaintenanceConfig | null>(null);
  const [isEnabled, setIsEnabled] = useState(false);
  const [message, setMessage] = useState('');
  const [estimatedTime, setEstimatedTime] = useState('');
  const [internalReason, setInternalReason] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchConfig = async () => {
    try {
      const data = await adminService.getMaintenanceConfig();
      setConfig(data);
      setIsEnabled(data.maintenance_enabled);
      setMessage(data.maintenance_message);
      setEstimatedTime(data.estimated_restore_time || '');
      setInternalReason(data.internal_reason || '');
    } catch (err) {
      console.error('Failed to load maintenance config:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!internalReason.trim()) {
      setFeedback({
        type: 'error',
        message: 'An internal reason is mandatory for administrative audit logging.',
      });
      return;
    }

    setIsSaving(true);
    setFeedback(null);

    try {
      const updated = await adminService.updateMaintenanceConfig({
        maintenance_enabled: isEnabled,
        maintenance_message: message.trim(),
        estimated_restore_time: estimatedTime.trim() || undefined,
        internal_reason: internalReason.trim(),
      });
      setConfig(updated);
      setFeedback({
        type: 'success',
        message: isEnabled
          ? 'Maintenance mode is now ACTIVE. Public scanner traffic is blocked with HTTP 503.'
          : 'Maintenance mode has been DEACTIVATED. Public access is fully restored.',
      });
    } catch (err: any) {
      console.error('Failed to update maintenance mode:', err);
      setFeedback({
        type: 'error',
        message: err.response?.data?.detail || 'Failed to update maintenance mode settings.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#222222] pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono uppercase">
              Website Maintenance Mode
            </h1>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium tracking-wide border ${
                isEnabled
                  ? 'bg-[#2a1313] text-[#f87171] border-[#522525]'
                  : 'bg-[#132313] text-[#4ade80] border-[#254d25]'
              }`}
            >
              {isEnabled ? 'SYSTEM IN MAINTENANCE' : 'SYSTEM ONLINE'}
            </span>
          </div>
          <p className="text-sm text-[#737373] mt-1 font-mono">
            Control platform availability, public 503 responses and planned downtime announcements
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchConfig}
            className="border-[#333333] hover:bg-[#1c1c1c] text-[#e5e5e5] font-mono text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-2" />
            Reload Settings
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="py-24 flex flex-col items-center justify-center space-y-4">
          <PixelSpinner />
          <p className="text-xs font-mono text-[#737373] tracking-widest uppercase">
            Loading System Configuration...
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Main Configuration Form */}
          <div className="lg:col-span-7 space-y-6">
            {feedback && (
              <div
                className={`p-4 rounded border text-xs font-mono ${
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

            {/* Status Notice Banner */}
            {isEnabled ? (
              <Card className="bg-[#241010] border-[#4a1c1c] p-5">
                <div className="flex items-start gap-3">
                  <AlertOctagon className="w-5 h-5 text-[#f87171] shrink-0 mt-0.5" />
                  <div className="space-y-1 text-xs font-mono">
                    <div className="font-semibold text-white uppercase tracking-wider">
                      Maintenance Mode is currently active
                    </div>
                    <p className="text-[#fca5a5]">
                      All public scanner routes, authentication pages, and community reporting endpoints are
                      returning HTTP 503 Service Unavailable. Admin panel access remains available.
                    </p>
                  </div>
                </div>
              </Card>
            ) : (
              <Card className="bg-[#101b10] border-[#1d3d1d] p-5">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[#4ade80] shrink-0 mt-0.5" />
                  <div className="space-y-1 text-xs font-mono">
                    <div className="font-semibold text-white uppercase tracking-wider">
                      Public System is Online
                    </div>
                    <p className="text-[#86efac]">
                      The platform is operating normally. All public users have uninterrupted access to the scanner,
                      API, and security reports.{config?.updated_at && ` (Last evaluated: ${new Date(config.updated_at).toLocaleString()})`}
                    </p>
                  </div>
                </div>
              </Card>
            )}

            <Card className="bg-[#111111] border-[#222222] p-6">
              <form onSubmit={handleSave} className="space-y-6">
                {/* Mode Toggle */}
                <div className="flex items-center justify-between pb-6 border-b border-[#222222]">
                  <div>
                    <label className="text-sm font-mono font-semibold text-white uppercase tracking-wider block">
                      Enable Maintenance Mode
                    </label>
                    <p className="text-xs font-mono text-[#737373] mt-1">
                      Toggle to immediately activate or deactivate global public lockdown
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setIsEnabled(!isEnabled)}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      isEnabled ? 'bg-[#ef4444]' : 'bg-[#262626]'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                        isEnabled ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>

                {/* Public Message */}
                <div className="space-y-2">
                  <label className="text-xs font-mono font-semibold text-white uppercase tracking-wider block">
                    Public Announcement Message
                  </label>
                  <p className="text-[11px] font-mono text-[#737373]">
                    Displayed on the visitor-facing maintenance screen and returned in JSON 503 errors
                  </p>
                  <textarea
                    rows={4}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    required
                    placeholder="Enter visitor announcement message..."
                    className="w-full px-3 py-2 bg-[#0c0c0c] border border-[#262626] rounded text-xs font-mono text-white placeholder-[#525252] focus:outline-none focus:border-[#404040]"
                  />
                </div>

                {/* Estimated Restoration Time */}
                <div className="space-y-2">
                  <label className="text-xs font-mono font-semibold text-white uppercase tracking-wider block">
                    Estimated Restoration Time (Optional)
                  </label>
                  <p className="text-[11px] font-mono text-[#737373]">
                    Displayed on the visitor maintenance screen (e.g. "Approximately 30 minutes" or "14:00 UTC")
                  </p>
                  <div className="relative">
                    <Clock className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#737373]" />
                    <input
                      type="text"
                      value={estimatedTime}
                      onChange={(e) => setEstimatedTime(e.target.value)}
                      placeholder="e.g. Approximately 45 minutes / 2026-11-09 02:00 UTC"
                      className="w-full pl-9 pr-3 py-2 bg-[#0c0c0c] border border-[#262626] rounded text-xs font-mono text-white placeholder-[#525252] focus:outline-none focus:border-[#404040]"
                    />
                  </div>
                </div>

                {/* Mandatory Internal Reason */}
                <div className="space-y-2">
                  <label className="text-xs font-mono font-semibold text-white uppercase tracking-wider block">
                    Mandatory Internal Reason *
                  </label>
                  <p className="text-[11px] font-mono text-[#737373]">
                    Recorded in the immutable administrative audit log for security compliance
                  </p>
                  <input
                    type="text"
                    value={internalReason}
                    onChange={(e) => setInternalReason(e.target.value)}
                    required
                    placeholder="e.g. Scheduled database migration / security engine update"
                    className="w-full px-3 py-2 bg-[#0c0c0c] border border-[#262626] rounded text-xs font-mono text-white placeholder-[#525252] focus:outline-none focus:border-[#404040]"
                  />
                </div>

                {/* Form Actions */}
                <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#222222]">
                  <Button
                    type="submit"
                    disabled={isSaving}
                    className="bg-white hover:bg-[#e5e5e5] text-black font-mono text-xs font-semibold px-5 py-2.5"
                  >
                    <Save className={`w-3.5 h-3.5 mr-2 ${isSaving ? 'animate-spin' : ''}`} />
                    {isSaving ? 'Applying Settings...' : 'Save & Apply Configuration'}
                  </Button>
                </div>
              </form>
            </Card>
          </div>

          {/* Visitor Screen Live Preview */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center gap-2 text-xs font-mono text-[#a0a0a0] uppercase tracking-wider">
              <Eye className="w-4 h-4 text-white" />
              <span>Visitor Screen Live Preview</span>
            </div>

            <Card className="bg-[#050505] border-[#222222] p-8 text-center space-y-6 relative overflow-hidden">
              <div className="absolute top-2 right-2 px-2 py-0.5 rounded text-[9px] font-mono bg-[#1c1c1c] text-[#737373] border border-[#2a2a2a]">
                PREVIEW
              </div>

              <div className="w-14 h-14 mx-auto rounded-full bg-[#111111] border border-[#222222] flex items-center justify-center">
                <Wrench className="w-7 h-7 text-white" />
              </div>

              <div className="space-y-2">
                <span className="px-2.5 py-1 rounded text-[10px] font-mono tracking-widest uppercase bg-[#141414] text-[#a0a0a0] border border-[#262626]">
                  HTTP 503 — SYSTEM UPGRADE
                </span>
                <h3 className="text-xl font-bold font-mono text-white tracking-tight mt-2">
                  TRUSTGUARD AI UNDER MAINTENANCE
                </h3>
                <p className="text-xs font-mono text-[#a0a0a0] max-w-sm mx-auto leading-relaxed">
                  {message || 'TrustGuard AI is temporarily undergoing scheduled maintenance.'}
                </p>
              </div>

              {estimatedTime && (
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-[#0d0d0d] border border-[#1f1f1f] text-[11px] font-mono text-[#cccccc]">
                  <Clock className="w-3.5 h-3.5 text-white" />
                  <span>Estimated Return: {estimatedTime}</span>
                </div>
              )}

              <div className="pt-4 border-t border-[#1a1a1a] text-[10px] font-mono text-[#525252]">
                Our security analysis pipeline & intelligence feeds will resume shortly.
              </div>
            </Card>

            <Card className="bg-[#111111] border-[#222222] p-4 text-xs font-mono text-[#737373] space-y-2">
              <div className="flex items-center gap-2 text-[#a0a0a0]">
                <Info className="w-4 h-4 text-white" />
                <span className="font-semibold">Security & Access Policy</span>
              </div>
              <p>
                Maintenance mode is enforced at the backend HTTP gateway. Requests to <code className="text-white">/api/v1/admin/*</code> and <code className="text-white">/api/v1/maintenance/status</code> bypass the 503 handler to allow continuous administration.
              </p>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
