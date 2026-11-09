import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { Activity, Calendar } from 'lucide-react';
import { Card } from '../common/Card';
import { Skeleton } from '../common/Skeleton';
import { scanService } from '../../services/scanService';
import { DailyScanActivity } from '../../types/scan';

// High-performance timeline cache to prevent layout jumps on navigation
const timelineCache = new Map<number, { data: DailyScanActivity[]; timestamp: number }>();
const TIMELINE_CACHE_TTL_MS = 60000; // 60 seconds

interface ActivityChartProps {
  onTotalScansCalculated?: (total: number) => void;
}

export const ActivityChart: React.FC<ActivityChartProps> = () => {
  const [days, setDays] = useState<7 | 30 | 90>(30);
  const [timeline, setTimeline] = useState<DailyScanActivity[]>(() => {
    const cached = timelineCache.get(30);
    if (cached && Date.now() - cached.timestamp < TIMELINE_CACHE_TTL_MS) {
      return cached.data;
    }
    return [];
  });
  const [isLoading, setIsLoading] = useState<boolean>(() => {
    const cached = timelineCache.get(30);
    return !cached || Date.now() - cached.timestamp >= TIMELINE_CACHE_TTL_MS;
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();

    const fetchTimeline = async () => {
      const cached = timelineCache.get(days);
      const isFresh = cached && Date.now() - cached.timestamp < TIMELINE_CACHE_TTL_MS;

      if (cached) {
        setTimeline(cached.data);
      }
      if (!isFresh) {
        setIsLoading(!cached);
      }
      setError(null);

      try {
        const data = await scanService.getActivityTimeline(days, controller.signal);
        if (isMounted) {
          timelineCache.set(days, { data, timestamp: Date.now() });
          setTimeline(data);
        }
      } catch (err: any) {
        if (!controller.signal.aborted && isMounted && !cached) {
          setError('Unable to load scan activity timeline.');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchTimeline();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [days]);

  const totalScansInWindow = timeline.reduce((acc, curr) => acc + curr.scan_count, 0);

  // Custom monochromatic tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data: DailyScanActivity = payload[0].payload;
      return (
        <div className="p-3 bg-[#101010] border border-[#292929] text-xs font-mono space-y-1 shadow-xl">
          <div className="text-[#A1A1A1] border-b border-[#222222] pb-1 font-semibold">
            {label}
          </div>
          <div className="flex justify-between space-x-4 text-[#F5F5F5]">
            <span>Total Scans:</span>
            <span className="font-bold">{data.scan_count}</span>
          </div>
          {data.threat_count > 0 && (
            <div className="flex justify-between space-x-4 text-[#F87171]">
              <span>Threats Flagged:</span>
              <span className="font-bold">{data.threat_count}</span>
            </div>
          )}
          {data.moderate_count > 0 && (
            <div className="flex justify-between space-x-4 text-[#FBBF24]">
              <span>Moderate Risk:</span>
              <span className="font-bold">{data.moderate_count}</span>
            </div>
          )}
          {data.safe_count > 0 && (
            <div className="flex justify-between space-x-4 text-[#4ADE80]">
              <span>Safe / Low Risk:</span>
              <span className="font-bold">{data.safe_count}</span>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <Card pixelFrame className="p-5 md:p-6 space-y-4">
      {/* Header and Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#222222]">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-[#A1A1A1]" />
          <div>
            <h3 className="text-xs font-mono font-semibold uppercase text-[#F5F5F5]">
              SCANNING FREQUENCY & TEMPORAL ACTIVITY
            </h3>
            <span className="text-[11px] font-mono text-[#666666]">
              DAILY AUDIT HISTOGRAM OVER HISTORICAL WINDOW
            </span>
          </div>
        </div>

        {/* Date Range Selector */}
        <div className="flex items-center space-x-1 font-mono text-[11px]">
          <span className="text-[#666666] mr-1 hidden sm:inline">WINDOW:</span>
          {([7, 30, 90] as const).map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-2.5 py-1 border transition-colors ${
                days === d
                  ? 'bg-[#F5F5F5] text-[#080808] border-[#F5F5F5] font-semibold'
                  : 'bg-[#101010] text-[#A1A1A1] border-[#292929] hover:text-[#F5F5F5]'
              }`}
            >
              {d}D
            </button>
          ))}
        </div>
      </div>

      {/* Chart Body */}
      {isLoading ? (
        <div className="h-48 flex items-center justify-center">
          <Skeleton className="w-full h-full" />
        </div>
      ) : error ? (
        <div className="h-48 flex items-center justify-center text-xs font-mono text-[#F87171]">
          {error}
        </div>
      ) : totalScansInWindow === 0 ? (
        <div className="h-48 flex flex-col items-center justify-center space-y-2 border border-dashed border-[#222222] p-6 text-center">
          <Calendar className="w-6 h-6 text-[#555555]" />
          <p className="text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
            INSUFFICIENT HISTORICAL ACTIVITY
          </p>
          <p className="text-[11px] font-mono text-[#666666] max-w-sm">
            No audits recorded during the past {days} days. Scan target websites to populate temporal trends.
          </p>
        </div>
      ) : (
        <div className="h-56 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={timeline} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
              <CartesianGrid stroke="#1A1A1A" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="date"
                stroke="#666666"
                fontSize={10}
                tickLine={false}
                axisLine={{ stroke: '#292929' }}
                tickFormatter={(val) => {
                  // Format '2026-11-08' -> 'Nov 08'
                  const parts = val.split('-');
                  if (parts.length === 3) {
                    const d = new Date(val);
                    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                  }
                  return val;
                }}
              />
              <YAxis
                stroke="#666666"
                fontSize={10}
                tickLine={false}
                axisLine={{ stroke: '#292929' }}
                allowDecimals={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: '#141414' }} />
              <Bar dataKey="safe_count" stackId="a" fill="#4ADE80" radius={[0, 0, 0, 0]} />
              <Bar dataKey="moderate_count" stackId="a" fill="#FBBF24" radius={[0, 0, 0, 0]} />
              <Bar dataKey="threat_count" stackId="a" fill="#F87171" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Legend & Summary */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#1F1F1F] text-[11px] font-mono text-[#666666]">
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 bg-[#4ADE80] inline-block" />
            <span>SAFE / LOW</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 bg-[#FBBF24] inline-block" />
            <span>MODERATE</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 bg-[#F87171] inline-block" />
            <span>THREAT / CRITICAL</span>
          </span>
        </div>

        <div>
          <span>TOTAL IN WINDOW: </span>
          <span className="text-[#F5F5F5] font-semibold">{totalScansInWindow} SCANS</span>
        </div>
      </div>
    </Card>
  );
};

export default ActivityChart;

