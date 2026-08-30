import { apiClient } from './client';
import { IngestionJob, KnowledgeSource } from '@/types/api';

export async function getKnowledgeSources(params?: { page?: number; page_size?: number }): Promise<KnowledgeSource[]> {
  const query = new URLSearchParams();
  if (params?.page) query.set('page', params.page.toString());
  if (params?.page_size) query.set('page_size', params.page_size.toString());

  return apiClient<KnowledgeSource[]>(`/knowledge/sources?${query.toString()}`);
}

export async function createKnowledgeSource(data: {
  title: string;
  url: string;
  publisher?: string;
  scheme_id?: string;
  scheme_version_id?: string;
}): Promise<IngestionJob> {
  return apiClient<IngestionJob>('/knowledge/sources', {
    method: 'POST',
    body: data,
  });
}

export async function getIngestionJob(jobId: string): Promise<IngestionJob> {
  return apiClient<IngestionJob>(`/knowledge/jobs/${jobId}`);
}

export async function verifyKnowledgeSource(
  sourceId: string,
  data: {
    verification_status: 'verified' | 'rejected' | 'stale';
    trust_level: 'official_government' | 'official_document' | 'official_portal' | 'verified_secondary' | 'unverified';
  }
): Promise<KnowledgeSource> {
  return apiClient<KnowledgeSource>(`/knowledge/sources/${sourceId}/verify`, {
    method: 'POST',
    body: data,
  });
}

export async function searchKnowledge(query: string, schemeId?: string, limit = 5) {
  return apiClient<any[]>('/knowledge/search', {
    method: 'POST',
    body: { query, scheme_id: schemeId, limit },
  });
}
