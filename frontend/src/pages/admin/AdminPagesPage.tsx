import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Check,
  Edit,
  ExternalLink,
  Eye,
  FileText,
  Plus,
  RefreshCw,
  Save,
  Trash2,
  X,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import { WebsitePage, WebsitePageCreate } from '../../types/admin';

export const AdminPagesPage: React.FC = () => {
  const [pages, setPages] = useState<WebsitePage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Editor Modal State
  const [editingPage, setEditingPage] = useState<{
    id?: string;
    title: string;
    slug: string;
    content: string;
    meta_description: string;
    is_published: boolean;
    show_in_navigation: boolean;
    nav_order: number;
    previewMode: boolean;
  } | null>(null);

  // Delete target
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadPages = async () => {
    setIsLoading(true);
    try {
      const data = await adminService.getPages(true);
      setPages(data);
    } catch (err) {
      console.error('Failed loading pages:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPages();
  }, []);

  const openNewPageModal = () => {
    setEditingPage({
      title: '',
      slug: '',
      content: '# New Page\n\nEnter markdown content here...',
      meta_description: '',
      is_published: true,
      show_in_navigation: false,
      nav_order: pages.length + 1,
      previewMode: false,
    });
  };

  const openEditModal = (p: WebsitePage) => {
    setEditingPage({
      id: p.id,
      title: p.title,
      slug: p.slug,
      content: p.content,
      meta_description: p.meta_description || '',
      is_published: p.is_published,
      show_in_navigation: p.show_in_navigation,
      nav_order: p.nav_order,
      previewMode: false,
    });
  };

  const generateSlug = (title: string) => {
    return title
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  };

  const handleTitleChange = (val: string) => {
    if (!editingPage) return;
    const shouldUpdateSlug = !editingPage.id && (!editingPage.slug || editingPage.slug === generateSlug(editingPage.title));
    setEditingPage({
      ...editingPage,
      title: val,
      slug: shouldUpdateSlug ? generateSlug(val) : editingPage.slug,
    });
  };

  const handleSavePage = async () => {
    if (!editingPage) return;
    if (!editingPage.title.trim() || !editingPage.slug.trim()) {
      setFeedbackMsg({ type: 'error', text: 'Page title and slug are required.' });
      return;
    }

    setIsSaving(true);
    setFeedbackMsg(null);
    try {
      const payload: WebsitePageCreate = {
        title: editingPage.title.trim(),
        slug: editingPage.slug.trim().toLowerCase().replace(/^\/|\/$/g, ''),
        content: editingPage.content,
        meta_description: editingPage.meta_description.trim() || undefined,
        is_published: editingPage.is_published,
        show_in_navigation: editingPage.show_in_navigation,
        nav_order: editingPage.nav_order,
      };

      if (editingPage.id) {
        await adminService.updatePage(editingPage.id, payload);
        setFeedbackMsg({ type: 'success', text: `Page '${payload.title}' updated.` });
      } else {
        await adminService.createPage(payload);
        setFeedbackMsg({ type: 'success', text: `New page '${payload.title}' published.` });
      }

      setEditingPage(null);
      await loadPages();
    } catch (err: any) {
      setFeedbackMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed saving page.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    setIsSaving(true);
    try {
      await adminService.deletePage(id);
      setDeletingId(null);
      setFeedbackMsg({ type: 'success', text: 'Page deleted successfully.' });
      await loadPages();
    } catch (err: any) {
      setFeedbackMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed deleting page.',
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
            <span>Dynamic CMS & Page Management</span>
          </h1>
          <p className="text-xs font-mono text-[#888888] mt-1">
            CREATE, EDIT, PUBLISH & MANAGE DYNAMIC WEBSITE CONTENT PAGES
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadPages}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            REFRESH
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={openNewPageModal}
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            CREATE NEW PAGE
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

      {/* Pages Data Table */}
      <Card pixelFrame className="p-0 bg-[#0E0E0E] border-[#222222] overflow-hidden">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <PixelSpinner size={32} />
            <p className="text-xs font-mono text-[#888888]">Loading pages...</p>
          </div>
        ) : pages.length === 0 ? (
          <div className="py-16 text-center space-y-3">
            <FileText className="w-8 h-8 text-[#555555] mx-auto" />
            <p className="text-xs font-mono text-[#777777]">NO DYNAMIC PAGES CREATED YET.</p>
            <Button variant="primary" size="sm" onClick={openNewPageModal}>
              CREATE FIRST PAGE
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#121212] border-b border-[#222222] text-[#888888] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Title & Slug</th>
                  <th className="py-3 px-4">URL Route</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">In Navbar</th>
                  <th className="py-3 px-4">Order</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#181818]">
                {pages.map((p) => (
                  <tr key={p.id} className="hover:bg-[#121212] transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-white">{p.title}</div>
                      <div className="text-[10px] text-[#666666] font-mono truncate max-w-xs">
                        {p.meta_description || 'No meta description provided'}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-cyan-400">
                      <a
                        href={`/p/${p.slug}`}
                        target="_blank"
                        rel="noreferrer"
                        className="hover:underline flex items-center space-x-1"
                      >
                        <span>/p/{p.slug}</span>
                        <ExternalLink className="w-3 h-3 text-[#666666]" />
                      </a>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold ${
                          p.is_published
                            ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800/60'
                            : 'bg-zinc-900 text-[#888888] border border-[#333333]'
                        }`}
                      >
                        {p.is_published ? 'PUBLISHED' : 'DRAFT'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[#CCCCCC]">
                      {p.show_in_navigation ? (
                        <span className="text-emerald-400 flex items-center space-x-1">
                          <Check className="w-3 h-3" />
                          <span>Yes</span>
                        </span>
                      ) : (
                        <span className="text-[#666666]">No</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-[#888888]">#{p.nav_order}</td>
                    <td className="py-3 px-4 text-right space-x-1.5">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEditModal(p)}
                        className="text-[11px] font-mono py-1 px-2"
                        title="Edit Page Content"
                      >
                        <Edit className="w-3.5 h-3.5" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setDeletingId(p.id)}
                        className="text-[11px] font-mono py-1 px-2 text-rose-500 hover:text-rose-400 hover:bg-rose-950/20"
                        title="Delete Page"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ------------------------------------------------------------- */}
      {/* Editor Modal                                                  */}
      {/* ------------------------------------------------------------- */}
      {editingPage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <Card pixelFrame className="max-w-4xl w-full p-6 bg-[#0E0E0E] border-[#2A2A2A] space-y-4 max-h-[90vh] flex flex-col">
            <div className="flex items-start justify-between border-b border-[#1C1C1C] pb-3 shrink-0">
              <div>
                <h3 className="text-sm font-mono font-semibold uppercase text-white">
                  {editingPage.id ? 'Edit Dynamic Page' : 'Create New CMS Page'}
                </h3>
                <p className="text-xs font-mono text-[#888888] mt-0.5">
                  URL Route: <span className="text-cyan-400">/p/{editingPage.slug || 'your-slug'}</span>
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setEditingPage({ ...editingPage, previewMode: !editingPage.previewMode })
                  }
                  leftIcon={<Eye className="w-3.5 h-3.5" />}
                >
                  {editingPage.previewMode ? 'EDIT MARKDOWN' : 'LIVE PREVIEW'}
                </Button>
                <button
                  onClick={() => setEditingPage(null)}
                  className="text-[#666666] hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="space-y-3 font-mono text-xs flex-1 overflow-y-auto pr-1">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">Page Title *</label>
                  <input
                    type="text"
                    value={editingPage.title}
                    onChange={(e) => handleTitleChange(e.target.value)}
                    placeholder="e.g. Terms of Service"
                    className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                    required
                  />
                </div>
                <div>
                  <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">URL Slug *</label>
                  <input
                    type="text"
                    value={editingPage.slug}
                    onChange={(e) => setEditingPage({ ...editingPage, slug: e.target.value })}
                    placeholder="e.g. terms"
                    className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white font-mono"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                  Meta Description (SEO & OpenGraph)
                </label>
                <input
                  type="text"
                  value={editingPage.meta_description}
                  onChange={(e) =>
                    setEditingPage({ ...editingPage, meta_description: e.target.value })
                  }
                  placeholder="Short description for search engines and social shares"
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                />
              </div>

              {/* Editor / Preview Area */}
              <div>
                <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">
                  Page Content (Markdown)
                </label>
                {editingPage.previewMode ? (
                  <div className="p-4 bg-[#141414] border border-[#282828] rounded min-h-[250px] max-h-[350px] overflow-y-auto text-white prose prose-invert prose-xs font-sans">
                    <div className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                      {editingPage.content}
                    </div>
                  </div>
                ) : (
                  <textarea
                    value={editingPage.content}
                    onChange={(e) => setEditingPage({ ...editingPage, content: e.target.value })}
                    rows={12}
                    className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-3 text-white font-mono text-xs leading-relaxed"
                    placeholder="# Page Header&#10;&#10;Write content in GitHub-flavored Markdown..."
                    required
                  />
                )}
              </div>

              {/* Toggles */}
              <div className="pt-2 border-t border-[#1C1C1C] grid grid-cols-1 sm:grid-cols-3 gap-3">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editingPage.is_published}
                    onChange={(e) =>
                      setEditingPage({ ...editingPage, is_published: e.target.checked })
                    }
                    className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0 w-4 h-4"
                  />
                  <span className="text-white font-semibold">Published Status</span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editingPage.show_in_navigation}
                    onChange={(e) =>
                      setEditingPage({ ...editingPage, show_in_navigation: e.target.checked })
                    }
                    className="rounded bg-[#1A1A1A] border-[#333333] text-white focus:ring-0 w-4 h-4"
                  />
                  <span className="text-white font-semibold">Show in Navigation</span>
                </label>

                <div className="flex items-center space-x-2">
                  <span className="text-[#888888]">Order:</span>
                  <input
                    type="number"
                    value={editingPage.nav_order}
                    onChange={(e) =>
                      setEditingPage({ ...editingPage, nav_order: parseInt(e.target.value) || 0 })
                    }
                    className="w-20 bg-[#141414] border border-[#282828] focus:border-white rounded p-1 text-white text-center font-mono"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-[#1C1C1C] shrink-0">
              <Button variant="outline" size="sm" onClick={() => setEditingPage(null)}>
                CANCEL
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSavePage}
                isLoading={isSaving}
                leftIcon={<Save className="w-3.5 h-3.5" />}
              >
                SAVE & PUBLISH
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
                  Delete Dynamic Page
                </h3>
                <p className="text-xs font-mono text-[#888888] mt-1">
                  Are you sure you want to delete this page? The public route will return 404 Not Found.
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
                CONFIRM DELETION
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
