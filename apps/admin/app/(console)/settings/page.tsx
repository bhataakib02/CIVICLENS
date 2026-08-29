'use client';

import React, { useEffect, useState } from 'react';
import { createUser, getSystemHealth, getUsers, updateUser } from '@/lib/api/system';
import { SystemHealth, UserInfo, UserPage } from '@/types/api';
import { DataTable, Column } from '@/components/ui/data-table';
import { StatusBadge } from '@/components/ui/status-badge';
import { Pagination } from '@/components/ui/pagination';
import { TableSkeleton } from '@/components/ui/loading-skeleton';
import { formatDate } from '@/lib/formatting';
import { Settings, Shield, UserPlus, Server, Activity, Loader2 } from 'lucide-react';

export default function SettingsPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [usersData, setUsersData] = useState<UserPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [showAddUserModal, setShowAddUserModal] = useState(false);

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('agent');
  const [submitLoading, setSubmitLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const h = await getSystemHealth();
      const u = await getUsers({ page, page_size: 10 });
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

  const columns: Column<UserInfo>[] = [
    {
      header: 'Email / Staff ID',
      accessorKey: 'email',
      cell: (item) => <span className="font-mono text-console-text font-medium">{item.email || item.id}</span>,
    },
    {
      header: 'Role',
      accessorKey: 'role',
      cell: (item) => (
        <span className="font-mono text-xs uppercase px-2 py-0.5 rounded bg-console-surface border border-console-border text-console-accent font-semibold">
          {item.role}
        </span>
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
      cell: (item) => <span className="font-mono text-xs">{formatDate(item.created_at)}</span>,
    },
    {
      header: 'Account Actions',
      cell: (item) => (
        <button
          onClick={() => handleToggleStatus(item)}
          className={`btn-secondary text-[11px] py-1 px-2.5 ${
            item.status === 'active' ? 'border-red-500/30 text-red-400 hover:bg-red-500/10' : 'border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10'
          }`}
        >
          {item.status === 'active' ? 'Suspend Account' : 'Reactivate Account'}
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-console-text tracking-tight">System Operations & Staff Control</h1>
          <p className="text-xs text-console-muted mt-1">Operational health overview and staff role governance</p>
        </div>

        <button
          onClick={() => setShowAddUserModal(true)}
          className="btn-primary text-xs flex items-center space-x-1.5"
        >
          <UserPlus className="h-4 w-4" />
          <span>Provision Staff Account</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
          {error}
        </div>
      )}

      {/* Health Overview */}
      {health && (
        <div className="glass-card p-5 space-y-3">
          <h2 className="text-xs font-semibold text-console-muted uppercase tracking-wider flex items-center space-x-2">
            <Server className="h-4 w-4 text-console-accent" />
            <span>Infrastructure Health Status</span>
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-3 rounded-lg bg-console-bg border border-console-border flex items-center justify-between">
              <span>PostgreSQL Database:</span>
              <StatusBadge status={health.database} />
            </div>
            <div className="p-3 rounded-lg bg-console-bg border border-console-border flex items-center justify-between">
              <span>Redis Event Bus:</span>
              <StatusBadge status={health.redis} />
            </div>
            <div className="p-3 rounded-lg bg-console-bg border border-console-border flex items-center justify-between">
              <span>System Readiness:</span>
              <StatusBadge status={health.overall} />
            </div>
          </div>
        </div>
      )}

      {/* Staff User Management */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold text-console-text flex items-center space-x-2">
          <Shield className="h-4 w-4 text-console-accent" />
          <span>Staff Accounts & Privilege Governance</span>
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
      {showAddUserModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="glass-elevated max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-semibold text-console-text mb-4">Provision Staff Account</h3>
            <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-console-text mb-1">Staff Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="operator@civiclens.gov.in"
                  className="input-field w-full text-xs"
                />
              </div>

              <div>
                <label className="block font-medium text-console-text mb-1">Password</label>
                <input
                  type="password"
                  required
                  minLength={12}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min 12 characters..."
                  className="input-field w-full text-xs"
                />
              </div>

              <div>
                <label className="block font-medium text-console-text mb-1">Assigned Operational Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="input-field w-full text-xs"
                >
                  <option value="agent">AGENT / CSC Operator</option>
                  <option value="scheme_admin">SCHEME_ADMIN</option>
                  <option value="admin">ADMIN (System Administrator)</option>
                </select>
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddUserModal(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button type="submit" disabled={submitLoading} className="btn-primary text-xs flex items-center space-x-1.5">
                  {submitLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <span>Create Staff Account</span>}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
