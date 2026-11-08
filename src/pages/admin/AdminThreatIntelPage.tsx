import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Database,
  Flame,
  Globe,
  Radio,
  RefreshCw,
  Search,
  ShieldAlert,
  Zap,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import { AdminThreatIntelSummary } from '../../types/admin';

export const AdminThreatIntelPage: React.FC = () => {
  const [intel, setIntel] = useState<AdminThreatIntelSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const fetchThreatIntel = async () => {
    try {
      const data = await adminService.getThreatIntelSummary();
      setIntel(data);
    } catch (err) {
      console.error('Failed to load threat intel summary:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchThreatIntel();
  }, []);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchThreatIntel();
  };

  const filteredThreats = intel?.recent_threats.filter((item) => {
    const matchesSearch =
      item.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.threat_category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.source.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCat =
      selectedCategory === 'all' ||
      item.threat_category.toLowerCase() === selectedCategory.toLowerCase();
    return matchesSearch && matchesCat;
  }) || [];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#222222] pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono uppercase">
              Threat Intelligence
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium tracking-wide border bg-[#111111] text-[#a0a0a0] border-[#333333]">
              FEED V2.4
            </span>
          </div>
          <p className="text-sm text-[#737373] mt-1 font-mono">
            Automated reputation feeds, verified high-confidence IOCs & external scanner status
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="border-[#333333] hover:bg-[#1c1c1c] text-[#e5e5e5] font-mono text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh Intelligence
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="py-24 flex flex-col items-center justify-center space-y-4">
          <PixelSpinner />
          <p className="text-xs font-mono text-[#737373] tracking-widest uppercase">
            Aggregating Global IOC Feeds...
          </p>
        </div>
      ) : !intel ? (
        <Card className="bg-[#111111] border-[#222222] p-8 text-center">
          <AlertTriangle className="w-8 h-8 text-[#a0a0a0] mx-auto mb-3" />
          <p className="text-sm font-mono text-[#a0a0a0]">Failed to retrieve threat intelligence feeds.</p>
          <Button
            size="sm"
            onClick={fetchThreatIntel}
            className="mt-4 bg-white text-black font-mono text-xs"
          >
            Retry Connection
          </Button>
        </Card>
      ) : (
        <>
          {/* Key Intelligence Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-[#111111] border-[#222222] p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#737373] uppercase tracking-wider">
                  Verified Active Threats
                </span>
                <Flame className="w-4 h-4 text-[#ffffff]" />
              </div>
              <div className="text-3xl font-bold font-mono text-white mt-3">
                {intel.total_verified_threats.toLocaleString()}
              </div>
              <div className="text-[11px] font-mono text-[#525252] mt-1">
                Confirmed via multi-engine consensus
              </div>
            </Card>

            <Card className="bg-[#111111] border-[#222222] p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#737373] uppercase tracking-wider">
                  Community Confirmed
                </span>
                <ShieldAlert className="w-4 h-4 text-[#a0a0a0]" />
              </div>
              <div className="text-3xl font-bold font-mono text-white mt-3">
                {intel.source_breakdown['community_moderated'] || 0}
              </div>
              <div className="text-[11px] font-mono text-[#525252] mt-1">
                Moderator reviewed & accepted
              </div>
            </Card>

            <Card className="bg-[#111111] border-[#222222] p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#737373] uppercase tracking-wider">
                  Automated Scanner Hits
                </span>
                <Zap className="w-4 h-4 text-[#a0a0a0]" />
              </div>
              <div className="text-3xl font-bold font-mono text-white mt-3">
                {intel.source_breakdown['scanner_high_risk'] || 0}
              </div>
              <div className="text-[11px] font-mono text-[#525252] mt-1">
                Risk score &gt; 80 / 100
              </div>
            </Card>

            <Card className="bg-[#111111] border-[#222222] p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-[#737373] uppercase tracking-wider">
                  Live External Feeds
                </span>
                <Radio className="w-4 h-4 text-[#ffffff] animate-pulse" />
              </div>
              <div className="text-3xl font-bold font-mono text-white mt-3">
                {intel.external_providers.filter((p) => p.status === 'OPERATIONAL').length} /{' '}
                {intel.external_providers.length}
              </div>
              <div className="text-[11px] font-mono text-[#525252] mt-1">
                Threat providers synchronized
              </div>
            </Card>
          </div>

          {/* External Threat Provider Health Cards */}
          <div className="space-y-3">
            <h2 className="text-xs font-mono font-semibold text-[#a0a0a0] uppercase tracking-wider">
              Connected Threat Feeds & Intelligence Engines
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {intel.external_providers.map((provider) => (
                <Card
                  key={provider.name}
                  className="bg-[#111111] border-[#222222] p-5 hover:border-[#333333] transition-colors"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {provider.name.includes('VirusTotal') ? (
                        <Globe className="w-4 h-4 text-white" />
                      ) : provider.name.includes('ML') ? (
                        <Cpu className="w-4 h-4 text-white" />
                      ) : (
                        <Database className="w-4 h-4 text-white" />
                      )}
                      <span className="font-mono text-sm font-semibold text-white">
                        {provider.name}
                      </span>
                    </div>
                    <span
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium ${
                        provider.status === 'OPERATIONAL'
                          ? 'bg-[#1c2e1c] text-[#4ade80] border border-[#2e542e]'
                          : 'bg-[#2e1c1c] text-[#f87171] border border-[#542e2e]'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          provider.status === 'OPERATIONAL' ? 'bg-[#4ade80]' : 'bg-[#f87171]'
                        }`}
                      />
                      {provider.status}
                    </span>
                  </div>

                  <div className="text-xs text-[#737373] font-mono mb-4">
                    Type: <span className="text-[#e5e5e5]">{provider.type}</span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-mono pt-3 border-t border-[#1c1c1c]">
                    <span className="text-[#525252]">Response Latency</span>
                    <span className="text-[#a0a0a0]">{provider.latency_ms}ms</span>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Threat Category Distribution */}
          <Card className="bg-[#111111] border-[#222222] p-6">
            <h3 className="text-sm font-mono font-semibold text-white uppercase tracking-wider mb-4">
              Threat Category Prevalence
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {intel.top_threat_categories.map((cat) => (
                <div
                  key={cat.category}
                  className="p-3 bg-[#0c0c0c] border border-[#1f1f1f] rounded"
                >
                  <div className="text-xs font-mono text-[#a0a0a0] capitalize">
                    {cat.category}
                  </div>
                  <div className="text-xl font-bold font-mono text-white mt-1">
                    {cat.count}
                  </div>
                  <div className="text-[10px] font-mono text-[#525252] mt-0.5">
                    {cat.percentage}% of verified database
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* IOC Threat Stream Table */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <h2 className="text-sm font-mono font-semibold text-white uppercase tracking-wider">
                Active IOC Stream ({filteredThreats.length})
              </h2>

              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#737373]" />
                  <input
                    type="text"
                    placeholder="Search IOC domain or category..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 pr-3 py-1.5 bg-[#0e0e0e] border border-[#262626] rounded text-xs font-mono text-white placeholder-[#525252] focus:outline-none focus:border-[#404040] w-64"
                  />
                </div>

                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-2.5 py-1.5 bg-[#0e0e0e] border border-[#262626] rounded text-xs font-mono text-[#e5e5e5] focus:outline-none focus:border-[#404040]"
                >
                  <option value="all">All Categories</option>
                  <option value="phishing">Phishing</option>
                  <option value="malware">Malware</option>
                  <option value="scam">Scam / Fraud</option>
                  <option value="suspicious">Suspicious</option>
                </select>
              </div>
            </div>

            <Card className="bg-[#111111] border-[#222222] overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[#0a0a0a] border-b border-[#222222] text-[#737373] uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Domain / Target</th>
                      <th className="py-3 px-4">Threat Classification</th>
                      <th className="py-3 px-4">Severity</th>
                      <th className="py-3 px-4">Source Provider</th>
                      <th className="py-3 px-4">Verification</th>
                      <th className="py-3 px-4">First Observed</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1a1a1a]">
                    {filteredThreats.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-[#737373]">
                          No threat intelligence items matching the search query.
                        </td>
                      </tr>
                    ) : (
                      filteredThreats.map((item) => (
                        <tr key={item.id} className="hover:bg-[#141414] transition-colors">
                          <td className="py-3 px-4 font-semibold text-white flex items-center gap-2">
                            <ShieldAlert className="w-3.5 h-3.5 text-[#ef4444]" />
                            <span>{item.domain}</span>
                          </td>
                          <td className="py-3 px-4 text-[#a0a0a0] capitalize">
                            {item.threat_category}
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium ${
                                item.severity === 'CRITICAL' || item.severity === 'HIGH'
                                  ? 'bg-[#2e1515] text-[#f87171] border border-[#522323]'
                                  : 'bg-[#2b2515] text-[#fbbf24] border border-[#4a3e1e]'
                              }`}
                            >
                              {item.severity}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-[#737373]">
                            {item.source}
                          </td>
                          <td className="py-3 px-4">
                            <span className="inline-flex items-center gap-1 text-[#4ade80]">
                              <CheckCircle2 className="w-3 h-3" />
                              VERIFIED
                            </span>
                          </td>
                          <td className="py-3 px-4 text-[#525252]">
                            {new Date(item.first_seen).toLocaleDateString()}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
};
