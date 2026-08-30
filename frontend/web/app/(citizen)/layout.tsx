'use client';

import React, { useEffect } from 'react';
import { useAuth } from '@/lib/auth/auth-context';
import { useRouter } from 'next/navigation';
import LoadingPage from '@/app/loading';

import { FloatingAssistantWidget } from '@/components/assistant/floating-assistant-widget';

export default function CitizenLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return <LoadingPage />;
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <>
      {children}
      <FloatingAssistantWidget />
    </>
  );
}
