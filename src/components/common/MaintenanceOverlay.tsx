import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Clock, RefreshCw, Wrench } from 'lucide-react';
import { adminService } from '../../services/adminService';
import { Button } from './Button';

export const MaintenanceOverlay: React.FC = () => {
  const location = useLocation();
  const [maintenance, setMaintenance] = useState<{
    enabled: boolean;
    message?: string;
    estimatedTime?: string;
  }>({
    enabled: false,
  });
  const [isChecking, setIsChecking] = useState(false);

  // Exempt all admin routes
  const isAdminRoute = location.pathname.startsWith('/admin');

  const checkStatus = async () => {
    if (isAdminRoute) return;
    try {
      const data = await adminService.getPublicMaintenanceStatus();
      setMaintenance({
        enabled: data.maintenance_enabled,
        message: data.maintenance_message,
        estimatedTime: data.estimated_restore_time,
      });
    } catch {
      // If network fails or server returns 503, check if error was maintenance
    }
  };

  useEffect(() => {
    if (!isAdminRoute) {
      checkStatus();
      const interval = setInterval(checkStatus, 30000); // Check every 30s
      return () => clearInterval(interval);
    }
  }, [location.pathname]);

  if (isAdminRoute || !maintenance.enabled) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 bg-[#080808] flex items-center justify-center p-6 text-center select-none overflow-y-auto">
      <div className="max-w-lg w-full space-y-8 py-12">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-[#111111] border border-[#262626] flex items-center justify-center shadow-xl">
          <Wrench className="w-8 h-8 text-white" />
        </div>

        <div className="space-y-3">
          <span className="inline-block px-3 py-1 rounded text-xs font-mono font-semibold tracking-widest uppercase bg-[#141414] text-[#a0a0a0] border border-[#2a2a2a]">
            SYSTEM UPGRADE IN PROGRESS
          </span>
          <h1 className="text-3xl font-bold font-mono text-white tracking-tight">
            TRUSTGUARD AI MAINTENANCE
          </h1>
          <p className="text-sm font-mono text-[#a3a3a3] leading-relaxed pt-2">
            {maintenance.message ||
              'TrustGuard AI is temporarily undergoing scheduled maintenance. We are optimizing our security analysis engines and will be back shortly.'}
          </p>
        </div>

        {maintenance.estimatedTime && (
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded bg-[#111111] border border-[#222222] text-xs font-mono text-[#e5e5e5]">
            <Clock className="w-4 h-4 text-white" />
            <span>Estimated Restoration: {maintenance.estimatedTime}</span>
          </div>
        )}

        <div className="pt-6 border-t border-[#1a1a1a] flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={async () => {
              setIsChecking(true);
              await checkStatus();
              setIsChecking(false);
            }}
            className="border-[#333333] hover:bg-[#1a1a1a] text-white font-mono text-xs px-4"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-2 ${isChecking ? 'animate-spin' : ''}`} />
            Check Availability
          </Button>
          <a
            href="/admin/login"
            className="text-xs font-mono text-[#737373] hover:text-[#a0a0a0] transition-colors underline underline-offset-4"
          >
            Administrator Login
          </a>
        </div>
      </div>
    </div>
  );
};
