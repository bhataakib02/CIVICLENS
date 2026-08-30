import { apiClient } from './client';
import { Notification } from '@/types/api';

export async function getNotifications(page = 1, pageSize = 20): Promise<Notification[]> {
  const data = await apiClient<{ items: Notification[]; total: number; page: number; page_size: number }>(`/notifications?page=${page}&page_size=${pageSize}`);
  return data.items || [];
}

export async function getNotificationPreferences(): Promise<Record<string, any>> {
  return apiClient<Record<string, any>>('/notifications/preferences');
}

export async function updateNotificationPreferences(preferences: Record<string, any>): Promise<Record<string, any>> {
  return apiClient<Record<string, any>>('/notifications/preferences', {
    method: 'PATCH',
    body: preferences
  });
}
