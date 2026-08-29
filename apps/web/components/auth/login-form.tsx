'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useTranslation } from '@/lib/i18n';
import { requestOtp } from '@/lib/api/auth';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';
import { Phone, ShieldCheck } from 'lucide-react';

interface LoginFormProps {
  onOtpSent: (phone: string) => void;
}

export function LoginForm({ onOtpSent }: LoginFormProps) {
  const { t } = useTranslation();
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanPhone = phone.trim();
    if (!/^\d{10}$/.test(cleanPhone)) {
      setError(t.auth.invalidPhone);
      return;
    }

    setError(null);
    setIsLoading(true);
    try {
      await requestOtp(cleanPhone);
      onOtpSent(cleanPhone);
    } catch (err: any) {
      setError(err.message || 'Failed to send OTP code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
      <div className="flex flex-col items-center text-center mb-6">
        <div className="w-12 h-12 bg-blue-600 text-white rounded-xl flex items-center justify-center mb-3 shadow-md">
          <ShieldCheck className="w-7 h-7" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900">{t.auth.welcome}</h1>
        <p className="text-sm text-slate-500 mt-1">{t.auth.subtitle}</p>
      </div>

      {error && <Alert type="error" className="mb-4">{error}</Alert>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label={t.auth.phoneLabel}
          type="tel"
          placeholder="e.g. 9876543210"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          maxLength={10}
          required
          autoFocus
        />

        <Button type="submit" className="w-full py-3" isLoading={isLoading}>
          <Phone className="w-4 h-4 mr-2" />
          {t.auth.sendOtp}
        </Button>
      </form>

      <div className="mt-6 pt-4 border-t border-slate-100 text-center text-sm text-slate-600">
        New to CivicLens?{' '}
        <Link href="/register" className="font-semibold text-blue-600 hover:text-blue-800 hover:underline">
          Create an Account
        </Link>
      </div>
    </div>
  );
}
