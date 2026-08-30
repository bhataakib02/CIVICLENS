import React, { useState, useEffect } from 'react';
import { useTranslation } from '@/lib/i18n';
import { useAuth } from '@/lib/auth/auth-context';
import { requestOtp } from '@/lib/api/auth';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';
import { KeyRound, ArrowLeft, RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface OtpFormProps {
  phone: string;
  onBack: () => void;
}

export function OtpForm({ phone, onBack }: OtpFormProps) {
  const { t } = useTranslation();
  const { loginWithOtp } = useAuth();
  const router = useRouter();
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(30);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    let timer: any;
    if (resendTimer > 0) {
      timer = setInterval(() => setResendTimer((prev) => prev - 1), 1000);
    }
    return () => clearInterval(timer);
  }, [resendTimer]);

  const handleResend = async () => {
    if (resendTimer > 0 || resendLoading) return;
    setError(null);
    setSuccessMsg(null);
    setResendLoading(true);
    try {
      await requestOtp(phone);
      setSuccessMsg(`A new 6-digit verification OTP code has been dispatched to +91 ${phone}`);
      setResendTimer(30);
    } catch (err: any) {
      setError(err.message || 'Failed to resend OTP code.');
    } finally {
      setResendLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanCode = code.trim();
    if (!/^\d{6}$/.test(cleanCode)) {
      setError(t.auth.invalidOtp);
      return;
    }

    setError(null);
    setIsLoading(true);
    try {
      await loginWithOtp(phone, cleanCode);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Invalid or expired OTP code.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
      <button
        onClick={onBack}
        className="flex items-center text-xs font-semibold text-slate-500 hover:text-slate-800 mb-4 transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5 mr-1" />
        {t.common.back}
      </button>

      <div className="text-center mb-6">
        <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-xl flex items-center justify-center mx-auto mb-3">
          <KeyRound className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">{t.auth.enterOtp}</h2>
        <p className="text-xs text-slate-500 mt-1">
          {t.auth.otpSent} <span className="font-semibold text-slate-700">+91 {phone}</span>
        </p>
      </div>

      {error && <Alert type="error" className="mb-4">{error}</Alert>}
      {successMsg && <Alert type="success" className="mb-4">{successMsg}</Alert>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label={t.auth.otpLabel}
          type="text"
          placeholder="6-digit OTP code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          maxLength={6}
          required
          autoFocus
          className="text-center letter-spacing-2 text-lg font-mono font-bold"
        />

        <Button type="submit" className="w-full py-3" isLoading={isLoading}>
          {t.auth.verifyOtp}
        </Button>

        <div className="text-center pt-2">
          <button
            type="button"
            onClick={handleResend}
            disabled={resendTimer > 0 || resendLoading}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${resendLoading ? 'animate-spin' : ''}`} />
            {resendTimer > 0 ? `Resend OTP in ${resendTimer}s` : 'Resend OTP Code'}
          </button>
        </div>
      </form>
    </div>
  );
}
