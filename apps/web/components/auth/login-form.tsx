'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useTranslation } from '@/lib/i18n';
import { useAuth } from '@/lib/auth/auth-context';
import { requestOtp } from '@/lib/api/auth';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';
import { Phone, ShieldCheck, Mail, Lock, ArrowRight } from 'lucide-react';

interface LoginFormProps {
  onOtpSent: (phone: string) => void;
}

export function LoginForm({ onOtpSent }: LoginFormProps) {
  const { t } = useTranslation();
  const { loginWithEmail } = useAuth();
  const router = useRouter();

  // Tab state: 'email' | 'phone'
  const [method, setMethod] = useState<'email' | 'phone'>('email');

  // Email form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Phone form state
  const [phone, setPhone] = useState('');

  // Common UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanEmail = email.trim();
    if (!cleanEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)) {
      setError('Please enter a valid email address.');
      return;
    }

    if (!password) {
      setError('Please enter your password.');
      return;
    }

    setIsLoading(true);
    try {
      await loginWithEmail(cleanEmail, password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Invalid email or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePhoneSubmit = async (e: React.FormEvent) => {
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

      {/* Auth Method Selector Tabs */}
      <div className="flex bg-slate-100 p-1 rounded-xl mb-6">
        <button
          type="button"
          onClick={() => {
            setMethod('email');
            setError(null);
          }}
          className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all flex items-center justify-center gap-1.5 ${
            method === 'email'
              ? 'bg-white text-blue-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Mail className="w-3.5 h-3.5" />
          Email &amp; Password
        </button>
        <button
          type="button"
          onClick={() => {
            setMethod('phone');
            setError(null);
          }}
          className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all flex items-center justify-center gap-1.5 ${
            method === 'phone'
              ? 'bg-white text-blue-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Phone className="w-3.5 h-3.5" />
          Mobile OTP
        </button>
      </div>

      {error && <Alert type="error" className="mb-4">{error}</Alert>}

      {method === 'email' ? (
        <form onSubmit={handleEmailSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            placeholder="citizen@example.gov.in"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <Button type="submit" className="w-full py-3" isLoading={isLoading}>
            <ArrowRight className="w-4 h-4 mr-2" />
            Sign In
          </Button>
        </form>
      ) : (
        <form onSubmit={handlePhoneSubmit} className="space-y-4">
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
      )}

      <div className="mt-6 pt-4 border-t border-slate-100 text-center text-sm text-slate-600">
        New to CivicLens?{' '}
        <Link href="/register" className="font-semibold text-blue-600 hover:text-blue-800 hover:underline">
          Create an Account
        </Link>
      </div>
    </div>
  );
}
