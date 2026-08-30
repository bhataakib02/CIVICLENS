import { describe, it, expect } from 'vitest';
import { hasCapability } from '@/lib/permissions/roles';

describe('Admin Capabilities and RBAC Matrix', () => {
  it('correctly checks role capabilities for Admin', () => {
    expect(hasCapability('admin', 'canViewDashboard')).toBe(true);
    expect(hasCapability('admin', 'canManageUsers')).toBe(true);
    expect(hasCapability('admin', 'canViewAuditLogs')).toBe(true);
    expect(hasCapability('admin', 'canPublishSchemes')).toBe(true);
  });

  it('correctly enforces capabilities for Scheme Admin', () => {
    expect(hasCapability('scheme_admin', 'canEditSchemeDrafts')).toBe(true);
    expect(hasCapability('scheme_admin', 'canSimulateRules')).toBe(true);
    expect(hasCapability('scheme_admin', 'canManageUsers')).toBe(false);
    expect(hasCapability('scheme_admin', 'canViewAuditLogs')).toBe(false);
  });

  it('correctly restricts Agent access to system admin capabilities', () => {
    expect(hasCapability('agent', 'canReviewApplications')).toBe(true);
    expect(hasCapability('agent', 'canVerifyDocuments')).toBe(true);
    expect(hasCapability('agent', 'canEditSchemeDrafts')).toBe(false);
    expect(hasCapability('agent', 'canManageUsers')).toBe(false);
  });

  it('returns false for undefined or unknown roles', () => {
    expect(hasCapability(undefined, 'canViewDashboard')).toBe(false);
    // @ts-expect-error testing invalid role string
    expect(hasCapability('invalid_role', 'canViewDashboard')).toBe(false);
  });
});
