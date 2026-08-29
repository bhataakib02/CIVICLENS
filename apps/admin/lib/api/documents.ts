import { apiClient } from './client';
import { DocumentDetail, DocumentSummary } from '@/types/api';

export async function getDocuments(): Promise<DocumentSummary[]> {
  return apiClient<DocumentSummary[]>('/documents');
}

export async function getDocumentDetail(id: string): Promise<DocumentDetail> {
  return apiClient<DocumentDetail>(`/documents/${id}`);
}

export async function getDocumentDownloadUrl(id: string): Promise<{ download_url: string; expires_at: string }> {
  return apiClient<{ download_url: string; expires_at: string }>(`/documents/${id}/download`);
}

export async function confirmDocumentVerification(
  id: string,
  data: {
    action: 'confirm' | 'correct' | 'reject';
    corrected_fields?: Record<string, any>;
    correction_reason?: string;
  }
): Promise<DocumentDetail> {
  return apiClient<DocumentDetail>(`/documents/${id}/confirm`, {
    method: 'POST',
    body: data,
  });
}
