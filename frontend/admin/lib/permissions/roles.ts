import { UserRole } from '@/types/api';

export interface RoleCapability {
  canViewDashboard: boolean;
  canManageApplications: boolean;
  canAssignApplications: boolean;
  canReviewApplications: boolean;
  canViewCitizens: boolean;
  canViewAssistedCitizens: boolean;
  canViewCitizenPII: boolean;
  canManageDocuments: boolean;
  canVerifyDocuments: boolean;
  canViewSchemes: boolean;
  canEditSchemeDrafts: boolean;
  canPublishSchemes: boolean;
  canSimulateRules: boolean;
  canManageKnowledge: boolean;
  canViewAuditLogs: boolean;
  canViewNotificationOps: boolean;
  canManageUsers: boolean;
  canViewSystemHealth: boolean;
}

export const ROLE_CAPABILITIES: Record<UserRole, RoleCapability> = {
  citizen: {
    canViewDashboard: false,
    canManageApplications: false,
    canAssignApplications: false,
    canReviewApplications: false,
    canViewCitizens: false,
    canViewAssistedCitizens: false,
    canViewCitizenPII: false,
    canManageDocuments: false,
    canVerifyDocuments: false,
    canViewSchemes: true,
    canEditSchemeDrafts: false,
    canPublishSchemes: false,
    canSimulateRules: false,
    canManageKnowledge: false,
    canViewAuditLogs: false,
    canViewNotificationOps: false,
    canManageUsers: false,
    canViewSystemHealth: false,
  },
  agent: {
    canViewDashboard: true,
    canManageApplications: true,
    canAssignApplications: false,
    canReviewApplications: true,
    canViewCitizens: false,
    canViewAssistedCitizens: true,
    canViewCitizenPII: true, // Only with active consent
    canManageDocuments: true,
    canVerifyDocuments: true,
    canViewSchemes: true,
    canEditSchemeDrafts: false,
    canPublishSchemes: false,
    canSimulateRules: false,
    canManageKnowledge: false,
    canViewAuditLogs: false,
    canViewNotificationOps: false,
    canManageUsers: false,
    canViewSystemHealth: false,
  },
  scheme_admin: {
    canViewDashboard: true,
    canManageApplications: true,
    canAssignApplications: true,
    canReviewApplications: true,
    canViewCitizens: true,
    canViewAssistedCitizens: true,
    canViewCitizenPII: true,
    canManageDocuments: true,
    canVerifyDocuments: true,
    canViewSchemes: true,
    canEditSchemeDrafts: true,
    canPublishSchemes: true,
    canSimulateRules: true,
    canManageKnowledge: true,
    canViewAuditLogs: false,
    canViewNotificationOps: true,
    canManageUsers: false,
    canViewSystemHealth: true,
  },
  admin: {
    canViewDashboard: true,
    canManageApplications: true,
    canAssignApplications: true,
    canReviewApplications: true,
    canViewCitizens: true,
    canViewAssistedCitizens: false,
    canViewCitizenPII: false, // Object-level authorization & audit required
    canManageDocuments: true,
    canVerifyDocuments: true,
    canViewSchemes: true,
    canEditSchemeDrafts: true,
    canPublishSchemes: true,
    canSimulateRules: true,
    canManageKnowledge: true,
    canViewAuditLogs: true,
    canViewNotificationOps: true,
    canManageUsers: true,
    canViewSystemHealth: true,
  },
};

export function hasCapability(role: UserRole | undefined, capability: keyof RoleCapability): boolean {
  if (!role || !ROLE_CAPABILITIES[role]) return false;
  return ROLE_CAPABILITIES[role][capability];
}
