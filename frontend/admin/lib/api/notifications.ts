import { apiClient } from './client';
import { NotificationOps, NotificationOpsPage } from '@/types/api';

export async function getNotificationOps(params: {
  status?: string;
  channel?: string;
  page?: number;
  page_size?: number;
}): Promise<NotificationOpsPage> {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.channel) query.set('channel', params.channel);
  if (params.page) query.set('page', params.page.toString());
  if (params.page_size) query.set('page_size', params.page_size.toString());

  return apiClient<NotificationOpsPage>(`/admin/notifications?${query.toString()}`);
}

export async function retryNotification(id: string): Promise<NotificationOps> {
  return apiClient<NotificationOps>(`/admin/notifications/${id}/retry`, {
    method: 'POST',
  });
}
