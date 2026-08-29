import { apiClient } from './client';
import { DashboardMetrics, SystemHealth, UserInfo, UserPage } from '@/types/api';

export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  return apiClient<DashboardMetrics>('/admin/dashboard');
}

export async function getSystemHealth(): Promise<SystemHealth> {
  return apiClient<SystemHealth>('/admin/system-health');
}

export async function getUsers(params?: { role?: string; page?: number; page_size?: number }): Promise<UserPage> {
  const query = new URLSearchParams();
  if (params?.role) query.set('role', params.role);
  if (params?.page) query.set('page', params.page.toString());
  if (params?.page_size) query.set('page_size', params.page_size.toString());

  return apiClient<UserPage>(`/admin/users?${query.toString()}`);
}

export async function createUser(data: { email: string; password: string; role: string }): Promise<UserInfo> {
  return apiClient<UserInfo>('/admin/users', {
    method: 'POST',
    body: data,
  });
}

export async function updateUser(id: string, data: { role?: string; status?: string }): Promise<UserInfo> {
  return apiClient<UserInfo>(`/admin/users/${id}`, {
    method: 'PATCH',
    body: data,
  });
}
