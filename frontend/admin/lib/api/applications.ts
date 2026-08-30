import { apiClient } from './client';
import { ApplicationDetail, ApplicationPage } from '@/types/api';

export async function getApplications(params: {
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<ApplicationPage> {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.page) query.set('page', params.page.toString());
  if (params.page_size) query.set('page_size', params.page_size.toString());

  return apiClient<ApplicationPage>(`/applications?${query.toString()}`);
}

export async function getApplication(id: string): Promise<ApplicationDetail> {
  return apiClient<ApplicationDetail>(`/applications/${id}`);
}

export async function assignApplication(id: string, caseWorkerId: string): Promise<ApplicationDetail> {
  return apiClient<ApplicationDetail>(`/applications/${id}/assign`, {
    method: 'POST',
    body: { case_worker_id: caseWorkerId },
  });
}

export async function reviewApplication(
  id: string,
  data: {
    action: 'approve' | 'reject' | 'request_action';
    reason?: string;
    required_items?: string[];
  }
): Promise<ApplicationDetail> {
  return apiClient<ApplicationDetail>(`/applications/${id}/review`, {
    method: 'POST',
    body: data,
  });
}

export async function completeApplication(id: string): Promise<ApplicationDetail> {
  return apiClient<ApplicationDetail>(`/applications/${id}/complete`, {
    method: 'POST',
  });
}

export async function exportApplicationPdf(id: string): Promise<Blob> {
  return apiClient<Blob>(`/applications/${id}/export`);
}
