'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/auth-context';
import { requestOtp, verifyOtp } from '@/lib/api/auth';
import { ShieldCheck, Lock, Mail, AlertCircle, Loader2, Sparkles, RefreshCw, KeyRound } from 'lucide-react';

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
  const [resendLoading, setResendLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setInfoMsg('');
    setLoading(true);

    try {
      if (!requiresMfa) {
        const cleanEmail = email.trim();
        if (!cleanEmail || !password) {
          setError('Please enter staff email address and password.');
          setLoading(false);
          return;
        }

        // Verify password first
        await login(cleanEmail, password);

        // Dispatch real 6-digit Email OTP
        try {
          await requestOtp(cleanEmail);
        } catch (otpErr) {}

        setRequiresMfa(true);
        setInfoMsg(`A 6-digit verification code has been dispatched to ${cleanEmail}. Enter the code below to enter the console.`);
      } else {
        const cleanCode = mfaCode.trim();
        if (!/^\d{6}$/.test(cleanCode)) {
          setError('Please enter a valid 6-digit Email OTP verification code.');
          setLoading(false);
          return;
        }

        try {
          await verifyOtp(email.trim(), cleanCode);
        } catch (otpErr: any) {
          setError(otpErr.message || 'Invalid or expired OTP code.');
          setLoading(false);
          return;
        }

        await login(email.trim(), password);
        router.push('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (resendLoading || !email) return;
    setError('');
    setInfoMsg('');
    setResendLoading(true);
    try {
      await requestOtp(email.trim());
      setInfoMsg(`A new 6-digit Email OTP verification code has been dispatched to ${email.trim()}`);
    } catch (err: any) {
      setError('Failed to resend OTP code.');
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="relative w-full max-w-md mx-auto">
      {/* Background Glow Blobs */}
      <div className="absolute -top-12 -left-12 w-64 h-64 bg-indigo-600/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-12 -right-12 w-64 h-64 bg-blue-600/20 rounded-full blur-3xl pointer-events-none" />

      {/* Main Glassmorphic Elevated Card */}
      <div className="relative glass-elevated p-8 sm:p-10 border border-slate-800/90 shadow-2xl shadow-indigo-950/50 rounded-3xl">
        {/* Header Icon & Title */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-blue-500 p-0.5 shadow-lg shadow-indigo-500/30 mx-auto mb-4">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <Sparkles className="w-7 h-7 text-indigo-400" />
            </div>
          </div>

          <h1 className="text-2xl font-extrabold text-white tracking-tight">CivicLens Console</h1>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px] font-bold uppercase tracking-wider mt-2">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span>Authenticated Operations Portal</span>
          </div>
        </div>

        {/* Notifications Banners */}
        {infoMsg && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-start space-x-2.5 shadow-lg shadow-emerald-950/20">
            <ShieldCheck className="h-4 w-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <span>{infoMsg}</span>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-semibold flex items-start space-x-2.5 shadow-lg shadow-red-950/20">
            <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {!requiresMfa ? (
            <>
              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                  Staff Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="operator@civiclens.gov.in"
                    className="input-field pl-10 w-full font-medium"
                    autoFocus
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="input-field pl-10 w-full font-medium"
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="animate-in fade-in duration-300 space-y-4">
              <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-200 text-xs font-medium flex items-center gap-3">
                <KeyRound className="h-5 w-5 text-indigo-400 flex-shrink-0" />
                <span>Multi-Factor Security Challenge: Enter the 6-Digit OTP sent to your staff email.</span>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 text-center">
                  6-Digit Email OTP Verification Code
                </label>
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="• • • • • •"
                  className="w-full py-3.5 bg-slate-950 border border-indigo-500/40 rounded-xl text-center text-2xl font-mono font-bold tracking-[0.6em] text-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-inner"
                  autoFocus
                />
              </div>

              <div className="text-center pt-1">
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={resendLoading}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 disabled:opacity-50 transition-colors"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${resendLoading ? 'animate-spin' : ''}`} />
                  Resend Email OTP Code
                </button>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full py-3.5 text-sm font-bold mt-4 flex items-center justify-center space-x-2"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <span>{requiresMfa ? 'Verify & Enter Console' : 'Sign In to Console'}</span>
            )}
          </button>
        </form>

        <div className="mt-8 pt-4 border-t border-slate-800/80 text-center">
          <p className="text-[11px] text-slate-500 font-medium">
            Protected by CivicLens Multi-Tenant RBAC Security Architecture.
          </p>
        </div>
      </div>
    </div>
  );
}
