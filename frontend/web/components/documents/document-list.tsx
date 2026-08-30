'use client';

import React, { useState, useEffect } from 'react';
import { getDocuments, uploadDocument, getDocumentDetail, getDocumentDownloadUrl } from '@/lib/api/documents';
import { Document, DocumentDetail } from '@/types/api';
import { useTranslation } from '@/lib/i18n';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/ui/status-badge';
import { Modal } from '@/components/ui/modal';
import { Select } from '@/components/ui/select';
import { Alert } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { ExtractionReviewModal } from './extraction-review-modal';
import { formatDate } from '@/lib/formatting/date';
import { Upload, FileText, Download, Eye, Plus } from 'lucide-react';

export function DocumentList() {
  const { t } = useTranslation();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Upload modal state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [docType, setDocType] = useState('identity_proof');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  // Review modal state
  const [reviewDoc, setReviewDoc] = useState<DocumentDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const fetchDocs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getDocuments();
      setDocuments(data || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch documents.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);
    try {
      await uploadDocument(selectedFile, docType);
      setIsUploadOpen(false);
      setSelectedFile(null);
      await fetchDocs();
    } catch (err: any) {
      setError(err.message || 'Failed to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleReviewClick = async (docId: string) => {
    setIsLoadingDetail(true);
    try {
      const detail = await getDocumentDetail(docId);
      setReviewDoc(detail);
    } catch (err: any) {
      setError(err.message || 'Failed to load document details.');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleDownloadClick = async (docId: string) => {
    try {
      const { download_url } = await getDocumentDownloadUrl(docId);
      window.open(download_url, '_blank');
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve download link.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">{t.documents.title}</h1>
          <p className="text-sm text-slate-500 mt-1">{t.documents.subtitle}</p>
        </div>
        <Button onClick={() => setIsUploadOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          {t.documents.uploadBtn}
        </Button>
      </div>

      {error && <Alert type="error">{error}</Alert>}

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      ) : documents.length === 0 ? (
        <Card className="text-center py-12">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-2" />
          <p className="text-slate-500 text-sm">{t.common.noData}</p>
          <Button size="sm" className="mt-4" onClick={() => setIsUploadOpen(true)}>
            {t.documents.uploadBtn}
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {documents.map((doc) => (
            <Card key={doc.id} className="flex flex-col justify-between p-5 border-slate-200">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-blue-50 text-blue-700 rounded-xl">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm capitalize">{doc.document_type.replace(/_/g, ' ')}</h4>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">Uploaded: {formatDate(doc.uploaded_at)}</p>
                  </div>
                </div>
                <StatusBadge status={doc.status} />
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2 mt-2">
                <Button size="sm" variant="outline" onClick={() => handleDownloadClick(doc.id)}>
                  <Download className="w-3.5 h-3.5 mr-1" />
                  {t.common.download}
                </Button>

                {(doc.status === 'verification_required' || doc.status === 'verified' || doc.status === 'uploaded') && (
                  <Button size="sm" variant="ghost" onClick={() => handleReviewClick(doc.id)} isLoading={isLoadingDetail}>
                    <Eye className="w-3.5 h-3.5 mr-1" />
                    {t.documents.reviewExtraction}
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <Modal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} title={t.documents.uploadBtn}>
        <form onSubmit={handleUploadSubmit} className="space-y-4">
          <Select
            label={t.documents.selectDocType}
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            options={[
              { value: 'identity_proof', label: 'Aadhaar / Passport / Voter ID' },
              { value: 'income_certificate', label: 'Income Certificate' },
              { value: 'residence_certificate', label: 'Residence / Domicile Certificate' },
              { value: 'caste_certificate', label: 'Caste / Community Certificate' },
              { value: 'disability_certificate', label: 'Disability Certificate' }
            ]}
          />

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">{t.documents.chooseFile}</label>
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              required
              className="w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-slate-100">
            <Button variant="outline" type="button" onClick={() => setIsUploadOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button type="submit" isLoading={isUploading} disabled={!selectedFile}>
              <Upload className="w-4 h-4 mr-2" />
              {t.common.upload}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Extraction Review Modal */}
      {reviewDoc && (
        <ExtractionReviewModal
          isOpen={!!reviewDoc}
          onClose={() => setReviewDoc(null)}
          documentDetail={reviewDoc}
          onConfirmed={fetchDocs}
        />
      )}
    </div>
  );
}
