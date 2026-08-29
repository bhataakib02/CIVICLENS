'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { ApplicationDetailView } from '@/components/applications/application-detail-view';

export default function ApplicationDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  return <ApplicationDetailView applicationId={id} />;
}
