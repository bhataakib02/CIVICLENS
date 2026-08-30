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

export async function updateCitizen(
  userId: string,
  data: { email?: string; phone_number?: string; password?: string; status?: string }
): Promise<CitizenDetail> {
  return apiClient<CitizenDetail>(`/admin/citizens/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function sendCitizenOtp(userId: string): Promise<{ success: boolean; message: string; target: string }> {
  return apiClient<{ success: boolean; message: string; target: string }>(`/admin/citizens/${userId}/send-otp`, {
    method: 'POST',
  });
}

export async function updateCitizenProfile(userId: string, data: Record<string, any>): Promise<CitizenDetail> {
  return apiClient<CitizenDetail>(`/admin/citizens/${userId}/profile`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteCitizen(userId: string): Promise<{ success: boolean; message: string }> {
  return apiClient<{ success: boolean; message: string }>(`/admin/citizens/${userId}`, {
    method: 'DELETE',
  });
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
