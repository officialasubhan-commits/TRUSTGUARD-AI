import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Award,
  Edit2,
  Plus,
  RefreshCw,
  Save,
  Sliders,
  Trash2,
  Users,
  X,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import {
  Contributor,
  ContributorCreate,
  ContributorsPageConfig,
} from '../../types/admin';

export const AdminContributorsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'contributors' | 'page_config'>('contributors');
  const [contributors, setContributors] = useState<Contributor[]>([]);
  const [pageConfig, setPageConfig] = useState<ContributorsPageConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Contributor Modal (Add / Edit)
  const [editingContributor, setEditingContributor] = useState<{
    id?: string;
    name: string;
    role: string;
    bio: string;
    avatar_url: string;
    github: string;
    linkedin: string;
    twitter: string;
    website: string;
    display_order: number;
    is_active: boolean;
  } | null>(null);

  // Delete confirmation
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [list, cfg] = await Promise.all([
        adminService.getContributors(true),
        adminService.getContributorsPageConfig(),
      ]);
      setContributors(list);
      setPageConfig(cfg);
    } catch (err) {
      console.error('Failed loading contributors:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openNewContributorModal = () => {
    setEditingContributor({
      name: '',
      role: '',
      bio: '',
      avatar_url: '',
      github: '',
      linkedin: '',
      twitter: '',
      website: '',
      display_order: contributors.length + 1,
      is_active: true,
    });
  };

  const openEditModal = (c: Contributor) => {
    setEditingContributor({
      id: c.id,
      name: c.name,
      role: c.role,
      bio: c.bio || '',
      avatar_url: c.avatar_url || '',
      github: c.social_links?.github || '',
      linkedin: c.social_links?.linkedin || '',
      twitter: c.social_links?.twitter || '',
      website: c.social_links?.website || '',
      display_order: c.display_order,
      is_active: c.is_active,
    });
  };

  const handleSaveContributor = async () => {
    if (!editingContributor) return;
    if (!editingContributor.name.trim() || !editingContributor.role.trim()) {
      setFeedbackMsg({ type: 'error', text: 'Name and Role are required.' });
      return;
    }

    setIsSaving(true);
    setFeedbackMsg(null);
    try {
      const payload: ContributorCreate = {
        name: editingContributor.name.trim(),
        role: editingContributor.role.trim(),
        bio: editingContributor.bio.trim() || undefined,
        avatar_url: editingContributor.avatar_url.trim() || undefined,
        social_links: {
          github: editingContributor.github.trim() || undefined,
          linkedin: editingContributor.linkedin.trim() || undefined,
          twitter: editingContributor.twitter.trim() || undefined,
          website: editingContributor.website.trim() || undefined,
        },
        display_order: editingContributor.display_order,
        is_active: editingContributor.is_active,
      };

      if (editingContributor.id) {
        await adminService.updateContributor(editingContributor.id, payload);
        setFeedbackMsg({ type: 'success', text: 'Contributor updated successfully.' });
      } else {
        await adminService.createContributor(payload);
        setFeedbackMsg({ type: 'success', text: 'New contributor added successfully.' });
      }

      setEditingContributor(null);
      await loadData();
    } catch (err: any) {
      setFeedbackMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed saving contributor.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    setIsSaving(true);
    try {
      await adminService.deleteContributor(id);
      setDeletingId(null);
      setFeedbackMsg({ type: 'success', text: 'Contributor deleted.' });
      await loadData();
    } catch (err: any) {
      setFeedbackMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed deleting contributor.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSavePageConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pageConfig) return;
    setIsSaving(true);
    setFeedbackMsg(null);
    try {
      const updated = await adminService.updateContributorsPageConfig(pageConfig);
      setPageConfig(updated);
      setFeedbackMsg({ type: 'success', text: 'Contributors page settings saved.' });
    } catch (err: any) {
      setFeedbackMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed updating page settings.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1E1E1E]">
        <div>
          <h1 className="text-xl sm:text-2xl font-light tracking-tight text-white flex items-center space-x-2">
            <span>Contributors & Team CMS</span>
          </h1>
          <p className="text-xs font-mono text-[#888888] mt-1">
            MANAGE PROJECT CONTRIBUTORS, DISPLAY PRIORITY & PUBLIC VISIBILITY
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            REFRESH
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={openNewContributorModal}
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            ADD CONTRIBUTOR
          </Button>
        </div>
      </div>

      {feedbackMsg && (
        <div
          className={`p-3 rounded text-xs font-mono border ${
            feedbackMsg.type === 'success'
              ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
              : 'bg-rose-950/40 text-rose-300 border-rose-800/60'
          }`}
        >
          {feedbackMsg.text}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center space-x-2 border-b border-[#222222]">
        <button
          onClick={() => setActiveTab('contributors')}
          className={`px-4 py-2 text-xs font-mono tracking-wider transition-colors border-b-2 -mb-px flex items-center space-x-2 ${
            activeTab === 'contributors'
              ? 'border-white text-white font-semibold'
              : 'border-transparent text-[#777777] hover:text-[#CCCCCC]'
          }`}
        >
          <Award className="w-3.5 h-3.5" />
          <span>CONTRIBUTORS LIST ({contributors.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('page_config')}
          className={`px-4 py-2 text-xs font-mono tracking-wider transition-colors border-b-2 -mb-px flex items-center space-x-2 ${
            activeTab === 'page_config'
              ? 'border-white text-white font-semibold'
              : 'border-transparent text-[#777777] hover:text-[#CCCCCC]'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>PAGE & NAVIGATION SETTINGS</span>
        </button>
      </div>

      {isLoading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <PixelSpinner size={32} />
          <p className="text-xs font-mono text-[#888888]">Loading contributors data...</p>
        </div>
      ) : activeTab === 'contributors' ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {contributors.map((c) => (
              <Card
                key={c.id}
                pixelFrame
                className={`p-5 bg-[#0E0E0E] border-[#222222] relative flex flex-col justify-between ${
                  !c.is_active ? 'opacity-60' : ''
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center space-x-3">
                      {c.avatar_url ? (
                        <img
                          src={c.avatar_url}
                          alt={c.name}
                          className="w-10 h-10 rounded bg-[#181818] border border-[#333333] object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded bg-[#1A1A1A] border border-[#333333] flex items-center justify-center font-mono text-white text-xs font-bold">
                          {c.name.slice(0, 2).toUpperCase()}
                        </div>
                      )}
                      <div>
                        <h3 className="text-sm font-mono font-semibold text-white leading-tight">
                          {c.name}
                        </h3>
                        <p className="text-[11px] font-mono text-cyan-400 mt-0.5">{c.role}</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono text-[#777777] bg-[#141414] px-1.5 py-0.5 border border-[#262626] rounded">
                      #{c.display_order}
                    </span>
                  </div>

                  {c.bio && (
                    <p className="text-xs font-mono text-[#AAAAAA] line-clamp-3 mb-4 leading-relaxed">
                      {c.bio}
                    </p>
                  )}

                  {/* Social badges */}
                  <div className="flex flex-wrap items-center gap-1.5 mb-4">
                    {c.social_links?.github && (
                      <span className="text-[10px] font-mono bg-[#161616] text-[#888888] px-2 py-0.5 rounded border border-[#282828]">
                        GitHub
                      </span>
                    )}
                    {c.social_links?.linkedin && (
                      <span className="text-[10px] font-mono bg-[#161616] text-[#888888] px-2 py-0.5 rounded border border-[#282828]">
                        LinkedIn
                      </span>
                    )}
                    {c.social_links?.twitter && (
                      <span className="text-[10px] font-mono bg-[#161616] text-[#888888] px-2 py-0.5 rounded border border-[#282828]">
                        Twitter
                      </span>
                    )}
                  </div>
                </div>

                <div className="pt-3 border-t border-[#1C1C1C] flex items-center justify-between">
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                      c.is_active
                        ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800/60'
                        : 'bg-zinc-900 text-[#888888] border border-[#333333]'
                    }`}
                  >
                    {c.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </span>

                  <div className="flex items-center space-x-1.5">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openEditModal(c)}
                      className="text-[11px] font-mono py-1 px-2"
                      title="Edit Contributor"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setDeletingId(c.id)}
                      className="text-[11px] font-mono py-1 px-2 text-rose-500 hover:text-rose-400 hover:bg-rose-950/20"
                      title="Delete Contributor"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {contributors.length === 0 && (
            <Card pixelFrame className="p-12 text-center bg-[#0E0E0E] border-[#222222]">
              <Users className="w-8 h-8 text-[#555555] mx-auto mb-2" />
              <p className="text-xs font-mono text-[#888888]">NO CONTRIBUTORS REGISTERED YET.</p>
              <Button
                variant="primary"
                size="sm"
                onClick={openNewContributorModal}
                className="mt-4"
              >
                ADD FIRST CONTRIBUTOR
              </Button>
            </Card>
          )}
        </div>
      ) : (
        /* Page Config Tab */
        <Card pixelFrame className="p-6 bg-[#0E0E0E] border-[#222222] max-w-2xl">
          <form onSubmit={handleSavePageConfig} className="space-y-5 font-mono text-xs">
            <div>
              <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                Contributors Page Title
              </label>
              <input
                type="text"
                value={pageConfig?.title || ''}
                onChange={(e) =>
                  setPageConfig(pageConfig ? { ...pageConfig, title: e.target.value } : null)
                }
                className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                required
              />
            </div>

            <div>
              <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                Page Subtitle & Hero Description
              </label>
              <textarea
                value={pageConfig?.subtitle || ''}
                onChange={(e) =>
                  setPageConfig(pageConfig ? { ...pageConfig, subtitle: e.target.value } : null)
                }
                rows={3}
                className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
              />
            </div>

            <div>
              <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                Optional Header Banner Image URL
              </label>
              <input
                type="url"
                value={pageConfig?.header_banner_url || ''}
                onChange={(e) =>
                  setPageConfig(
                    pageConfig ? { ...pageConfig, header_banner_url: e.target.value } : null
                  )
                }
                placeholder="https://..."
                className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
              />
            </div>

            <div className="pt-3 border-t border-[#1C1C1C] space-y-3">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={pageConfig?.is_published ?? true}
                  onChange={(e) =>
                    setPageConfig(
                      pageConfig ? { ...pageConfig, is_published: e.target.checked } : null
                    )
                  }
                  className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0 w-4 h-4"
                />
                <div>
                  <span className="text-white font-semibold">Publish Contributors Page (`/contributors`)</span>
                  <p className="text-[11px] text-[#777777]">
                    When unchecked, public visitors see an "Under Construction / Unavailable" message.
                  </p>
                </div>
              </label>

              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={pageConfig?.show_in_navigation ?? true}
                  onChange={(e) =>
                    setPageConfig(
                      pageConfig ? { ...pageConfig, show_in_navigation: e.target.checked } : null
                    )
                  }
                  className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0 w-4 h-4"
                />
                <div>
                  <span className="text-white font-semibold">Show Link in Main Navigation Bar</span>
                  <p className="text-[11px] text-[#777777]">
                    Dynamically renders "Contributors" in the website navbar header.
                  </p>
                </div>
              </label>
            </div>

            <div className="flex justify-end pt-3">
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={isSaving}
                leftIcon={<Save className="w-3.5 h-3.5" />}
              >
                SAVE PAGE SETTINGS
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Contributor Edit/Create Modal                                 */}
      {/* ------------------------------------------------------------- */}
      {editingContributor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <Card pixelFrame className="max-w-lg w-full p-6 bg-[#0E0E0E] border-[#2A2A2A] space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-mono font-semibold uppercase text-white">
                  {editingContributor.id ? 'Edit Contributor' : 'Add New Contributor'}
                </h3>
                <p className="text-xs font-mono text-[#888888] mt-1">
                  Configure contributor credentials and public links.
                </p>
              </div>
              <button
                onClick={() => setEditingContributor(null)}
                className="text-[#666666] hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs max-h-[70vh] overflow-y-auto pr-1">
              <div>
                <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">Full Name *</label>
                <input
                  type="text"
                  value={editingContributor.name}
                  onChange={(e) =>
                    setEditingContributor({ ...editingContributor, name: e.target.value })
                  }
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                  placeholder="e.g. Ratul Saha"
                  required
                />
              </div>

              <div>
                <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">Role / Title *</label>
                <input
                  type="text"
                  value={editingContributor.role}
                  onChange={(e) =>
                    setEditingContributor({ ...editingContributor, role: e.target.value })
                  }
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                  placeholder="e.g. Security Researcher & Architect"
                  required
                />
              </div>

              <div>
                <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">Bio / Expertise</label>
                <textarea
                  value={editingContributor.bio}
                  onChange={(e) =>
                    setEditingContributor({ ...editingContributor, bio: e.target.value })
                  }
                  rows={3}
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                  placeholder="Brief background or role summary..."
                />
              </div>

              <div>
                <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">Avatar Image URL</label>
                <input
                  type="url"
                  value={editingContributor.avatar_url}
                  onChange={(e) =>
                    setEditingContributor({ ...editingContributor, avatar_url: e.target.value })
                  }
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                  placeholder="https://..."
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">GitHub URL</label>
                  <input
                    type="url"
                    value={editingContributor.github}
                    onChange={(e) =>
                      setEditingContributor({ ...editingContributor, github: e.target.value })
                    }
                    className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white text-[11px]"
                    placeholder="https://github.com/..."
                  />
                </div>
                <div>
                  <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">LinkedIn URL</label>
                  <input
                    type="url"
                    value={editingContributor.linkedin}
                    onChange={(e) =>
                      setEditingContributor({ ...editingContributor, linkedin: e.target.value })
                    }
                    className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white text-[11px]"
                    placeholder="https://linkedin.com/in/..."
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">Display Priority Order</label>
                  <input
                    type="number"
                    value={editingContributor.display_order}
                    onChange={(e) =>
                      setEditingContributor({
                        ...editingContributor,
                        display_order: parseInt(e.target.value) || 0,
                      })
                    }
                    className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                  />
                </div>
                <div className="flex items-center pt-5">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editingContributor.is_active}
                      onChange={(e) =>
                        setEditingContributor({
                          ...editingContributor,
                          is_active: e.target.checked,
                        })
                      }
                      className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0 w-4 h-4"
                    />
                    <span className="text-white">Active Status</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-[#1C1C1C]">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditingContributor(null)}
              >
                CANCEL
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveContributor}
                isLoading={isSaving}
              >
                SAVE CONTRIBUTOR
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <Card pixelFrame className="max-w-md w-full p-6 bg-[#0E0E0E] border-[#2A2A2A] space-y-4">
            <div className="flex items-start space-x-3 text-rose-500">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-mono font-semibold uppercase text-white">
                  Delete Contributor
                </h3>
                <p className="text-xs font-mono text-[#888888] mt-1">
                  Are you sure you want to remove this contributor from TrustGuard AI?
                </p>
              </div>
            </div>
            <div className="flex justify-end space-x-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setDeletingId(null)}>
                CANCEL
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleDelete(deletingId)}
                isLoading={isSaving}
              >
                CONFIRM REMOVAL
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
