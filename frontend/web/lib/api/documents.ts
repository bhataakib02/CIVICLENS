import { apiClient } from './client';
import { Document, DocumentDetail, UploadInitResponse } from '@/types/api';

export async function initUpload(documentType: string, filename: string, sizeBytes: number): Promise<UploadInitResponse> {
  return apiClient<UploadInitResponse>('/documents/upload-init', {
    method: 'POST',
    body: {
      document_type: documentType,
      filename,
      size_bytes: sizeBytes
    }
  });
}

export async function getDocuments(): Promise<Document[]> {
  return apiClient<Document[]>('/documents');
}

export async function uploadDocument(file: File, documentType: string): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);

  return apiClient<Document>('/documents', {
    method: 'POST',
    isMultipart: true,
    body: formData
  });
}

export async function getDocumentDetail(documentId: string): Promise<DocumentDetail> {
  return apiClient<DocumentDetail>(`/documents/${documentId}`);
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiClient(`/documents/${documentId}`, {
    method: 'DELETE'
  });
}

export async function completeDocument(documentId: string): Promise<void> {
  await apiClient(`/documents/${documentId}/complete`, {
    method: 'POST'
  });
}

export async function getDocumentDownloadUrl(documentId: string): Promise<{ download_url: string }> {
  return apiClient<{ download_url: string }>(`/documents/${documentId}/download`);
}

export async function confirmDocumentExtraction(documentId: string, correctedFields?: Record<string, any>): Promise<void> {
  await apiClient(`/documents/${documentId}/confirm`, {
    method: 'POST',
    body: { corrected_fields: correctedFields || {} }
  });
}
