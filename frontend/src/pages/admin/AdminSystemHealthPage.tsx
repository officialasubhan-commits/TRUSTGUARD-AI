import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Database,
  Globe,
  Lock,
  Play,
  Server,
  Shield,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import { ServiceHealthItem, SystemHealthResponse } from '../../types/admin';

export const AdminSystemHealthPage: React.FC = () => {
  const [healthData, setHealthData] = useState<SystemHealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunningCheck, setIsRunningCheck] = useState(false);

  const fetchHealth = async () => {
    try {
      const data = await adminService.getSystemHealth();
      setHealthData(data);
    } catch (err) {
      console.error('Failed to load system health diagnostics:', err);
    } finally {
      setIsLoading(false);
      setIsRunningCheck(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleRunCheck = () => {
    setIsRunningCheck(true);
    fetchHealth();
  };

  const getServiceIcon = (name: string) => {
    if (name.includes('FastAPI')) return <Server className="w-5 h-5 text-white" />;
    if (name.includes('PostgreSQL') || name.includes('Database')) return <Database className="w-5 h-5 text-white" />;
    if (name.includes('Auth')) return <Lock className="w-5 h-5 text-white" />;
    if (name.includes('VirusTotal')) return <Globe className="w-5 h-5 text-white" />;
    if (name.includes('ML') || name.includes('Machine Learning')) return <Cpu className="w-5 h-5 text-white" />;
    if (name.includes('SSL') || name.includes('TLS')) return <Shield className="w-5 h-5 text-white" />;
    return <Activity className="w-5 h-5 text-white" />;
  };

  const getStatusBadge = (status: ServiceHealthItem['status']) => {
    switch (status) {
      case 'OPERATIONAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-medium bg-[#142814] text-[#4ade80] border border-[#234d23]">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#4ade80]" />
            OPERATIONAL
          </span>
        );
      case 'DEGRADED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-medium bg-[#2a2212] text-[#fbbf24] border border-[#4d3d1e]">
            <AlertTriangle className="w-3.5 h-3.5 text-[#fbbf24]" />
            DEGRADED
          </span>
        );
      case 'UNAVAILABLE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-medium bg-[#2e1414] text-[#f87171] border border-[#522323]">
            <AlertOctagon className="w-3.5 h-3.5 text-[#f87171]" />
            UNAVAILABLE
          </span>
        );
      case 'NOT_CONFIGURED':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-medium bg-[#1a1a1a] text-[#a0a0a0] border border-[#333333]">
            NOT CONFIGURED
          </span>
        );
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#222222] pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono uppercase">
              System Health & Diagnostics
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium tracking-wide border bg-[#111111] text-[#a0a0a0] border-[#333333]">
              DIAGNOSTICS
            </span>
          </div>
          <p className="text-sm text-[#737373] mt-1 font-mono">
            Real-time status probes for core infrastructure, inference engines & third-party connectors
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            size="sm"
            onClick={handleRunCheck}
            disabled={isRunningCheck}
            className="bg-white hover:bg-[#e5e5e5] text-black font-mono text-xs font-semibold px-4 py-2"
          >
            <Play className={`w-3.5 h-3.5 mr-2 ${isRunningCheck ? 'animate-spin' : ''}`} />
            Run Diagnostics Now
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="py-24 flex flex-col items-center justify-center space-y-4">
          <PixelSpinner />
          <p className="text-xs font-mono text-[#737373] tracking-widest uppercase">
            Executing Live System Probes...
          </p>
        </div>
      ) : !healthData ? (
        <Card className="bg-[#111111] border-[#222222] p-8 text-center">
          <AlertOctagon className="w-8 h-8 text-[#ef4444] mx-auto mb-3" />
          <p className="text-sm font-mono text-[#a0a0a0]">
            Unable to connect to diagnostic probes.
          </p>
          <Button
            size="sm"
            onClick={fetchHealth}
            className="mt-4 bg-white text-black font-mono text-xs"
          >
            Retry Diagnostics
          </Button>
        </Card>
      ) : (
        <>
          {/* Overall Health Status Banner */}
          <Card
            className={`border p-6 ${
              healthData.overall_status === 'OPERATIONAL'
                ? 'bg-[#0d1a0d] border-[#1f401f]'
                : healthData.overall_status === 'DEGRADED'
                ? 'bg-[#1f1a0d] border-[#40351f]'
                : 'bg-[#210e0e] border-[#4a1c1c]'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div
                  className={`w-12 h-12 rounded flex items-center justify-center ${
                    healthData.overall_status === 'OPERATIONAL'
                      ? 'bg-[#153315] text-[#4ade80]'
                      : healthData.overall_status === 'DEGRADED'
                      ? 'bg-[#3b2d13] text-[#fbbf24]'
                      : 'bg-[#3d1818] text-[#f87171]'
                  }`}
                >
                  {healthData.overall_status === 'OPERATIONAL' ? (
                    <CheckCircle2 className="w-6 h-6" />
                  ) : healthData.overall_status === 'DEGRADED' ? (
                    <AlertTriangle className="w-6 h-6" />
                  ) : (
                    <AlertOctagon className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <div className="text-xs font-mono uppercase tracking-wider text-[#a0a0a0]">
                    Overall System Condition
                  </div>
                  <div className="text-xl font-bold font-mono text-white mt-0.5">
                    ALL SYSTEMS {healthData.overall_status}
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-[11px] font-mono text-[#737373]">Last Verified</div>
                <div className="text-xs font-mono text-white mt-0.5">
                  {new Date(healthData.checked_at).toLocaleTimeString()} ({new Date(healthData.checked_at).toLocaleDateString()})
                </div>
              </div>
            </div>
          </Card>

          {/* Diagnostic Services Grid */}
          <div className="space-y-3">
            <h2 className="text-xs font-mono font-semibold text-[#a0a0a0] uppercase tracking-wider">
              Diagnostic Service Breakdown ({healthData.services.length})
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {healthData.services.map((service) => (
                <Card
                  key={service.service_name}
                  className="bg-[#111111] border-[#222222] p-5 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded bg-[#1a1a1a] flex items-center justify-center border border-[#2a2a2a]">
                          {getServiceIcon(service.service_name)}
                        </div>
                        <div>
                          <div className="font-mono text-sm font-semibold text-white">
                            {service.service_name}
                          </div>
                          <div className="text-[11px] font-mono text-[#737373] mt-0.5">
                            Checked {new Date(service.last_checked).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                      <div>{getStatusBadge(service.status)}</div>
                    </div>

                    <div className="text-xs font-mono text-[#a0a0a0] bg-[#0c0c0c] border border-[#1c1c1c] p-3 rounded my-3">
                      {service.message || 'All diagnostic probes returned healthy status.'}
                    </div>

                    {service.details && Object.keys(service.details).length > 0 && (
                      <div className="space-y-1 mt-2 text-[11px] font-mono">
                        {Object.entries(service.details).map(([key, value]) => (
                          <div key={key} className="flex items-center justify-between text-[#737373]">
                            <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                            <span className="text-[#cccccc]">
                              {typeof value === 'boolean' ? (value ? 'true' : 'false') : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-mono pt-3 border-t border-[#1c1c1c] mt-4">
                    <span className="text-[#525252]">Probe Latency</span>
                    <span className="text-white font-medium">
                      {service.latency_ms !== undefined ? `${service.latency_ms} ms` : 'N/A'}
                    </span>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
