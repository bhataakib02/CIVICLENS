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
  UserCheck,
  Building,
  LogOut,
  Sparkles,
  ChevronRight,
  ShieldCheck
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
    <aside className="w-64 bg-slate-950 border-r border-slate-800/90 flex flex-col h-screen sticky top-0 z-40 select-none shadow-2xl">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/90 flex items-center space-x-3.5">
        <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-blue-600 to-indigo-500 p-0.5 shadow-md shadow-indigo-500/30 flex-shrink-0">
          <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
            <Sparkles className="h-5 w-5 text-indigo-400" />
          </div>
        </div>
        <div className="overflow-hidden">
          <h1 className="font-extrabold text-sm text-white tracking-tight truncate">CivicLens Console</h1>
          <div className="flex items-center gap-1 mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono truncate">
              {role?.replace('_', ' ') || 'SCHEME ADMIN'}
            </p>
          </div>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Navigation Operations
        </div>
        {navigation
          .filter((item) => item.show)
          .map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`group flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-lg shadow-indigo-600/30 font-bold'
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-100'
                }`}
              >
                <div className="flex items-center gap-3 truncate">
                  <Icon className={`h-4 w-4 flex-shrink-0 transition-transform group-hover:scale-110 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-indigo-400'}`} />
                  <span className="truncate">{item.name}</span>
                </div>
                {isActive && <ChevronRight className="w-3.5 h-3.5 text-white/80" />}
              </Link>
            );
          })}
      </nav>

      {/* User Info & Logout Footer */}
      <div className="p-4 border-t border-slate-800/90 bg-slate-900/60">
        <div className="flex items-center justify-between gap-2">
          <div className="truncate space-y-0.5">
            <p className="text-xs font-bold text-white truncate">{account?.email || 'thefreelancer2076@gmail.com'}</p>
            <div className="flex items-center gap-1 text-[10px] text-indigo-400 font-mono font-semibold">
              <ShieldCheck className="w-3 h-3" />
              <span className="capitalize">{role || 'SCHEME_ADMIN'}</span>
            </div>
          </div>
          <button
            onClick={() => logout()}
            title="Log out from console"
            className="p-2 rounded-xl text-slate-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all flex-shrink-0"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
