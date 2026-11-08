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

export const DashboardPage: React.FC = () => {
  const { user, profile, logout } = useAuth();
  const navigate = useNavigate();

  const [statistics, setStatistics] = useState<ScanStatistics | null>(null);
  const [userReports, setUserReports] = useState<CommunityReportUserItem[]>([]);
  const [totalUserReports, setTotalUserReports] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchDashboardData = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [statsResult, communityResult] = await Promise.allSettled([
        scanService.getStatistics(signal),
        communityService.getMyReports(1, 5, signal),
      ]);

      if (statsResult.status === 'fulfilled') {
        setStatistics(statsResult.value);
      } else {
        const err = statsResult.reason;
        if (err?.name !== 'CanceledError' && err?.code !== 'ERR_CANCELED') {
          const formatted = formatApiError(err);
          setErrorMessage(
            formatted.message || 'Unable to retrieve your security scanning telemetry from the server.'
          );
        }
      }

      if (communityResult.status === 'fulfilled') {
        setUserReports(communityResult.value.items || []);
        setTotalUserReports(communityResult.value.total || 0);
      }
    } finally {
      setIsLoading(false);
    }
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
          <SecurityStatisticsGrid statistics={statistics} isLoading={isLoading} />

          {/* Temporal Activity Chart */}
          <ActivityChart />

          {/* Recent Security Scans List */}
          <RecentActivityList
            recentScans={statistics?.recent_scans || []}
            isLoading={isLoading}
          />

          {/* Community Threat Submissions & Status */}
          <UserCommunitySubmissions
            reports={userReports}
            totalReports={totalUserReports}
            isLoading={isLoading}
          />
        </div>
      </Container>
    </div>
  );
};

export default DashboardPage;
