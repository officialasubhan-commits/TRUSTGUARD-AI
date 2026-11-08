import React from 'react';
import { Navigate, useLocation, Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Container } from '../common/Container';
import { Card } from '../common/Card';
import { Button } from '../common/Button';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center py-24">
        <Container size="sm">
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <div className="w-8 h-8 border-2 border-[#292929] border-t-[#F5F5F5] rounded-full animate-spin" />
            <div className="space-y-1">
              <p className="text-xs font-mono tracking-widest text-[#F5F5F5] uppercase">
                VERIFYING SECURITY CREDENTIALS
              </p>
              <p className="text-[11px] font-mono text-[#666666]">
                AUTHENTICATING WITH TRUSTGUARD ENGINE...
              </p>
            </div>
          </div>
        </Container>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Preserve intended destination in router location state
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return (
      <div className="flex-1 flex items-center justify-center py-20">
        <Container size="sm">
          <Card pixelFrame className="p-8 space-y-6 text-center">
            <div className="w-12 h-12 mx-auto bg-[#181818] border border-[#F87171]/40 flex items-center justify-center text-[#F87171]">
              <ShieldAlert className="w-6 h-6" />
            </div>

            <div className="space-y-2">
              <h1 className="text-xl font-mono font-bold text-[#F5F5F5] uppercase">
                ACCESS RESTRICTED (403)
              </h1>
              <p className="text-xs text-[#A1A1A1] leading-relaxed">
                This sector requires elevated <span className="font-mono text-[#F5F5F5] font-semibold">{requiredRole.toUpperCase()}</span> clearance.
                Your current authorization profile is <span className="font-mono text-[#A1A1A1]">{user?.role || 'standard user'}</span>.
              </p>
            </div>

            <div className="p-3 bg-[#0D0D0D] border border-[#222222] text-[11px] font-mono text-[#666666] text-left space-y-1">
              <div>SUBJECT ID: {user?.id}</div>
              <div>IDENTITY: {user?.email}</div>
              <div>POLICY: ROLE_BASED_ACCESS_CONTROL</div>
            </div>

            <div className="pt-2 flex justify-center">
              <Link to="/dashboard">
                <Button variant="secondary" leftIcon={<ArrowLeft className="w-4 h-4" />}>
                  RETURN TO DASHBOARD
                </Button>
              </Link>
            </div>
          </Card>
        </Container>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;

