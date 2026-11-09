import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Shield, User as UserIcon, LogOut } from 'lucide-react';
import { Container } from '../common/Container';
import { useAuth } from '../../context/AuthContext';
import { publicCmsService } from '../../services/publicCmsService';

export const Navigation: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showContributors, setShowContributors] = useState(true);
  const [announcement, setAnnouncement] = useState<{
    enabled: boolean;
    message?: string;
    type?: string;
    link?: string;
  } | null>(null);

  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();

  useEffect(() => {
    publicCmsService
      .getContributorsPageConfig()
      .then((cfg) => {
        setShowContributors(Boolean(cfg.show_in_navigation && cfg.is_published));
      })
      .catch(() => {});

    publicCmsService
      .getPublicSettings()
      .then((s) => {
        if (s.announcement_enabled && s.announcement_message) {
          setAnnouncement({
            enabled: true,
            message: s.announcement_message,
            type: s.announcement_type,
            link: s.announcement_link,
          });
        }
      })
      .catch(() => {});
  }, []);

  const guestNavLinks = [
    { label: 'PRODUCT', href: '/scan' },
    { label: 'HOW IT WORKS', href: '/#how-it-works' },
    { label: 'SECURITY', href: '/#capabilities' },
    { label: 'COMMUNITY', href: '/community' },
    ...(showContributors ? [{ label: 'CONTRIBUTORS', href: '/contributors' }] : []),
  ];

  const authNavLinks = [
    { label: 'SCANNER', href: '/scan' },
    { label: 'DASHBOARD', href: '/dashboard' },
    { label: 'HISTORY', href: '/history' },
    { label: 'COMMUNITY', href: '/community' },
    ...(showContributors ? [{ label: 'CONTRIBUTORS', href: '/contributors' }] : []),
  ];

  const activeLinks = isAuthenticated ? authNavLinks : guestNavLinks;

  const handleScrollTo = (href: string) => {
    setMobileMenuOpen(false);
    if (href.startsWith('/#')) {
      const id = href.replace('/#', '');
      if (location.pathname === '/') {
        const element = document.getElementById(id);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' });
          return;
        }
      }
    }
  };

  const displayName = user?.full_name || user?.email?.split('@')[0] || 'Analyst';

  return (
    <header className="sticky top-0 z-50 w-full bg-[#080808]/90 backdrop-blur-md border-b border-[#292929]">
      {announcement?.enabled && announcement.message && (
        <div
          className={`py-1.5 px-4 text-center text-xs font-mono border-b ${
            announcement.type === 'critical'
              ? 'bg-rose-950/80 border-rose-800 text-rose-200'
              : announcement.type === 'warning'
              ? 'bg-amber-950/80 border-amber-800 text-amber-200'
              : 'bg-cyan-950/80 border-cyan-800 text-cyan-200'
          }`}
        >
          <span>{announcement.message}</span>
          {announcement.link && (
            <a href={announcement.link} className="ml-2 font-bold underline hover:opacity-80">
              LEARN MORE &rarr;
            </a>
          )}
        </div>
      )}
      <Container size="xl">
        <div className="flex h-16 items-center justify-between">
          {/* Brand Mark & Wordmark */}
          <Link to="/" className="flex items-center space-x-3 group select-none">
            <div className="relative w-8 h-8 bg-[#141414] border border-[#292929] flex items-center justify-center group-hover:border-[#F5F5F5] transition-colors">
              <Shield className="w-4 h-4 text-[#F5F5F5]" />
              <span className="absolute top-0 right-0 w-1 h-1 bg-[#F5F5F5]" />
              <span className="absolute bottom-0 left-0 w-1 h-1 bg-[#F5F5F5]" />
            </div>
            <div className="flex flex-col">
              <span className="font-mono text-sm font-bold tracking-widest text-[#F5F5F5]">
                TRUSTGUARD<span className="text-[#666666]">.AI</span>
              </span>
              <span className="text-[10px] font-mono text-[#666666] tracking-wider">
                DIGITAL TRUST ENGINE
              </span>
            </div>
          </Link>

          {/* Centre Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 font-mono text-xs">
            {activeLinks.map((link) => {
              const isHash = link.href.startsWith('/#');
              if (isHash) {
                return (
                  <a
                    key={link.label}
                    href={link.href}
                    onClick={() => handleScrollTo(link.href)}
                    className="px-3.5 py-1.5 text-[#A1A1A1] hover:text-[#F5F5F5] hover:bg-[#141414] tracking-wider transition-colors duration-150"
                  >
                    {link.label}
                  </a>
                );
              }
              return (
                <Link
                  key={link.label}
                  to={link.href}
                  className={`px-3.5 py-1.5 tracking-wider transition-colors duration-150 ${
                    location.pathname === link.href
                      ? 'text-[#F5F5F5] bg-[#141414] border border-[#383838]'
                      : 'text-[#A1A1A1] hover:text-[#F5F5F5] hover:bg-[#141414]'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Right Action Controls */}
          <div className="hidden md:flex items-center space-x-3 font-mono text-xs">
            {isAuthenticated ? (
              <div className="flex items-center space-x-2">
                <Link
                  to="/profile"
                  className={`flex items-center space-x-2 px-3 py-1.5 border transition-colors ${
                    location.pathname === '/profile'
                      ? 'bg-[#181818] border-[#444444] text-[#F5F5F5]'
                      : 'bg-[#101010] border-[#292929] hover:border-[#383838] text-[#A1A1A1] hover:text-[#F5F5F5]'
                  }`}
                >
                  <UserIcon className="w-3.5 h-3.5 text-[#A1A1A1]" />
                  <span className="max-w-[120px] truncate uppercase font-semibold">{displayName}</span>
                </Link>
                <button
                  onClick={() => logout()}
                  className="p-1.5 text-[#A1A1A1] hover:text-[#F87171] hover:bg-[#141414] border border-transparent hover:border-[#292929] transition-colors"
                  title="Sign out"
                  aria-label="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-3 py-1.5 text-[#A1A1A1] hover:text-[#F5F5F5] tracking-wider transition-colors"
                >
                  SIGN IN
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-1.5 bg-[#F5F5F5] text-[#080808] hover:bg-[#FFFFFF] font-semibold tracking-wider transition-colors border border-[#F5F5F5]"
                >
                  GET STARTED
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <div className="flex md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-[#A1A1A1] hover:text-[#F5F5F5] bg-[#101010] border border-[#292929]"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </Container>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#292929] bg-[#080808] px-4 pt-2 pb-6 space-y-4">
          <nav className="flex flex-col space-y-1 font-mono text-xs">
            {activeLinks.map((link) => {
              const isHash = link.href.startsWith('/#');
              if (isHash) {
                return (
                  <a
                    key={link.label}
                    href={link.href}
                    onClick={() => handleScrollTo(link.href)}
                    className="px-3 py-2 text-[#A1A1A1] hover:text-[#F5F5F5] tracking-wider"
                  >
                    {link.label}
                  </a>
                );
              }
              return (
                <Link
                  key={link.label}
                  to={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`px-3 py-2 tracking-wider ${
                    location.pathname === link.href
                      ? 'text-[#F5F5F5] bg-[#141414] border border-[#383838]'
                      : 'text-[#A1A1A1] hover:text-[#F5F5F5]'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
          <div className="pt-3 border-t border-[#292929] flex flex-col space-y-2 font-mono text-xs">
            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full flex items-center justify-center space-x-2 py-2 text-[#F5F5F5] bg-[#101010] border border-[#292929] tracking-wider"
                >
                  <UserIcon className="w-3.5 h-3.5" />
                  <span>PROFILE ({displayName.toUpperCase()})</span>
                </Link>
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center justify-center space-x-2 py-2 text-[#F87171] border border-[#292929] tracking-wider hover:bg-[#141414]"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>SIGN OUT</span>
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2 text-[#A1A1A1] border border-[#292929] tracking-wider"
                >
                  SIGN IN
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2 bg-[#F5F5F5] text-[#080808] font-semibold tracking-wider"
                >
                  GET STARTED
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
};

export default Navigation;
