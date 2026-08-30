import { apiClient } from './client';
import { EligibilityResult } from '@/types/api';

export async function checkEligibility(schemeId: string): Promise<EligibilityResult> {
  return apiClient<EligibilityResult>('/eligibility/check', {
    method: 'POST',
    body: { scheme_id: schemeId }
  });
}

export async function checkAllEligibility(): Promise<EligibilityResult[]> {
  return apiClient<EligibilityResult[]>('/eligibility/check-all', {
    method: 'POST'
  });
}
