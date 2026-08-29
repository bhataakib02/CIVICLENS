'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FileText,
  Users,
  FolderArchive,
  BookOpen,
  History,
  Bell,
  Settings,
  ShieldAlert,
  UserCheck,
  Building,
  LogOut,
  Layers,
} from 'lucide-react';
import { useAuth } from '@/lib/auth/auth-context';
import { hasCapability } from '@/lib/permissions/roles';

export function Sidebar() {
  const pathname = usePathname();
  const { account, logout } = useAuth();
  const role = account?.role;

  const navigation = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: LayoutDashboard,
      show: true,
    },
    {
      name: 'Assisted Citizens',
      href: '/assisted-citizens',
      icon: UserCheck,
      show: hasCapability(role, 'canViewAssistedCitizens'),
    },
    {
      name: 'Applications',
      href: '/applications',
      icon: FileText,
      show: hasCapability(role, 'canManageApplications'),
    },
    {
      name: 'Documents',
      href: '/documents',
      icon: FolderArchive,
      show: hasCapability(role, 'canManageDocuments'),
    },
    {
      name: 'Schemes',
      href: '/schemes',
      icon: Building,
      show: hasCapability(role, 'canViewSchemes'),
    },
    {
      name: 'Citizens',
      href: '/citizens',
      icon: Users,
      show: hasCapability(role, 'canViewCitizens'),
    },
    {
      name: 'Knowledge Base',
      href: '/knowledge',
      icon: BookOpen,
      show: hasCapability(role, 'canManageKnowledge'),
    },
    {
      name: 'Audit Logs',
      href: '/audit',
      icon: History,
      show: hasCapability(role, 'canViewAuditLogs'),
    },
    {
      name: 'Notification Ops',
      href: '/notifications',
      icon: Bell,
      show: hasCapability(role, 'canViewNotificationOps'),
    },
    {
      name: 'Settings & Users',
      href: '/settings',
      icon: Settings,
      show: hasCapability(role, 'canManageUsers'),
    },
  ];

  return (
    <aside className="w-64 bg-console-surface border-r border-console-border flex flex-col h-screen sticky top-0">
      {/* Brand Header */}
      <div className="p-4 border-b border-console-border flex items-center space-x-3">
        <div className="h-9 w-9 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
          <Layers className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-semibold text-sm text-console-text tracking-wide">CivicLens Console</h1>
          <p className="text-[10px] text-console-muted uppercase tracking-wider font-mono">
            {role?.replace('_', ' ')}
          </p>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navigation
          .filter((item) => item.show)
          .map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-console-accent text-white shadow-md shadow-indigo-600/20'
                    : 'text-console-muted hover:bg-console-elevated hover:text-console-text'
                }`}
              >
                <Icon className={`mr-3 h-4 w-4 flex-shrink-0 ${isActive ? 'text-white' : 'text-console-muted'}`} />
                {item.name}
              </Link>
            );
          })}
      </nav>

      {/* User Info & Logout */}
      <div className="p-3 border-t border-console-border bg-console-bg/50">
        <div className="flex items-center justify-between">
          <div className="truncate">
            <p className="text-xs font-medium text-console-text truncate">{account?.email || 'Operator'}</p>
            <p className="text-[10px] text-console-muted capitalize">{role}</p>
          </div>
          <button
            onClick={() => logout()}
            title="Log out"
            className="p-1.5 rounded-lg text-console-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
