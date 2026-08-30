import { apiClient } from './client';
import { AuditLogPage } from '@/types/api';

export async function getAuditLogs(params: {
  actor_id?: string;
  action?: string;
  entity_type?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}): Promise<AuditLogPage> {
  const query = new URLSearchParams();
  if (params.actor_id) query.set('actor_id', params.actor_id);
  if (params.action) query.set('action', params.action);
  if (params.entity_type) query.set('entity_type', params.entity_type);
  if (params.date_from) query.set('date_from', params.date_from);
  if (params.date_to) query.set('date_to', params.date_to);
  if (params.page) query.set('page', params.page.toString());
  if (params.page_size) query.set('page_size', params.page_size.toString());

  return apiClient<AuditLogPage>(`/admin/audit-logs?${query.toString()}`);
}
