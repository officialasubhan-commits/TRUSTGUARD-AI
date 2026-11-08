import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertOctagon,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  Flame,
  RefreshCw,
  Shield,
  Users,
  Wrench,
  XCircle,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import {
  AdminDashboardActivity,
  AdminDashboardStats,
  AdminEventItem,
} from '../../types/admin';

export const AdminDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [activity, setActivity] = useState<AdminDashboardActivity | null>(null);
  const [events, setEvents] = useState<AdminEventItem[]>([]);
  const [timeRange, setTimeRange] = useState<7 | 30 | 90>(30);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadData = async (range: 7 | 30 | 90 = timeRange) => {
    try {
      const [statsData, actData, eventsData] = await Promise.all([
        adminService.getDashboardStats(),
        adminService.getDashboardActivity(range),
        adminService.getRecentEvents(12),
      ]);
      setStats(statsData);
      setActivity(actData);
      setEvents(eventsData);
    } catch (err) {
      console.error('Failed loading admin dashboard data:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData(timeRange);
  }, [timeRange]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadData(timeRange);
  };

  if (isLoading) {
    return (
      <div className="py-24 flex flex-col items-center justify-center space-y-4">
        <PixelSpinner size={36} />
        <p className="text-xs font-mono text-[#888888] uppercase tracking-widest">
          Aggregating Platform Security Telemetry...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* ----------------------------------------------------------- */}
      {/* Page Header                                                 */}
      {/* ----------------------------------------------------------- */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1E1E1E]">
        <div>
          <h1 className="text-xl sm:text-2xl font-light tracking-tight text-white flex items-center space-x-2">
            <span>Platform Overview & Telemetry</span>
          </h1>
          <p className="text-xs font-mono text-[#888888] mt-1">
            REAL-TIME SECURITY METRICS, SCAN VOLUME & COMMUNITY MODERATION STATUS
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Time range selector */}
          <div className="flex items-center bg-[#121212] border border-[#262626] rounded p-0.5 text-xs font-mono">
            {([7, 30, 90] as const).map((r) => (
              <button
                key={r}
                onClick={() => setTimeRange(r)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  timeRange === r
                    ? 'bg-white text-black font-semibold'
                    : 'text-[#888888] hover:text-white'
                }`}
              >
                {r}D
              </button>
            ))}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            isLoading={isRefreshing}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            REFRESH
          </Button>
        </div>
      </div>

      {/* ----------------------------------------------------------- */}
      {/* Maintenance Status Banner (if active)                       */}
      {/* ----------------------------------------------------------- */}
      {stats?.maintenance_enabled && (
        <div className="p-4 bg-amber-950/30 border border-amber-800/60 rounded flex items-center justify-between gap-4 text-xs font-mono text-amber-200">
          <div className="flex items-center space-x-3">
            <Wrench className="w-5 h-5 text-amber-400 shrink-0" />
            <div>
              <p className="font-semibold text-amber-300">MAINTENANCE MODE IS CURRENTLY ACTIVE</p>
              <p className="text-[11px] text-amber-300/80 mt-0.5">
                {stats.maintenance_message || 'Public visitor traffic is temporarily restricted.'}
              </p>
            </div>
          </div>
          <a
            href="/admin/maintenance"
            className="px-3 py-1.5 bg-amber-400 text-black font-bold rounded text-[11px] hover:bg-amber-300 transition-colors shrink-0"
          >
            CONFIGURE
          </a>
        </div>
      )}

      {/* ----------------------------------------------------------- */}
      {/* Top Key Statistics Grid                                     */}
      {/* ----------------------------------------------------------- */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Scans */}
        <Card pixelFrame className="p-4 bg-[#0E0E0E] border-[#222222]">
          <div className="flex items-center justify-between text-[#888888] mb-2">
            <span className="text-[11px] font-mono tracking-wider">TOTAL SCANS</span>
            <Activity className="w-4 h-4 text-white" />
          </div>
          <p className="text-2xl sm:text-3xl font-light text-white font-mono">
            {stats?.total_scans.toLocaleString() || 0}
          </p>
          <p className="text-[10px] font-mono text-emerald-400 mt-1">Multi-layer Engine</p>
        </Card>

        {/* High Risk URLs */}
        <Card pixelFrame className="p-4 bg-[#0E0E0E] border-[#222222]">
          <div className="flex items-center justify-between text-[#888888] mb-2">
            <span className="text-[11px] font-mono tracking-wider">HIGH-RISK DETECTIONS</span>
            <AlertOctagon className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-light text-rose-400 font-mono">
            {stats?.high_risk_urls.toLocaleString() || 0}
          </p>
          <p className="text-[10px] font-mono text-[#777777] mt-1">Threats neutralised</p>
        </Card>

        {/* Community Reports */}
        <Card pixelFrame className="p-4 bg-[#0E0E0E] border-[#222222]">
          <div className="flex items-center justify-between text-[#888888] mb-2">
            <span className="text-[11px] font-mono tracking-wider">COMMUNITY REPORTS</span>
            <Flame className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-light text-white font-mono">
            {stats?.total_community_reports || 0}
          </p>
          <p className="text-[10px] font-mono text-amber-400 mt-1">
            {stats?.pending_reports || 0} pending review
          </p>
        </Card>

        {/* Total Users */}
        <Card pixelFrame className="p-4 bg-[#0E0E0E] border-[#222222]">
          <div className="flex items-center justify-between text-[#888888] mb-2">
            <span className="text-[11px] font-mono tracking-wider">REGISTERED USERS</span>
            <Users className="w-4 h-4 text-white" />
          </div>
          <p className="text-2xl sm:text-3xl font-light text-white font-mono">
            {stats?.total_users || 0}
          </p>
          <p className="text-[10px] font-mono text-emerald-400 mt-1">
            {stats?.active_users || 0} active accounts
          </p>
        </Card>
      </div>

      {/* Moderation Status Breakdown Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#0D0D0D] p-3 border border-[#222222] rounded text-xs font-mono">
        <div className="flex items-center space-x-2">
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-[#888888]">PENDING:</span>
          <span className="text-white font-semibold">{stats?.pending_reports || 0}</span>
        </div>
        <div className="flex items-center space-x-2">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-[#888888]">VERIFIED:</span>
          <span className="text-emerald-400 font-semibold">{stats?.verified_reports || 0}</span>
        </div>
        <div className="flex items-center space-x-2">
          <XCircle className="w-3.5 h-3.5 text-rose-400" />
          <span className="text-[#888888]">REJECTED:</span>
          <span className="text-rose-400 font-semibold">{stats?.rejected_reports || 0}</span>
        </div>
        <div className="flex items-center space-x-2">
          <Shield className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-[#888888]">RESOLVED:</span>
          <span className="text-blue-400 font-semibold">{stats?.resolved_reports || 0}</span>
        </div>
      </div>

      {/* ----------------------------------------------------------- */}
      {/* Activity Charts Section                                     */}
      {/* ----------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline Chart */}
        <Card pixelFrame className="p-5 bg-[#0E0E0E] border-[#222222] lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-[#202020] pb-3">
            <div>
              <h2 className="text-sm font-mono font-medium text-white">SCAN & REGISTRATION VELOCITY</h2>
              <p className="text-[11px] font-mono text-[#777777]">
                Daily volume over the past {timeRange} days
              </p>
            </div>
            <span className="text-[10px] font-mono text-[#888888] bg-[#161616] px-2 py-0.5 border border-[#282828] rounded">
              TIME SERIES
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={activity?.timeline || []}>
                <defs>
                  <linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FFFFFF" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#FFFFFF" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="userGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#888888" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#888888" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1C1C1C" />
                <XAxis dataKey="date" stroke="#555555" fontSize={10} tickLine={false} />
                <YAxis stroke="#555555" fontSize={10} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111111',
                    borderColor: '#333333',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
                <Area
                  type="monotone"
                  dataKey="scans"
                  name="Scans Executed"
                  stroke="#FFFFFF"
                  fillOpacity={1}
                  fill="url(#scanGrad)"
                />
                <Area
                  type="monotone"
                  dataKey="registrations"
                  name="New Users"
                  stroke="#888888"
                  fillOpacity={1}
                  fill="url(#userGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Threat Category Distribution */}
        <Card pixelFrame className="p-5 bg-[#0E0E0E] border-[#222222] space-y-4">
          <div className="flex items-center justify-between border-b border-[#202020] pb-3">
            <div>
              <h2 className="text-sm font-mono font-medium text-white">THREAT CATEGORIES</h2>
              <p className="text-[11px] font-mono text-[#777777]">Classification distribution</p>
            </div>
            <Flame className="w-4 h-4 text-amber-400" />
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={activity?.threat_categories || []}
                layout="vertical"
                margin={{ top: 5, right: 20, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1C1C1C" horizontal={false} />
                <XAxis type="number" stroke="#555555" fontSize={10} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="category"
                  stroke="#888888"
                  fontSize={10}
                  tickLine={false}
                  width={75}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111111',
                    borderColor: '#333333',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                  }}
                />
                <Bar dataKey="count" name="Reports" fill="#FFFFFF" radius={[0, 2, 2, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* ----------------------------------------------------------- */}
      {/* Recent Platform & Administrative Events Feed                */}
      {/* ----------------------------------------------------------- */}
      <Card pixelFrame className="p-5 bg-[#0E0E0E] border-[#222222] space-y-4">
        <div className="flex items-center justify-between border-b border-[#202020] pb-3">
          <div>
            <h2 className="text-sm font-mono font-medium text-white">RECENT ADMINISTRATIVE EVENTS</h2>
            <p className="text-[11px] font-mono text-[#777777]">
              Live security audit log stream
            </p>
          </div>
          <a
            href="/admin/audit-logs"
            className="text-xs font-mono text-[#A1A1A1] hover:text-white flex items-center space-x-1"
          >
            <span>FULL AUDIT TRAIL</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </a>
        </div>

        <div className="divide-y divide-[#181818] overflow-hidden">
          {events.length === 0 ? (
            <p className="py-6 text-center text-xs font-mono text-[#666666]">
              NO RECENT ADMINISTRATIVE EVENTS RECORDED.
            </p>
          ) : (
            events.map((ev) => (
              <div key={ev.id} className="py-3 flex items-center justify-between gap-4 text-xs font-mono">
                <div className="flex items-center space-x-3 truncate">
                  <span
                    className={`w-2 h-2 rounded-full shrink-0 ${
                      ev.severity === 'warning'
                        ? 'bg-amber-400'
                        : ev.severity === 'danger'
                        ? 'bg-rose-500'
                        : 'bg-emerald-400'
                    }`}
                  />
                  <div className="truncate">
                    <p className="text-white font-medium truncate">{ev.title}</p>
                    <p className="text-[11px] text-[#777777] truncate">{ev.description}</p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-[10px] text-[#666666]">
                    {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
};
