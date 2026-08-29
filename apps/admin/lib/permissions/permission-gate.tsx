'use client';

import React from 'react';
import { useAuth } from '../auth/auth-context';
import { hasCapability, RoleCapability } from './roles';

interface PermissionGateProps {
  capability?: keyof RoleCapability;
  allowedRoles?: Array<'agent' | 'scheme_admin' | 'admin'>;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export function PermissionGate({ capability, allowedRoles, fallback = null, children }: PermissionGateProps) {
  const { account } = useAuth();

  if (!account) return <>{fallback}</>;

  if (allowedRoles && !allowedRoles.includes(account.role as any)) {
    return <>{fallback}</>;
  }

  if (capability && !hasCapability(account.role, capability)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
