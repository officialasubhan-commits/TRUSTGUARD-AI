import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Award,
  ChevronRight,
  Github,
  Globe,
  Home,
  Linkedin,
  Shield,
  Twitter,
  Users,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { PixelSpinner } from '../components/common/PixelSpinner';
import { publicCmsService } from '../services/publicCmsService';
import { Contributor, ContributorsPageConfig } from '../types/admin';

export const ContributorsPage: React.FC = () => {
  const [contributors, setContributors] = useState<Contributor[]>([]);
  const [config, setConfig] = useState<ContributorsPageConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadContributors = async () => {
      try {
        const [list, cfg] = await Promise.all([
          publicCmsService.getContributors(),
          publicCmsService.getContributorsPageConfig(),
        ]);
        setContributors(list);
        setConfig(cfg);
      } catch (err) {
        console.error('Failed fetching public contributors:', err);
      } finally {
        setIsLoading(false);
      }
    };
    loadContributors();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <PixelSpinner size={36} />
        <p className="text-xs font-mono text-[#888888] tracking-widest uppercase">
          Loading Contributors & Team Registry...
        </p>
      </div>
    );
  }

  // Unpublished Page State
  if (config && !config.is_published) {
    return (
      <div className="max-w-2xl mx-auto py-20 px-4 text-center">
        <Card pixelFrame className="p-10 bg-[#0E0E0E] border-[#222222] space-y-4">
          <div className="w-12 h-12 rounded bg-[#181818] border border-[#333333] flex items-center justify-center mx-auto text-amber-400">
            <Award className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-mono font-semibold text-white uppercase tracking-wider">
            Contributors Page Under Preparation
          </h1>
          <p className="text-xs font-mono text-[#888888] max-w-md mx-auto leading-relaxed">
            The project contributors and researcher registry is currently undergoing editorial review and will be published shortly.
          </p>
          <div className="pt-4">
            <Link to="/">
              <Button variant="outline" size="sm" leftIcon={<Home className="w-3.5 h-3.5" />}>
                RETURN TO HOME
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      {/* Breadcrumb */}
      <div className="flex items-center space-x-2 text-xs font-mono text-[#666666]">
        <Link to="/" className="hover:text-white transition-colors">
          HOME
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-[#AAAAAA]">CONTRIBUTORS</span>
      </div>

      {/* Hero Header */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded bg-[#141414] border border-[#282828] text-xs font-mono text-cyan-400">
          <Shield className="w-3.5 h-3.5" />
          <span>CYBER DEFENSE INITIATIVE</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-light tracking-tight text-white font-sans">
          {config?.title || 'Project Contributors & Security Researchers'}
        </h1>
        <p className="text-sm font-mono text-[#888888] leading-relaxed">
          {config?.subtitle ||
            'The engineers, threat analysts, and security researchers dedicated to defending online users against deception, phishing campaigns, and digital fraud.'}
        </p>
      </div>

      {/* Optional Header Banner */}
      {config?.header_banner_url && (
        <div className="w-full h-48 sm:h-64 rounded overflow-hidden border border-[#222222]">
          <img
            src={config.header_banner_url}
            alt="Contributors Banner"
            className="w-full h-full object-cover"
          />
        </div>
      )}

      {/* Contributors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {contributors.map((c) => (
          <Card
            key={c.id}
            pixelFrame
            className="p-6 bg-[#0E0E0E] border-[#222222] hover:border-[#383838] transition-colors flex flex-col justify-between space-y-5"
          >
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                {c.avatar_url ? (
                  <img
                    src={c.avatar_url}
                    alt={c.name}
                    className="w-14 h-14 rounded bg-[#161616] border border-[#2E2E2E] object-cover shrink-0"
                  />
                ) : (
                  <div className="w-14 h-14 rounded bg-[#1A1A1A] border border-[#333333] flex items-center justify-center font-mono text-white text-base font-bold shrink-0">
                    {c.name.slice(0, 2).toUpperCase()}
                  </div>
                )}
                <div>
                  <h3 className="text-base font-mono font-semibold text-white tracking-wide leading-snug">
                    {c.name}
                  </h3>
                  <span className="inline-block mt-1 text-[11px] font-mono text-cyan-400 bg-cyan-950/30 border border-cyan-800/50 px-2 py-0.5 rounded">
                    {c.role}
                  </span>
                </div>
              </div>

              {c.bio && (
                <p className="text-xs font-mono text-[#AAAAAA] leading-relaxed line-clamp-4">
                  {c.bio}
                </p>
              )}
            </div>

            {/* Social Links Footer */}
            <div className="pt-4 border-t border-[#1C1C1C] flex items-center space-x-3 text-xs font-mono">
              {c.social_links?.github && (
                <a
                  href={c.social_links.github}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#888888] hover:text-white transition-colors flex items-center space-x-1"
                  title="GitHub Profile"
                >
                  <Github className="w-3.5 h-3.5" />
                  <span>GitHub</span>
                </a>
              )}
              {c.social_links?.linkedin && (
                <a
                  href={c.social_links.linkedin}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#888888] hover:text-white transition-colors flex items-center space-x-1"
                  title="LinkedIn Profile"
                >
                  <Linkedin className="w-3.5 h-3.5" />
                  <span>LinkedIn</span>
                </a>
              )}
              {c.social_links?.twitter && (
                <a
                  href={c.social_links.twitter}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#888888] hover:text-white transition-colors flex items-center space-x-1"
                  title="Twitter / X"
                >
                  <Twitter className="w-3.5 h-3.5" />
                  <span>X</span>
                </a>
              )}
              {c.social_links?.website && (
                <a
                  href={c.social_links.website}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[#888888] hover:text-white transition-colors flex items-center space-x-1"
                  title="Personal Website"
                >
                  <Globe className="w-3.5 h-3.5" />
                  <span>Web</span>
                </a>
              )}
            </div>
          </Card>
        ))}
      </div>

      {contributors.length === 0 && (
        <Card pixelFrame className="p-12 text-center bg-[#0E0E0E] border-[#222222]">
          <Users className="w-8 h-8 text-[#555555] mx-auto mb-2" />
          <p className="text-xs font-mono text-[#888888]">NO CONTRIBUTORS ARE CURRENTLY LISTED.</p>
        </Card>
      )}
    </div>
  );
};
