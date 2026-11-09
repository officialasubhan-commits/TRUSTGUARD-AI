import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Container } from '../components/common/Container';
import { Button } from '../components/common/Button';
import {
  WelcomeHeader,
  SecurityStatisticsGrid,
  ActivityChart,
  RecentActivityList,
  UserCommunitySubmissions,
} from '../components/dashboard';
import { useAuth } from '../context/AuthContext';
import { scanService } from '../services/scanService';
import { communityService } from '../services/communityService';
import { formatApiError } from '../services/api';
import { ScanStatistics } from '../types/scan';
import { CommunityReportUserItem } from '../types/community';

// Short-term in-memory cache to make tab switches and re-renders instantaneous (< 5ms)
let cachedStats: ScanStatistics | null = null;
let cachedStatsTimestamp = 0;
let cachedReports: CommunityReportUserItem[] = [];
let cachedTotal = 0;
let cachedReportsTimestamp = 0;
const DASHBOARD_CACHE_TTL_MS = 30000; // 30 seconds

export const DashboardPage: React.FC = () => {
  const { user, profile, logout } = useAuth();
  const navigate = useNavigate();

  const [statistics, setStatistics] = useState<ScanStatistics | null>(() => {
    if (cachedStats && Date.now() - cachedStatsTimestamp < DASHBOARD_CACHE_TTL_MS) {
      return cachedStats;
    }
    return null;
  });

  const [userReports, setUserReports] = useState<CommunityReportUserItem[]>(() => {
    if (Date.now() - cachedReportsTimestamp < DASHBOARD_CACHE_TTL_MS) {
      return cachedReports;
    }
    return [];
  });

  const [totalUserReports, setTotalUserReports] = useState<number>(() => {
    if (Date.now() - cachedReportsTimestamp < DASHBOARD_CACHE_TTL_MS) {
      return cachedTotal;
    }
    return 0;
  });

  const [isStatsLoading, setIsStatsLoading] = useState<boolean>(() => {
    return !cachedStats || Date.now() - cachedStatsTimestamp >= DASHBOARD_CACHE_TTL_MS;
  });

  const [isReportsLoading, setIsReportsLoading] = useState<boolean>(() => {
    return cachedReports.length === 0 && Date.now() - cachedReportsTimestamp >= DASHBOARD_CACHE_TTL_MS;
  });

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchDashboardData = useCallback(async (signal?: AbortSignal) => {
    setErrorMessage(null);

    if (!cachedStats || Date.now() - cachedStatsTimestamp >= DASHBOARD_CACHE_TTL_MS) {
      setIsStatsLoading(true);
    }
    if (cachedReports.length === 0 && Date.now() - cachedReportsTimestamp >= DASHBOARD_CACHE_TTL_MS) {
      setIsReportsLoading(true);
    }

    // Fetch scan statistics and community reports in parallel, decoupling rendering
    const statsPromise = scanService
      .getStatistics(signal)
      .then((data) => {
        cachedStats = data;
        cachedStatsTimestamp = Date.now();
        setStatistics(data);
      })
      .catch((err) => {
        if (err?.name !== 'CanceledError' && err?.code !== 'ERR_CANCELED') {
          const formatted = formatApiError(err);
          setErrorMessage(
            formatted.message || 'Unable to retrieve your security scanning telemetry from the server.'
          );
        }
      })
      .finally(() => {
        setIsStatsLoading(false);
      });

    const reportsPromise = communityService
      .getMyReports(1, 5, signal)
      .then((data) => {
        cachedReports = data.items || [];
        cachedTotal = data.total || 0;
        cachedReportsTimestamp = Date.now();
        setUserReports(data.items || []);
        setTotalUserReports(data.total || 0);
      })
      .catch(() => {})
      .finally(() => {
        setIsReportsLoading(false);
      });

    await Promise.allSettled([statsPromise, reportsPromise]);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchDashboardData(controller.signal);

    return () => {
      controller.abort();
    };
  }, [fetchDashboardData]);

  const handleLogout = async () => {
    await logout();
    navigate('/', { replace: true });
  };

  return (
    <div className="flex-1 py-10 md:py-16 px-4">
      <Container size="xl">
        <div className="space-y-8">
          {/* Welcome and Identity Header */}
          <WelcomeHeader user={user} profile={profile} onLogout={handleLogout} />

          {/* Error Banner */}
          {errorMessage && (
            <div className="p-4 bg-[#1C1212] border border-[#F87171]/40 flex items-center justify-between gap-3 text-xs font-mono text-[#FCA5A5]">
              <div className="flex items-center space-x-2.5">
                <AlertTriangle className="w-4 h-4 text-[#F87171] shrink-0" />
                <span>{errorMessage}</span>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => fetchDashboardData()}
                leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              >
                RETRY
              </Button>
            </div>
          )}

          {/* Security Telemetry Metric Cards */}
          <SecurityStatisticsGrid statistics={statistics} isLoading={isStatsLoading} />

          {/* Temporal Activity Chart */}
          <ActivityChart />

          {/* Recent Security Scans List */}
          <RecentActivityList
            recentScans={statistics?.recent_scans || []}
            isLoading={isStatsLoading}
          />

          {/* Community Threat Submissions & Status */}
          <UserCommunitySubmissions
            reports={userReports}
            totalReports={totalUserReports}
            isLoading={isReportsLoading}
          />
        </div>
      </Container>
    </div>
  );
};

export default DashboardPage;
