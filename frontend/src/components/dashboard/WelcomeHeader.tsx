import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, ArrowRight, User as UserIcon, LogOut, Search } from 'lucide-react';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { User, UserProfile } from '../../types/auth';

interface WelcomeHeaderProps {
  user: User | null;
  profile: UserProfile | null;
  onLogout: () => void;
}

export const WelcomeHeader: React.FC<WelcomeHeaderProps> = ({
  user,
  profile,
  onLogout,
}) => {
  const displayName =
    user?.full_name || profile?.full_name || user?.email?.split('@')[0] || 'Analyst';

  const roleLabel = user?.role === 'admin' ? 'SYSTEM ADMINISTRATOR' : 'SECURITY ANALYST';

  return (
    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 pb-6 border-b border-[#222222]">
      {/* User Identity and Status */}
      <div className="flex items-start sm:items-center space-x-4">
        <div className="w-12 h-12 bg-[#121212] border border-[#292929] flex items-center justify-center shrink-0">
          <Shield className="w-6 h-6 text-[#F5F5F5]" />
        </div>

        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-light tracking-tight text-[#F5F5F5]">
              Welcome back, <span className="font-medium text-[#F5F5F5]">{displayName}</span>
            </h1>
            <Badge variant="safe" size="xs">
              ACTIVE
            </Badge>
          </div>

          <p className="text-xs font-mono text-[#666666] flex flex-wrap items-center gap-2">
            <span>{roleLabel}</span>
            <span>•</span>
            <span className="truncate max-w-[220px]" title={user?.email}>
              {user?.email}
            </span>
            <span>•</span>
            <span className="truncate max-w-[140px]" title={user?.id}>
              UID: {user?.id ? `${user.id.slice(0, 8)}...` : 'N/A'}
            </span>
          </p>
        </div>
      </div>

      {/* Quick Action Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <Link to="/scan">
          <Button
            variant="primary"
            size="md"
            leftIcon={<Search className="w-4 h-4" />}
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            SCAN NEW URL
          </Button>
        </Link>

        <Link to="/profile">
          <Button variant="secondary" size="md" leftIcon={<UserIcon className="w-4 h-4" />}>
            PROFILE
          </Button>
        </Link>

        <Button
          variant="outline"
          size="md"
          onClick={onLogout}
          leftIcon={<LogOut className="w-4 h-4 text-[#F87171]" />}
          title="Sign out of active session"
        >
          SIGN OUT
        </Button>
      </div>
    </div>
  );
};

export default WelcomeHeader;

