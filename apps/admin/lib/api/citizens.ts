import { apiClient } from './client';
import { AssistedCitizen, CitizenDetail, CitizenSummaryPage, ConsentRecord } from '@/types/api';

export async function searchCitizens(params: {
  q?: string;
  page?: number;
  page_size?: number;
}): Promise<CitizenSummaryPage> {
  const query = new URLSearchParams();
  if (params.q) query.set('q', params.q);
  if (params.page) query.set('page', params.page.toString());
  if (params.page_size) query.set('page_size', params.page_size.toString());

  return apiClient<CitizenSummaryPage>(`/admin/citizens?${query.toString()}`);
}

export async function getCitizenDetail(userId: string): Promise<CitizenDetail> {
  return apiClient<CitizenDetail>(`/admin/citizens/${userId}`);
}

export async function getCitizenConsents(userId: string): Promise<ConsentRecord[]> {
  return apiClient<ConsentRecord[]>(`/admin/citizens/${userId}/consents`);
}

export async function getAgentCitizens(): Promise<AssistedCitizen[]> {
  return apiClient<AssistedCitizen[]>('/agent/citizens');
}

export async function getAgentCitizenDetail(userId: string): Promise<CitizenDetail> {
  return apiClient<CitizenDetail>(`/agent/citizens/${userId}`);
}
