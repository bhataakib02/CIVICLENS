import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function NotFoundPage() {
  return (
    <div className="max-w-md mx-auto my-16 text-center space-y-4">
      <h1 className="text-4xl font-extrabold text-slate-900">404</h1>
      <h2 className="text-xl font-bold text-slate-700">Page Not Found</h2>
      <p className="text-sm text-slate-500">
        The public service page or application link you requested does not exist.
      </p>
      <Link href="/dashboard" className="inline-block mt-4">
        <Button>Return to Dashboard</Button>
      </Link>
    </div>
  );
}
