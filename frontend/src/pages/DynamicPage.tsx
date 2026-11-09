import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ChevronRight, FileText, Home } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { PixelSpinner } from '../components/common/PixelSpinner';
import { publicCmsService } from '../services/publicCmsService';
import { WebsitePage } from '../types/admin';

// Safe markdown renderer without raw HTML injection
const renderSafeMarkdown = (content: string) => {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBuffer: string[] = [];

  lines.forEach((line, idx) => {
    // Code blocks
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre
            key={`code-${idx}`}
            className="p-4 bg-[#141414] border border-[#262626] rounded text-emerald-400 font-mono text-xs overflow-x-auto my-3"
          >
            <code>{codeBuffer.join('\n')}</code>
          </pre>
        );
        codeBuffer = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      return;
    }

    // Headers
    if (line.startsWith('# ')) {
      elements.push(
        <h1 key={`h1-${idx}`} className="text-2xl sm:text-3xl font-light text-white font-sans mt-6 mb-3">
          {line.replace('# ', '')}
        </h1>
      );
    } else if (line.startsWith('## ')) {
      elements.push(
        <h2 key={`h2-${idx}`} className="text-xl font-normal text-white font-sans mt-5 mb-2 pb-1 border-b border-[#222222]">
          {line.replace('## ', '')}
        </h2>
      );
    } else if (line.startsWith('### ')) {
      elements.push(
        <h3 key={`h3-${idx}`} className="text-base font-medium text-cyan-400 font-sans mt-4 mb-2">
          {line.replace('### ', '')}
        </h3>
      );
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      elements.push(
        <li key={`li-${idx}`} className="text-sm font-sans text-[#CCCCCC] ml-6 list-disc mb-1 leading-relaxed">
          {line.replace(/^[-*]\s+/, '')}
        </li>
      );
    } else if (/^\d+\.\s+/.test(line)) {
      elements.push(
        <li key={`ol-${idx}`} className="text-sm font-sans text-[#CCCCCC] ml-6 list-decimal mb-1 leading-relaxed">
          {line.replace(/^\d+\.\s+/, '')}
        </li>
      );
    } else if (line.trim().length === 0) {
      elements.push(<div key={`sp-${idx}`} className="h-2" />);
    } else {
      elements.push(
        <p key={`p-${idx}`} className="text-sm font-sans text-[#CCCCCC] leading-relaxed mb-3">
          {line}
        </p>
      );
    }
  });

  return elements;
};

export const DynamicPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [page, setPage] = useState<WebsitePage | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPage = async () => {
      if (!slug) return;
      setIsLoading(true);
      setError(null);
      try {
        const data = await publicCmsService.getPageBySlug(slug);
        setPage(data);
      } catch (err: any) {
        console.error('Failed loading CMS page:', err);
        setError(err.response?.data?.detail || 'Page not found or is currently unavailable.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchPage();
  }, [slug]);

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
        <PixelSpinner size={36} />
        <p className="text-xs font-mono text-[#888888] tracking-widest uppercase">
          Loading Page Content...
        </p>
      </div>
    );
  }

  if (error || !page) {
    return (
      <div className="max-w-xl mx-auto py-24 px-4 text-center">
        <Card pixelFrame className="p-8 bg-[#0E0E0E] border-[#222222] space-y-4">
          <FileText className="w-10 h-10 text-[#666666] mx-auto" />
          <h1 className="text-xl font-mono font-semibold text-white uppercase tracking-wider">
            Page Unavailable
          </h1>
          <p className="text-xs font-mono text-[#888888] leading-relaxed">
            {error || "The requested page does not exist or has been unpublished by the administrators."}
          </p>
          <div className="pt-2">
            <Link to="/">
              <Button variant="outline" size="sm" leftIcon={<Home className="w-3.5 h-3.5" />}>
                RETURN TO HOMEPAGE
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
      {/* Breadcrumb */}
      <div className="flex items-center space-x-2 text-xs font-mono text-[#666666]">
        <Link to="/" className="hover:text-white transition-colors">
          HOME
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-[#AAAAAA] uppercase">{page.title}</span>
      </div>

      {/* Main Content Article */}
      <Card pixelFrame className="p-8 sm:p-12 bg-[#0E0E0E] border-[#222222]">
        <article className="space-y-4 text-white">
          {renderSafeMarkdown(page.content)}
        </article>

        {page.updated_at && (
          <div className="pt-8 mt-8 border-t border-[#1C1C1C] flex items-center justify-between text-[11px] font-mono text-[#666666]">
            <span>TrustGuard AI Official Content</span>
            <span>Last Updated: {new Date(page.updated_at).toLocaleDateString()}</span>
          </div>
        )}
      </Card>
    </div>
  );
};
