'use client';

import React, { useEffect, useState } from 'react';
import { createUser, getSystemHealth, getUsers, updateUser, deleteUser } from '@/lib/api/system';
import { SystemHealth, UserInfo, UserPage } from '@/types/api';
import { DataTable, Column } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import { Pagination } from '@/components/ui/pagination';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { formatDate, formatReadableId } from '@/lib/formatting';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import {
  Shield,
  UserPlus,
  Server,
  Loader2,
  Trash2,
  Lock,
  UserCheck,
  CheckCircle2,
  Sparkles,
  ShieldCheck,
  Zap,
  Info
} from 'lucide-react';

export default function SettingsPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [usersData, setUsersData] = useState<UserPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [deletingUser, setDeletingUser] = useState<UserInfo | null>(null);

  // Provision form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('agent');
  const [submitLoading, setSubmitLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const h = await getSystemHealth();
      const u = await getUsers({ page, page_size: 15 });
      setHealth(h);
      setUsersData(u);
    } catch (err: any) {
      setError(err.message || 'Failed to load system settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitLoading(true);
    try {
      await createUser({ email, password, role });
      setShowAddUserModal(false);
      setEmail('');
      setPassword('');
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to create staff user.');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleRoleChange = async (user: UserInfo, newRole: string) => {
    try {
      await updateUser(user.id, { role: newRole });
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to update user role.');
    }
  };

  const handleToggleStatus = async (user: UserInfo) => {
    const nextStatus = user.status === 'active' ? 'suspended' : 'active';
    if (confirm(`Are you sure you want to change account status for ${user.email} to "${nextStatus.toUpperCase()}"?`)) {
      try {
        await updateUser(user.id, { status: nextStatus });
        await fetchData();
      } catch (err: any) {
        alert(err.message || 'Failed to update user status.');
      }
    }
  };

  const handleDeleteUser = async () => {
    if (!deletingUser) return;
    setSubmitLoading(true);
    try {
      await deleteUser(deletingUser.id);
      setDeletingUser(null);
      await fetchData();
    } catch (err: any) {
      alert(err.message || 'Failed to delete staff user.');
    } finally {
      setSubmitLoading(false);
    }
  };

  const columns: Column<UserInfo>[] = [
    {
      header: 'Email / Staff Handle',
      accessorKey: 'email',
      cell: (item) => (
        <div className="space-y-0.5">
          <p className="font-mono text-slate-900 dark:text-white font-bold">{item.email || 'Phone account'}</p>
          <p className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400 font-extrabold">
            Staff Ref: {formatReadableId(item.email || item.id, 'STF')}
          </p>
        </div>
      ),
    },
    {
      header: 'Role Governance',
      accessorKey: 'role',
      cell: (item) => (
        <select
          value={item.role}
          onChange={(e) => handleRoleChange(item, e.target.value)}
          className="text-xs font-bold font-mono px-2.5 py-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-indigo-700 dark:text-indigo-300 focus:outline-none"
        >
          <option value="admin">ADMIN (Full Access)</option>
          <option value="scheme_admin">SCHEME_ADMIN (Ops & Rules)</option>
          <option value="agent">AGENT (Assisted CSC)</option>
          <option value="citizen">CITIZEN (End User)</option>
        </select>
      ),
    },
    {
      header: 'Status',
      accessorKey: 'status',
      cell: (item) => <StatusBadge status={item.status} />,
    },
    {
      header: 'Created Date',
      accessorKey: 'created_at',
      cell: (item) => <span className="font-mono text-slate-600 dark:text-slate-400">{formatDate(item.created_at)}</span>,
    },
    {
      header: 'Account Actions',
      cell: (item) => (
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleToggleStatus(item)}
            className={`text-xs font-bold px-2.5 py-1.5 rounded-lg border transition-all ${
              item.status === 'active'
                ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30 hover:bg-amber-500/20'
                : 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20 hover:bg-emerald-500/20'
            }`}
          >
            {item.status === 'active' ? 'Suspend' : 'Activate'}
          </button>
          <button
            onClick={() => setDeletingUser(item)}
            className="p-1.5 rounded-lg bg-red-500/10 text-red-700 dark:text-red-300 border border-red-500/30 hover:bg-red-500/20 transition-all"
            title="Delete Staff Account"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-10">
      {/* Header & Provision Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-indigo-500" />
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">System Operations &amp; Staff Governance</h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Provision staff user accounts, configure role privilege matrices, and monitor core infrastructure health.
          </p>
        </div>

        <Button
          onClick={() => setShowAddUserModal(true)}
          className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white font-bold px-4 py-2.5 rounded-xl shadow-md flex items-center gap-2"
        >
          <UserPlus className="h-4 w-4" />
          <span>Provision Staff Account</span>
        </Button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold">
          {error}
        </div>
      )}

      {/* Infrastructure Health Card */}
      {health && (
        <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-200 dark:border-slate-800 pb-3">
            <Server className="h-5 w-5 text-indigo-500" />
            <h2 className="text-sm font-extrabold text-slate-900 dark:text-white uppercase tracking-wider">
              Infrastructure Health Status
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <span className="font-bold text-slate-700 dark:text-slate-300">PostgreSQL Database:</span>
              <StatusBadge status={health.database} />
            </div>
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <span className="font-bold text-slate-700 dark:text-slate-300">Redis Event Bus:</span>
              <StatusBadge status={health.redis} />
            </div>
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <span className="font-bold text-slate-700 dark:text-slate-300">System Readiness:</span>
              <StatusBadge status={health.overall} />
            </div>
          </div>
        </div>
      )}

      {/* Role Capabilities & Governance Reference Matrix */}
      <div className="bg-white dark:bg-slate-900/90 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-200 dark:border-slate-800 pb-3">
          <Sparkles className="h-5 w-5 text-indigo-500" />
          <h2 className="text-sm font-extrabold text-slate-900 dark:text-white uppercase tracking-wider">
            Staff Privilege &amp; Capability Matrix
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/20 space-y-2">
            <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-extrabold uppercase">
              <ShieldCheck className="w-4 h-4" />
              <span>ADMIN (System Administrator)</span>
            </div>
            <p className="text-slate-600 dark:text-slate-400 text-[11px]">
              Full platform control. Can manage staff users, review audit logs, publish schemes, manage knowledge sources, and configure infrastructure.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-blue-500/5 border border-blue-500/20 space-y-2">
            <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-extrabold uppercase">
              <ShieldCheck className="w-4 h-4" />
              <span>SCHEME_ADMIN (Scheme &amp; Rules Manager)</span>
            </div>
            <p className="text-slate-600 dark:text-slate-400 text-[11px]">
              Scheme authoring, AST rule simulation, opportunity crawling, document verification, citizen management, and application review.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 space-y-2">
            <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-extrabold uppercase">
              <UserCheck className="w-4 h-4" />
              <span>AGENT / CSC Operator</span>
            </div>
            <p className="text-slate-600 dark:text-slate-400 text-[11px]">
              Assisted citizen application submission, consent-scoped citizen profile access, document uploading, and applicant support.
            </p>
          </div>
        </div>
      </div>

      {/* Staff User Management Table */}
      <div className="space-y-4">
        <h2 className="text-sm font-extrabold text-slate-900 dark:text-white uppercase tracking-wider flex items-center space-x-2">
          <Shield className="h-4 w-4 text-indigo-500" />
          <span>Staff Accounts &amp; User Directory</span>
        </h2>

        {loading && !usersData ? (
          <TableSkeleton rows={5} cols={5} />
        ) : usersData ? (
          <div className="space-y-4">
            <DataTable
              columns={columns}
              data={usersData.items}
              keyExtractor={(item) => item.id}
              emptyMessage="No staff accounts found."
            />
            <Pagination
              page={usersData.page}
              pageSize={usersData.page_size}
              total={usersData.total}
              onPageChange={setPage}
            />
          </div>
        ) : null}
      </div>

      {/* Provision User Modal */}
      <Modal isOpen={showAddUserModal} onClose={() => setShowAddUserModal(false)} title="Provision Staff Account">
        <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Staff Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operator@civiclens.gov.in"
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Password</label>
            <input
              type="password"
              required
              minLength={12}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 12 characters..."
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">Assigned Operational Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2.5 text-sm text-slate-900 dark:text-white"
            >
              <option value="agent">AGENT / CSC Operator</option>
              <option value="scheme_admin">SCHEME_ADMIN (Rules &amp; Ops)</option>
              <option value="admin">ADMIN (System Administrator)</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <Button variant="outline" onClick={() => setShowAddUserModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitLoading} className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold">
              {submitLoading ? 'Provisioning...' : 'Provision Staff Account'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete User Modal */}
      {deletingUser && (
        <Modal isOpen={true} onClose={() => setDeletingUser(null)} title="Confirm Staff Account Deletion">
          <div className="space-y-4">
            <p className="text-xs text-slate-700 dark:text-slate-300">
              Are you sure you want to permanently delete staff account <strong>{deletingUser.email || deletingUser.id}</strong>?
            </p>
            <div className="flex justify-end space-x-3 pt-2">
              <Button variant="outline" onClick={() => setDeletingUser(null)}>
                Cancel
              </Button>
              <Button onClick={handleDeleteUser} disabled={submitLoading} className="bg-red-600 hover:bg-red-700 text-white font-bold">
                Delete Account
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
