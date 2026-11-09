import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AdminAuthProvider } from './context/AdminAuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { ProtectedAdminRoute } from './components/admin/ProtectedAdminRoute';
import { RootLayout } from './layouts/RootLayout';
import { AdminLayout } from './layouts/AdminLayout';

// Public & User Pages
import { HomePage } from './pages/HomePage';
import { ScannerPage } from './pages/ScannerPage';
import { ReportPage } from './pages/ReportPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { AuthCallbackPage } from './pages/AuthCallbackPage';
import { DashboardPage } from './pages/DashboardPage';
import { HistoryPage } from './pages/HistoryPage';
import { CommunityPage } from './pages/CommunityPage';
import { SubmitReportPage } from './pages/SubmitReportPage';
import { MyReportsPage } from './pages/MyReportsPage';
import { ProfilePage } from './pages/ProfilePage';
import { DesignSystemShowcasePage } from './pages/DesignSystemShowcasePage';
import { AnimationShowcasePage } from './pages/AnimationShowcasePage';
import { ContributorsPage } from './pages/ContributorsPage';
import { DynamicPage } from './pages/DynamicPage';
import { NotFoundPage } from './pages/NotFoundPage';

// Admin Pages
import { AdminLoginPage } from './pages/admin/AdminLoginPage';
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage';
import { AdminUsersPage } from './pages/admin/AdminUsersPage';
import { AdminContributorsPage } from './pages/admin/AdminContributorsPage';
import { AdminPagesPage } from './pages/admin/AdminPagesPage';
import { AdminScansPage } from './pages/admin/AdminScansPage';
import { AdminReportsPage } from './pages/admin/AdminReportsPage';
import { AdminReportDetailPage } from './pages/admin/AdminReportDetailPage';
import { AdminThreatIntelPage } from './pages/admin/AdminThreatIntelPage';
import { AdminSystemHealthPage } from './pages/admin/AdminSystemHealthPage';
import { AdminMaintenancePage } from './pages/admin/AdminMaintenancePage';
import { AdminAuditLogsPage } from './pages/admin/AdminAuditLogsPage';
import { AdminSettingsPage } from './pages/admin/AdminSettingsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AdminAuthProvider>
          <Routes>
            {/* 1. Dedicated Admin Authentication Route */}
            <Route path="/admin/login" element={<AdminLoginPage />} />

            {/* 2. Protected Administrator Workspace Routes */}
            <Route
              path="/admin"
              element={
                <ProtectedAdminRoute>
                  <AdminLayout />
                </ProtectedAdminRoute>
              }
            >
              <Route index element={<AdminDashboardPage />} />
              <Route path="users" element={<AdminUsersPage />} />
              <Route path="contributors" element={<AdminContributorsPage />} />
              <Route path="pages" element={<AdminPagesPage />} />
              <Route path="scans" element={<AdminScansPage />} />
              <Route path="reports" element={<AdminReportsPage />} />
              <Route path="reports/:reportId" element={<AdminReportDetailPage />} />
              <Route path="threat-intelligence" element={<AdminThreatIntelPage />} />
              <Route path="system" element={<AdminSystemHealthPage />} />
              <Route path="maintenance" element={<AdminMaintenancePage />} />
              <Route path="audit-logs" element={<AdminAuditLogsPage />} />
              <Route path="settings" element={<AdminSettingsPage />} />
            </Route>

            {/* 3. Public & User Application Routes */}
            <Route path="/" element={<RootLayout />}>
              <Route index element={<HomePage />} />
              <Route path="scan" element={<ScannerPage />} />
              <Route path="report/:scanId" element={<ReportPage />} />
              <Route path="contributors" element={<ContributorsPage />} />
              <Route path="p/:slug" element={<DynamicPage />} />
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />
              <Route path="forgot-password" element={<ForgotPasswordPage />} />
              <Route path="reset-password" element={<ResetPasswordPage />} />
              <Route path="auth/callback" element={<AuthCallbackPage />} />

              {/* Protected User Routes */}
              <Route
                path="dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="dashboard/history"
                element={
                  <ProtectedRoute>
                    <HistoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="history"
                element={
                  <ProtectedRoute>
                    <HistoryPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="profile"
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="community/report"
                element={
                  <ProtectedRoute>
                    <SubmitReportPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="community/my-reports"
                element={
                  <ProtectedRoute>
                    <MyReportsPage />
                  </ProtectedRoute>
                }
              />

              {/* Showcase & Informational Routes */}
              <Route path="community" element={<CommunityPage />} />
              <Route path="design-system" element={<DesignSystemShowcasePage />} />
              <Route path="animations" element={<AnimationShowcasePage />} />

              {/* 404 Catch-All */}
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </AdminAuthProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
