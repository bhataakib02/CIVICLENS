'use client';

import React from 'react';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="max-w-md mx-auto my-12 space-y-4 text-center">
      <Alert type="error" title="Something went wrong">
        {error.message || 'An unexpected error occurred while loading this page.'}
      </Alert>
      <Button onClick={() => reset()}>Try Again</Button>
    </div>
  );
}
