import { apiClient } from './client';
import { SchemePage, SchemeDetail } from '@/types/api';

export interface SchemeQueryParams {
  q?: string;
  category?: string;
  scope?: 'central' | 'state';
  page?: number;
  page_size?: number;
}

export async function getSchemes(params: SchemeQueryParams = {}): Promise<SchemePage> {
  const query = new URLSearchParams();
  if (params.q) query.append('q', params.q);
  if (params.category) query.append('category', params.category);
  if (params.scope) query.append('scope', params.scope);
  if (params.page) query.append('page', params.page.toString());
  if (params.page_size) query.append('page_size', params.page_size.toString());

  const queryString = query.toString();
  const endpoint = `/schemes${queryString ? `?${queryString}` : ''}`;
  return apiClient<SchemePage>(endpoint);
}

export async function getSchemeById(schemeId: string): Promise<SchemeDetail> {
  return apiClient<SchemeDetail>(`/schemes/${schemeId}`);
}
