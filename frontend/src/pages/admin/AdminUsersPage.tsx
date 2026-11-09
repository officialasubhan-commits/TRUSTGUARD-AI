import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Edit3,
  Eye,
  Mail,
  RefreshCw,
  Search,
  Trash2,
  UserCheck,
  UserX,
  Users,
  X,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { PixelSpinner } from '../../components/common/PixelSpinner';
import { adminService } from '../../services/adminService';
import { AdminUserDetail, AdminUserListItem } from '../../types/admin';

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<AdminUserListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'suspended'>('all');
  const [isLoading, setIsLoading] = useState(true);

  // Detail Modal State
  const [selectedUser, setSelectedUser] = useState<AdminUserDetail | null>(null);

  // Action Confirmation Modal State
  const [actionTarget, setActionTarget] = useState<{
    user: AdminUserListItem;
    type: 'suspend' | 'restore';
  } | null>(null);
  const [actionReason, setActionReason] = useState('');
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Edit Profile / Role Modal State
  const [editProfileTarget, setEditProfileTarget] = useState<{
    user: AdminUserListItem;
    fullName: string;
    role: string;
  } | null>(null);

  // Edit Email Modal State
  const [emailChangeTarget, setEmailChangeTarget] = useState<{
    user: AdminUserListItem;
    newEmail: string;
    reason: string;
  } | null>(null);

  // Delete User Modal State
  const [deleteTarget, setDeleteTarget] = useState<{
    user: AdminUserListItem;
    reason: string;
  } | null>(null);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const activeParam =
        statusFilter === 'all' ? undefined : statusFilter === 'active';
      const res = await adminService.getUsers(page, pageSize, search, activeParam);
      setUsers(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed fetching users:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadUsers();
  };

  const openUserDetail = async (userId: string) => {
    try {
      const detail = await adminService.getUserDetail(userId);
      setSelectedUser(detail);
    } catch (err) {
      console.error('Failed fetching user detail:', err);
    }
  };

  const handleExecuteAction = async () => {
    if (!actionTarget) return;
    if (!actionReason.trim()) {
      setActionError('A mandatory administrative rationale is required.');
      return;
    }

    setIsSubmittingAction(true);
    setActionError(null);

    try {
      if (actionTarget.type === 'suspend') {
        await adminService.suspendUser(actionTarget.user.id, actionReason.trim());
      } else {
        await adminService.restoreUser(actionTarget.user.id, actionReason.trim());
      }

      setActionTarget(null);
      setActionReason('');
      loadUsers();
      if (selectedUser?.id === actionTarget.user.id) {
        openUserDetail(actionTarget.user.id);
      }
    } catch (err: any) {
      setActionError(err.response?.data?.message || 'Action failed.');
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!editProfileTarget) return;
    setIsSubmittingAction(true);
    setActionError(null);
    try {
      await adminService.updateUser(editProfileTarget.user.id, {
        full_name: editProfileTarget.fullName.trim(),
        role: editProfileTarget.role,
      });
      setEditProfileTarget(null);
      loadUsers();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || err.response?.data?.message || 'Failed updating user.');
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const handleSaveEmail = async () => {
    if (!emailChangeTarget) return;
    if (!emailChangeTarget.newEmail.includes('@')) {
      setActionError('Valid email address required.');
      return;
    }
    setIsSubmittingAction(true);
    setActionError(null);
    try {
      await adminService.updateUserEmail(
        emailChangeTarget.user.id,
        emailChangeTarget.newEmail.trim(),
        emailChangeTarget.reason.trim() || undefined
      );
      setEmailChangeTarget(null);
      loadUsers();
    } catch (err: any) {
      setActionError(err.response?.data?.detail || err.response?.data?.message || 'Failed changing email.');
    } finally {
      setIsSubmittingAction(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!deleteTarget) return;
    setIsSubmittingAction(true);
    setActionError(null);
    try {
      await adminService.deleteUser(deleteTarget.user.id, deleteTarget.reason.trim() || undefined);
      setDeleteTarget(null);
      loadUsers();
      if (selectedUser?.id === deleteTarget.user.id) {
        setSelectedUser(null);
      }
    } catch (err: any) {
      setActionError(err.response?.data?.detail || err.response?.data?.message || 'Failed deleting user.');
    } finally {
      setIsSubmittingAction(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#1E1E1E]">
        <div>
          <h1 className="text-xl sm:text-2xl font-light tracking-tight text-white flex items-center space-x-2">
            <span>User Management & Authorization</span>
          </h1>
          <p className="text-xs font-mono text-[#888888] mt-1">
            VIEW ACCOUNT IDENTITIES, MANAGE SUSPENSIONS & INSPECT SCAN AUDIT TRAILS
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-[#888888]">
            TOTAL: <strong className="text-white">{total}</strong>
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={loadUsers}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            REFRESH
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <Card pixelFrame className="p-4 bg-[#0E0E0E] border-[#222222]">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[#555555] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by user email or ID..."
                className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded pl-9 pr-3 py-2 text-xs text-white placeholder-[#555555] font-mono focus:outline-none transition-colors"
              />
            </div>
            <Button type="submit" variant="outline" size="sm" className="shrink-0 font-mono text-xs">
              SEARCH
            </Button>
          </form>

          {/* Status Segmented Buttons */}
          <div className="flex items-center space-x-1 bg-[#141414] border border-[#262626] rounded p-0.5 text-xs font-mono">
            {(['all', 'active', 'suspended'] as const).map((s) => (
              <button
                key={s}
                onClick={() => {
                  setStatusFilter(s);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded transition-colors uppercase ${
                  statusFilter === s
                    ? 'bg-white text-black font-semibold'
                    : 'text-[#888888] hover:text-white'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Users Data Table */}
      <Card pixelFrame className="p-0 bg-[#0E0E0E] border-[#222222] overflow-hidden">
        {isLoading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <PixelSpinner size={32} />
            <p className="text-xs font-mono text-[#888888]">Loading user records...</p>
          </div>
        ) : users.length === 0 ? (
          <div className="py-16 text-center space-y-2">
            <Users className="w-8 h-8 text-[#444444] mx-auto" />
            <p className="text-xs font-mono text-[#777777]">NO USER ACCOUNTS MATCH CRITERIA.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#121212] border-b border-[#222222] text-[#888888] uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">User Email / ID</th>
                  <th className="py-3 px-4">Full Name</th>
                  <th className="py-3 px-4">Scans</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Registered</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#181818]">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-[#121212] transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-medium text-white truncate max-w-xs">{u.email}</div>
                      <div className="text-[10px] text-[#555555] font-mono truncate">{u.id}</div>
                    </td>
                    <td className="py-3 px-4 text-[#CCCCCC]">
                      {u.full_name || <span className="text-[#555555]">—</span>}
                    </td>
                    <td className="py-3 px-4 font-mono text-white">{u.scan_count}</td>
                    <td className="py-3 px-4">
                      {u.is_active ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/40 text-emerald-400 border border-emerald-800/60">
                          ACTIVE
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-950/40 text-rose-400 border border-rose-800/60">
                          SUSPENDED
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-[#888888]">
                      {new Date(u.created_at).toLocaleDateString([], {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="py-3 px-4 text-right space-x-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openUserDetail(u.id)}
                        className="text-[11px] font-mono py-1 px-1.5"
                        title="View Full Profile & History"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setEditProfileTarget({
                            user: u,
                            fullName: u.full_name || '',
                            role: u.role || 'user',
                          })
                        }
                        className="text-[11px] font-mono py-1 px-1.5 text-blue-400 hover:text-blue-300"
                        title="Edit Name & Role"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setEmailChangeTarget({
                            user: u,
                            newEmail: u.email,
                            reason: '',
                          })
                        }
                        className="text-[11px] font-mono py-1 px-1.5 text-amber-400 hover:text-amber-300"
                        title="Change Registered Email"
                      >
                        <Mail className="w-3.5 h-3.5" />
                      </Button>

                      {u.is_active ? (
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => setActionTarget({ user: u, type: 'suspend' })}
                          className="text-[11px] font-mono py-1 px-1.5"
                          title="Suspend User Access"
                        >
                          <UserX className="w-3.5 h-3.5" />
                        </Button>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setActionTarget({ user: u, type: 'restore' })}
                          className="text-[11px] font-mono py-1 px-1.5 text-emerald-400 hover:text-emerald-300"
                          title="Restore User Access"
                        >
                          <UserCheck className="w-3.5 h-3.5" />
                        </Button>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          setDeleteTarget({
                            user: u,
                            reason: '',
                          })
                        }
                        className="text-[11px] font-mono py-1 px-1.5 text-rose-500 hover:text-rose-400 hover:bg-rose-950/20"
                        title="Delete User Account"
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

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-[#202020] flex items-center justify-between text-xs font-mono text-[#888888]">
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* ------------------------------------------------------------- */}
      {/* User Detail Modal                                             */}
      {/* ------------------------------------------------------------- */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <Card pixelFrame className="max-w-2xl w-full p-6 bg-[#0E0E0E] border-[#262626] space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-[#222222] pb-4">
              <div>
                <h2 className="text-base font-mono font-semibold text-white">USER PROFILE INSPECTOR</h2>
                <p className="text-xs font-mono text-[#777777]">{selectedUser.id}</p>
              </div>
              <button
                onClick={() => setSelectedUser(null)}
                className="p-1 rounded text-[#888888] hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Account attributes */}
            <div className="grid grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3 bg-[#121212] border border-[#222222] rounded space-y-1">
                <span className="text-[#777777]">EMAIL ADDRESS:</span>
                <p className="text-white font-medium">{selectedUser.email}</p>
              </div>
              <div className="p-3 bg-[#121212] border border-[#222222] rounded space-y-1">
                <span className="text-[#777777]">ACCOUNT STATUS:</span>
                <p className={selectedUser.is_active ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
                  {selectedUser.is_active ? 'ACTIVE' : 'SUSPENDED'}
                </p>
              </div>
              <div className="p-3 bg-[#121212] border border-[#222222] rounded space-y-1">
                <span className="text-[#777777]">LIFETIME SCANS:</span>
                <p className="text-white font-medium">{selectedUser.scan_count}</p>
              </div>
              <div className="p-3 bg-[#121212] border border-[#222222] rounded space-y-1">
                <span className="text-[#777777]">REGISTERED SINCE:</span>
                <p className="text-white font-medium">{new Date(selectedUser.created_at).toLocaleString()}</p>
              </div>
            </div>

            {/* Recent Scans Table */}
            <div className="space-y-2">
              <h3 className="text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                Recent Scan Activity ({selectedUser.recent_scans.length})
              </h3>
              {selectedUser.recent_scans.length === 0 ? (
                <p className="text-xs font-mono text-[#555555] p-4 bg-[#121212] border border-[#222222] rounded text-center">
                  NO SCAN ACTIVITY RECORDED FOR THIS USER.
                </p>
              ) : (
                <div className="border border-[#222222] rounded overflow-hidden">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-[#141414] text-[#777777] border-b border-[#222222]">
                      <tr>
                        <th className="py-2 px-3">Target URL</th>
                        <th className="py-2 px-3">Score</th>
                        <th className="py-2 px-3">Risk</th>
                        <th className="py-2 px-3 text-right">Date</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1C1C1C]">
                      {selectedUser.recent_scans.map((s) => (
                        <tr key={s.id}>
                          <td className="py-2 px-3 text-white truncate max-w-xs">{s.submitted_url}</td>
                          <td className="py-2 px-3 font-semibold text-white">{s.trust_score ?? '—'}</td>
                          <td className="py-2 px-3 text-[10px] text-[#A1A1A1]">{s.risk_level ?? '—'}</td>
                          <td className="py-2 px-3 text-right text-[#666666] text-[10px]">
                            {new Date(s.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="outline" size="sm" onClick={() => setSelectedUser(null)}>
                CLOSE
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Action Confirmation Modal (Suspend / Restore)                 */}
      {/* ------------------------------------------------------------- */}
      {actionTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <Card pixelFrame className="max-w-md w-full p-6 bg-[#0E0E0E] border-[#2A2A2A] space-y-4">
            <div className="flex items-start space-x-3 text-rose-400">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-mono font-semibold uppercase text-white">
                  Confirm Account {actionTarget.type}
                </h3>
                <p className="text-xs font-mono text-[#888888] mt-1">
                  Target user: <span className="text-white">{actionTarget.user.email}</span>
                </p>
              </div>
            </div>

            {actionError && (
              <p className="text-xs font-mono text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-900/50">
                {actionError}
              </p>
            )}

            <div className="space-y-1.5">
              <label className="block text-xs font-mono text-[#A1A1A1] uppercase tracking-wider">
                Mandatory Administrative Reason
              </label>
              <textarea
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
                placeholder="Document the security rationale or compliance justification..."
                rows={3}
                className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2.5 text-xs text-white placeholder-[#555555] font-mono focus:outline-none transition-colors"
                required
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setActionTarget(null);
                  setActionReason('');
                  setActionError(null);
                }}
                disabled={isSubmittingAction}
              >
                CANCEL
              </Button>
              <Button
                variant={actionTarget.type === 'suspend' ? 'danger' : 'primary'}
                size="sm"
                onClick={handleExecuteAction}
                isLoading={isSubmittingAction}
                className="font-mono text-xs uppercase"
              >
                CONFIRM {actionTarget.type}
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Edit Profile & Role Modal                                     */}
      {/* ------------------------------------------------------------- */}
      {editProfileTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <Card pixelFrame className="max-w-md w-full p-6 bg-[#0E0E0E] border-[#2A2A2A] space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-mono font-semibold uppercase text-white">
                  Edit User Profile & Role
                </h3>
                <p className="text-xs font-mono text-[#888888] mt-1">
                  Target: <span className="text-white">{editProfileTarget.user.email}</span>
                </p>
              </div>
              <button
                onClick={() => {
                  setEditProfileTarget(null);
                  setActionError(null);
                }}
                className="text-[#666666] hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {actionError && (
              <p className="text-xs font-mono text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-900/50">
                {actionError}
              </p>
            )}

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">Display Name</label>
                <input
                  type="text"
                  value={editProfileTarget.fullName}
                  onChange={(e) =>
                    setEditProfileTarget({ ...editProfileTarget, fullName: e.target.value })
                  }
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                  placeholder="e.g. John Doe"
                />
              </div>

              <div>
                <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">Account Role</label>
                <select
                  value={editProfileTarget.role}
                  onChange={(e) =>
                    setEditProfileTarget({ ...editProfileTarget, role: e.target.value })
                  }
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                >
                  <option value="user">Standard User (user)</option>
                  <option value="security_analyst">Security Analyst (security_analyst)</option>
                  <option value="moderator">Community Moderator (moderator)</option>
                  <option value="admin">Administrator (admin)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setEditProfileTarget(null);
                  setActionError(null);
                }}
              >
                CANCEL
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveProfile}
                isLoading={isSubmittingAction}
              >
                SAVE CHANGES
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Change Registered Email Modal                                 */}
      {/* ------------------------------------------------------------- */}
      {emailChangeTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <Card pixelFrame className="max-w-md w-full p-6 bg-[#0E0E0E] border-[#2A2A2A] space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-mono font-semibold uppercase text-white">
                  Update Account Email
                </h3>
                <p className="text-xs font-mono text-[#888888] mt-1">
                  Updates Supabase Auth identity and public profile.
                </p>
              </div>
              <button
                onClick={() => {
                  setEmailChangeTarget(null);
                  setActionError(null);
                }}
                className="text-[#666666] hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {actionError && (
              <p className="text-xs font-mono text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-900/50">
                {actionError}
              </p>
            )}

            <div className="space-y-3 font-mono text-xs">
              <div>
                <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">New Email Address</label>
                <input
                  type="email"
                  value={emailChangeTarget.newEmail}
                  onChange={(e) =>
                    setEmailChangeTarget({ ...emailChangeTarget, newEmail: e.target.value })
                  }
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                  placeholder="new-address@trustguard.ai"
                  required
                />
              </div>

              <div>
                <label className="block text-[#A1A1A1] uppercase tracking-wider mb-1">Reason for Change</label>
                <input
                  type="text"
                  value={emailChangeTarget.reason}
                  onChange={(e) =>
                    setEmailChangeTarget({ ...emailChangeTarget, reason: e.target.value })
                  }
                  className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                  placeholder="User ticket request or typo correction"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setEmailChangeTarget(null);
                  setActionError(null);
                }}
              >
                CANCEL
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveEmail}
                isLoading={isSubmittingAction}
              >
                UPDATE EMAIL
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* Delete User Account Modal                                     */}
      {/* ------------------------------------------------------------- */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <Card pixelFrame className="max-w-md w-full p-6 bg-[#0E0E0E] border-[#2A2A2A] space-y-4">
            <div className="flex items-start space-x-3 text-rose-500">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <h3 className="text-sm font-mono font-semibold uppercase text-white">
                  Permanently Delete User Account
                </h3>
                <p className="text-xs font-mono text-[#888888] mt-1">
                  Target: <span className="text-white font-bold">{deleteTarget.user.email}</span>
                </p>
                <p className="text-[11px] font-mono text-rose-400 mt-1">
                  Warning: This action will permanently remove authentication records and profile data.
                </p>
              </div>
            </div>

            {actionError && (
              <p className="text-xs font-mono text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-900/50">
                {actionError}
              </p>
            )}

            <div className="space-y-1.5 font-mono text-xs">
              <label className="block text-[#A1A1A1] uppercase tracking-wider">Reason for Deletion</label>
              <input
                type="text"
                value={deleteTarget.reason}
                onChange={(e) => setDeleteTarget({ ...deleteTarget, reason: e.target.value })}
                className="w-full bg-[#141414] border border-[#282828] focus:border-white rounded p-2 text-white"
                placeholder="GDPR erasure request, compliance, or fraud removal"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setDeleteTarget(null);
                  setActionError(null);
                }}
              >
                CANCEL
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleDeleteUser}
                isLoading={isSubmittingAction}
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
