import { apiClient } from './client';
import {
  EligibilityRule,
  RuleValidationResult,
  SchemeDetail,
  SchemePage,
  SchemeSummary,
  SchemeVersion,
  SimulationResult,
} from '@/types/api';

export async function getSchemes(params: {
  q?: string;
  category?: string;
  scope?: string;
  page?: number;
  page_size?: number;
}): Promise<SchemePage> {
  const query = new URLSearchParams();
  if (params.q) query.set('q', params.q);
  if (params.category) query.set('category', params.category);
  if (params.scope) query.set('scope', params.scope);
  if (params.page) query.set('page', params.page.toString());
  if (params.page_size) query.set('page_size', params.page_size.toString());

  return apiClient<SchemePage>(`/schemes?${query.toString()}`);
}

export async function getScheme(id: string): Promise<SchemeDetail> {
  return apiClient<SchemeDetail>(`/schemes/${id}`);
}

export async function createScheme(data: {
  canonical_name: string;
  category: string;
  scope: 'central' | 'state';
  administering_dept?: string;
  code?: string;
}): Promise<SchemeSummary> {
  return apiClient<SchemeSummary>('/schemes', {
    method: 'POST',
    body: data,
  });
}

export async function getSchemeVersions(schemeId: string): Promise<SchemeVersion[]> {
  return apiClient<SchemeVersion[]>(`/schemes/${schemeId}/versions`);
}

export async function createSchemeVersion(
  schemeId: string,
  data: {
    benefits_summary: string;
    effective_from: string;
    effective_to?: string | null;
    knowledge_source_id?: string | null;
  }
): Promise<SchemeVersion> {
  return apiClient<SchemeVersion>(`/schemes/${schemeId}/versions`, {
    method: 'POST',
    body: data,
  });
}

export async function submitSchemeVersionForReview(versionId: string): Promise<SchemeVersion> {
  return apiClient<SchemeVersion>(`/admin/scheme-versions/${versionId}/submit-for-review`, {
    method: 'POST',
  });
}

export async function publishSchemeVersion(versionId: string): Promise<SchemeVersion> {
  return apiClient<SchemeVersion>(`/admin/scheme-versions/${versionId}/publish`, {
    method: 'POST',
  });
}

export async function supersedeSchemeVersion(versionId: string): Promise<SchemeVersion> {
  return apiClient<SchemeVersion>(`/admin/scheme-versions/${versionId}/supersede`, {
    method: 'POST',
  });
}

export async function getVersionRules(versionId: string): Promise<EligibilityRule[]> {
  return apiClient<EligibilityRule[]>(`/scheme-versions/${versionId}/rules`);
}

export async function setVersionRules(versionId: string, rules: any[]): Promise<EligibilityRule[]> {
  return apiClient<EligibilityRule[]>(`/scheme-versions/${versionId}/rules`, {
    method: 'POST',
    body: { rules },
  });
}

export async function validateRules(rules: any[]): Promise<RuleValidationResult> {
  return apiClient<RuleValidationResult>('/admin/rules/validate', {
    method: 'POST',
    body: { rules },
  });
}

export async function simulateRules(versionId: string, draftRules: any[]): Promise<SimulationResult> {
  return apiClient<SimulationResult>('/admin/eligibility/simulate', {
    method: 'POST',
    body: {
      scheme_version_id: versionId,
      draft_rules: draftRules,
    },
  });
}
