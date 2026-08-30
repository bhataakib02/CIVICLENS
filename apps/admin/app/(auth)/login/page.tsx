'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/auth-context';
import { requestOtp, verifyOtp } from '@/lib/api/auth';
import { Layers, ShieldCheck, Lock, Mail, AlertCircle, Loader2 } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [requiresMfa, setRequiresMfa] = useState(false);
  const [error, setError] = useState('');
  const [infoMsg, setInfoMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setInfoMsg('');
    setLoading(true);

    try {
      if (!requiresMfa) {
        // Step 1: Validate email + password and dispatch real 6-digit Email OTP
        const cleanEmail = email.trim();
        if (!cleanEmail || !password) {
          setError('Please enter staff email and password.');
          setLoading(false);
          return;
        }

        // Verify password first
        await login(cleanEmail, password);

        // Dispatch real 6-digit Email OTP
        try {
          await requestOtp(cleanEmail);
        } catch (otpErr) {
          // Continue if rate limited or already requested
        }

        setRequiresMfa(true);
        setInfoMsg(`A 6-digit OTP verification code has been dispatched to ${cleanEmail}. Enter the code below to access the Admin Console.`);
      } else {
        // Step 2: Verify 6-digit Email OTP code
        const cleanCode = mfaCode.trim();
        if (!/^\d{6}$/.test(cleanCode)) {
          setError('Please enter a valid 6-digit Email OTP verification code.');
          setLoading(false);
          return;
        }

        // Verify 6-digit OTP with backend
        try {
          await verifyOtp(email.trim(), cleanCode);
        } catch (otpErr: any) {
          setError(otpErr.message || 'Invalid or expired OTP code.');
          setLoading(false);
          return;
        }

        // Re-authenticate session & enter Admin Console
        await login(email.trim(), password);
        router.push('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-elevated p-8 shadow-2xl border border-console-border">
      <div className="text-center mb-8">
        <div className="h-12 w-12 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mx-auto mb-3">
          <Layers className="h-6 w-6" />
        </div>
        <h1 className="text-xl font-bold text-console-text tracking-tight">CivicLens Operations Console</h1>
        <p className="text-xs text-console-muted mt-1">Authenticated Staff & CSC Portal</p>
      </div>

      {infoMsg && (
        <div className="mb-6 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-start space-x-2">
          <ShieldCheck className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <span>{infoMsg}</span>
        </div>
      )}

      {error && (
        <div className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-start space-x-2">
          <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {!requiresMfa ? (
          <>
            <div>
              <label className="block text-xs font-medium text-console-text mb-1">Staff Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-console-muted" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="operator@civiclens.gov.in"
                  className="input-field pl-9 w-full text-xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-console-text mb-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-console-muted" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="input-field pl-9 w-full text-xs"
                />
              </div>
            </div>
          </>
        ) : (
          <div className="animate-in fade-in duration-300 space-y-3">
            <div className="p-3 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs flex items-center space-x-2">
              <ShieldCheck className="h-5 w-5 text-indigo-400 flex-shrink-0" />
              <span>Multi-Factor Authentication Required. Enter your 6-Digit Email OTP.</span>
            </div>

            <div>
              <label className="block text-xs font-medium text-console-text mb-1">6-Digit Email OTP Code</label>
              <input
                type="text"
                required
                maxLength={6}
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
                placeholder="6-digit OTP code"
                className="input-field w-full text-center text-lg tracking-[0.5em] font-mono"
                autoFocus
              />
            </div>

            <div className="text-center pt-1">
              <button
                type="button"
                onClick={async () => {
                  setError('');
                  setInfoMsg(`A new 6-digit Email OTP code has been dispatched to ${email}`);
                  try {
                    await requestOtp(email.trim());
                  } catch (err: any) {}
                }}
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                Resend Email OTP Code
              </button>
            </div>
          </div>
        )}

        <button type="submit" disabled={loading} className="btn-primary w-full text-xs py-2.5 mt-2 flex items-center justify-center space-x-2">
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <span>{requiresMfa ? 'Verify & Enter Admin Console' : 'Sign In to Console'}</span>
          )}
        </button>
      </form>

      <div className="mt-6 pt-4 border-t border-console-border text-center">
        <p className="text-[10px] text-console-muted">
          Unauthorized access is strictly prohibited and logged per audit policy.
        </p>
      </div>
    </div>
  );
}
