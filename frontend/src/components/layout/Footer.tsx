import React from 'react';
import { Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { Container } from '../common/Container';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-[#080808] border-t border-[#292929] pt-16 pb-12 text-xs font-mono">
      <Container size="xl">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-10 pb-12 border-b border-[#292929]">
          {/* Brand Column */}
          <div className="md:col-span-2 space-y-4">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-7 h-7 bg-[#141414] border border-[#292929] flex items-center justify-center">
                <Shield className="w-3.5 h-3.5 text-[#F5F5F5]" />
              </div>
              <span className="font-mono text-sm font-bold tracking-widest text-[#F5F5F5]">
                TRUSTGUARD<span className="text-[#666666]">.AI</span>
              </span>
            </Link>
            <p className="text-xs text-[#A1A1A1] font-sans max-w-sm leading-relaxed">
              Autonomous digital trust intelligence. Combining multi-vendor threat telemetry,
              machine-learning classification, SSL/TLS cryptographic verification, and lexical URL
              heuristics into transparent, explainable assessments.
            </p>
            <div className="flex items-center space-x-2 text-[11px] text-[#666666]">
              <span className="inline-block w-1.5 h-1.5 bg-[#4ADE80] rounded-full animate-pulse" />
              <span>CORE API ENGINE V1.0.0 OPERATIONAL</span>
            </div>
          </div>

          {/* Product Navigation */}
          <div className="space-y-3">
            <span className="text-[11px] text-[#666666] uppercase tracking-wider font-semibold">
              PRODUCT
            </span>
            <ul className="space-y-2 text-[#A1A1A1]">
              <li>
                <Link to="/scan" className="hover:text-[#F5F5F5] transition-colors">
                  URL Scanner
                </Link>
              </li>
              <li>
                <a href="/#capabilities" className="hover:text-[#F5F5F5] transition-colors">
                  Security Capabilities
                </a>
              </li>
              <li>
                <a href="/#how-it-works" className="hover:text-[#F5F5F5] transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <Link to="/history" className="hover:text-[#F5F5F5] transition-colors">
                  Scan History
                </Link>
              </li>
            </ul>
          </div>

          {/* Community & Intelligence */}
          <div className="space-y-3">
            <span className="text-[11px] text-[#666666] uppercase tracking-wider font-semibold">
              INTELLIGENCE
            </span>
            <ul className="space-y-2 text-[#A1A1A1]">
              <li>
                <Link to="/community" className="hover:text-[#F5F5F5] transition-colors">
                  Community Threat Feed
                </Link>
              </li>
              <li>
                <Link to="/dashboard" className="hover:text-[#F5F5F5] transition-colors">
                  Analytics Dashboard
                </Link>
              </li>
              <li>
                <Link to="/design-system" className="hover:text-[#F5F5F5] transition-colors">
                  Design System
                </Link>
              </li>
              <li>
                <Link to="/animations" className="hover:text-[#F5F5F5] transition-colors">
                  Animation Engine
                </Link>
              </li>
            </ul>
          </div>

          {/* Platform Governance & Access */}
          <div className="space-y-3">
            <span className="text-[11px] text-[#666666] uppercase tracking-wider font-semibold">
              COMPANY & LEGAL
            </span>
            <ul className="space-y-2 text-[#A1A1A1]">
              <li>
                <Link to="/contributors" className="hover:text-[#F5F5F5] transition-colors">
                  Contributors
                </Link>
              </li>
              <li>
                <Link to="/p/about" className="hover:text-[#F5F5F5] transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link to="/p/privacy" className="hover:text-[#F5F5F5] transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/p/terms" className="hover:text-[#F5F5F5] transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link to="/admin/login" className="hover:text-[#F5F5F5] text-[#777777] transition-colors">
                  Admin Console
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Security Disclaimer & Legal Notice */}
        <div className="pt-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-[#666666] text-[11px]">
          <p className="max-w-2xl font-sans leading-normal">
            <span className="font-mono text-[#A1A1A1] uppercase font-semibold">
              Security Disclaimer:{' '}
            </span>
            TrustGuard AI evaluates submitted URLs against probabilistic machine learning, public
            threat intelligence feeds, SSL/TLS configurations, and lexical heuristics. A clean score
            indicates no known threat indicators were detected at scan time; it does not constitute
            an absolute warranty against zero-day or runtime compromises.
          </p>

          <div className="shrink-0 font-mono">
            &copy; {new Date().getFullYear()} TRUSTGUARD AI. ALL RIGHTS RESERVED.
          </div>
        </div>
      </Container>
    </footer>
  );
};
