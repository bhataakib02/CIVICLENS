import { apiClient } from './client';
import { Application, ApplicationDetail, ApplicationPage, ApplicationChecklist } from '@/types/api';

export interface ApplicationQueryParams {
  status?: string;
  page?: number;
  page_size?: number;
}

export async function getApplications(params: ApplicationQueryParams = {}): Promise<ApplicationPage> {
  const query = new URLSearchParams();
  if (params.status) query.append('status', params.status);
  if (params.page) query.append('page', params.page.toString());
  if (params.page_size) query.append('page_size', params.page_size.toString());

  const queryString = query.toString();
  const endpoint = `/applications${queryString ? `?${queryString}` : ''}`;
  return apiClient<ApplicationPage>(endpoint);
}

export async function createApplication(data: {
  scheme_id: string;
  scheme_version_id?: string;
  scheme_specific_answers?: Record<string, any>;
  document_ids?: string[];
}): Promise<Application> {
  return apiClient<Application>('/applications', {
    method: 'POST',
    body: data
  });
}

export async function getApplicationDetail(applicationId: string): Promise<ApplicationDetail> {
  return apiClient<ApplicationDetail>(`/applications/${applicationId}`);
}

export async function submitApplication(applicationId: string): Promise<void> {
  await apiClient(`/applications/${applicationId}/submit`, {
    method: 'POST'
  });
}

export async function withdrawApplication(applicationId: string): Promise<void> {
  await apiClient(`/applications/${applicationId}/withdraw`, {
    method: 'POST'
  });
}

export async function getApplicationChecklist(applicationId: string): Promise<ApplicationChecklist> {
  return apiClient<ApplicationChecklist>(`/applications/${applicationId}/checklist`);
}

export async function resolveApplicationAction(applicationId: string, actionData?: Record<string, any>): Promise<void> {
  await apiClient(`/applications/${applicationId}/resolve-action`, {
    method: 'POST',
    body: actionData || {}
  });
}

export async function downloadApplicationPdf(applicationId: string): Promise<Blob> {
  return apiClient<Blob>(`/applications/${applicationId}/export`, {
    headers: { Accept: 'application/pdf' }
  });
}
