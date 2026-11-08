import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { AlertCircle, Lock, Shield, User } from 'lucide-react';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';

export const AdminLoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAdminAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/admin';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('Please provide both administrator username and password.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await login(username.trim(), password);
      navigate(from, { replace: true });
    } catch (err: any) {
      const msg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        'Authentication rejected. Verify administrator credentials.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080808] flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      {/* Background Subtle Ambience */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.02)_0,transparent_70%)] pointer-events-none" />

      <div className="w-full max-w-md space-y-6 relative z-10">
        {/* Header Branding */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded bg-[#141414] border border-[#2A2A2A] mb-2">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl sm:text-2xl font-light tracking-tight text-white">
            TrustGuard AI Administrator
          </h1>
          <p className="text-xs font-mono text-[#777777] uppercase tracking-wider">
            RESTRICTED ACCESS CONTROL CENTRE
          </p>
        </div>

        {/* Login Card */}
        <Card pixelFrame className="p-6 sm:p-8 bg-[#0E0E0E] border-[#222222] shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3.5 bg-rose-950/30 border border-rose-900/60 rounded flex items-start space-x-3 text-xs text-rose-300 font-mono">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {/* Username Input */}
            <div className="space-y-1.5">
              <label className="block text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                Admin Username
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-[#555555] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded px-9 py-2.5 text-sm text-white placeholder-[#555555] font-mono focus:outline-none transition-colors"
                  required
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="space-y-1.5">
              <label className="block text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#555555] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded px-9 py-2.5 text-sm text-white placeholder-[#555555] font-mono focus:outline-none transition-colors"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full font-mono tracking-wider font-semibold text-xs py-3 mt-2"
              isLoading={isLoading}
            >
              AUTHENTICATE ADMINISTRATOR
            </Button>
          </form>

          <div className="mt-6 pt-5 border-t border-[#1C1C1C] text-center">
            <p className="text-[11px] font-mono text-[#555555]">
              Protected by Argon2id cryptographic hashing & brute-force rate-limiting.
            </p>
          </div>
        </Card>

        {/* Public Return Link */}
        <div className="text-center">
          <a
            href="/"
            className="text-xs font-mono text-[#777777] hover:text-[#CCCCCC] transition-colors"
          >
            ← Return to TrustGuard AI Public Scanner
          </a>
        </div>
      </div>
    </div>
  );
};

