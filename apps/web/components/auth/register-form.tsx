'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/auth-context';
import { requestOtp, verifyOtp } from '@/lib/api/auth';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Alert } from '@/components/ui/alert';
import { ShieldCheck, UserPlus, Mail, Lock, Phone, ArrowRight, CheckCircle2, User } from 'lucide-react';

export function RegisterForm() {
  const router = useRouter();
  const { registerUser, loginWithOtp } = useAuth();

  // Tab state: 'email' | 'phone'
  const [method, setMethod] = useState<'email' | 'phone'>('email');

  // Common mandatory field
  const [fullName, setFullName] = useState('');

  // Email form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Phone form state
  const [phone, setPhone] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState('');

  // Common UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Email OTP state
  const [emailOtpSent, setEmailOtpSent] = useState(false);
  const [emailOtpCode, setEmailOtpCode] = useState('');

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const cleanName = fullName.trim();
    if (!cleanName || cleanName.length < 2) {
      setError('Please enter your full legal name.');
      return;
    }

    const cleanEmail = email.trim();
    if (!cleanEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanEmail)) {
      setError('Please enter a valid email address.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      if (!emailOtpSent) {
        // Step 1: Request 6-digit Email OTP
        await requestOtp(cleanEmail);
        setEmailOtpSent(true);
        setSuccess(`Verification code dispatched to ${cleanEmail}. Enter the code below to finalize your registration.`);
      } else {
        // Step 2: Verify 6-digit Email OTP and complete registration
        const cleanCode = emailOtpCode.trim();
        if (!/^\d{6}$/.test(cleanCode)) {
          setError('Please enter the 6-digit verification code.');
          setIsLoading(false);
          return;
        }

        try {
          await verifyOtp(cleanEmail, cleanCode);
        } catch (otpErr: any) {
          setError(otpErr.message || 'Invalid or expired OTP verification code.');
          setIsLoading(false);
          return;
        }

        await registerUser(cleanEmail, password);
        setSuccess(`Welcome ${cleanName}! Account verified & created successfully! Redirecting...`);
        setTimeout(() => {
          router.push('/dashboard');
        }, 1000);
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed. This email may already be registered.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendPhoneOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanName = fullName.trim();
    if (!cleanName || cleanName.length < 2) {
      setError('Please enter your full legal name.');
      return;
    }

    const cleanPhone = phone.trim();
    if (!/^\d{10}$/.test(cleanPhone)) {
      setError('Please enter a valid 10-digit mobile number.');
      return;
    }

    setIsLoading(true);
    try {
      await requestOtp(cleanPhone);
      setOtpSent(true);
      setSuccess(`Verification code dispatched to +91 ${cleanPhone}`);
    } catch (err: any) {
      setError(err.message || 'Failed to send OTP verification code.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyPhoneOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const cleanName = fullName.trim();
    if (!cleanName || cleanName.length < 2) {
      setError('Please enter your full legal name.');
      return;
    }

    const cleanCode = otpCode.trim();
    if (!/^\d{6}$/.test(cleanCode)) {
      setError('Please enter the 6-digit verification code.');
      return;
    }

    setIsLoading(true);
    try {
      await loginWithOtp(phone.trim(), cleanCode);
      setSuccess(`Welcome ${cleanName}! Phone verified successfully! Redirecting...`);
      setTimeout(() => {
        router.push('/dashboard');
      }, 1000);
    } catch (err: any) {
      setError(err.message || 'Invalid or expired OTP code.');
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
        <h1 className="text-2xl font-bold text-slate-900">Create Citizen Account</h1>
        <p className="text-sm text-slate-500 mt-1">
          Register to discover schemes, verify eligibility &amp; track applications.
        </p>
      </div>

      {/* Auth Method Selector Tabs */}
      <div className="flex bg-slate-100 p-1 rounded-xl mb-6">
        <button
          type="button"
          onClick={() => {
            setMethod('email');
            setError(null);
            setSuccess(null);
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
            setSuccess(null);
          }}
          className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all flex items-center justify-center gap-1.5 ${
            method === 'phone'
              ? 'bg-white text-blue-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Phone className="w-3.5 h-3.5" />
          Mobile Number OTP
        </button>
      </div>

      {error && <Alert type="error" className="mb-4">{error}</Alert>}
      {success && <Alert type="success" className="mb-4">{success}</Alert>}

      {method === 'email' ? (
        <form onSubmit={handleEmailSubmit} className="space-y-4">
          {!emailOtpSent ? (
            <>
              <Input
                label="Full Legal Name *"
                type="text"
                placeholder="e.g. Aakib Ahmad Bhat"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                autoFocus
              />

              <Input
                label="Email Address *"
                type="email"
                placeholder="citizen@example.gov.in"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <Input
                label="Password *"
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />

              <Input
                label="Confirm Password *"
                type="password"
                placeholder="••••••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />

              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200/60 text-xs text-slate-600 space-y-1">
                <div className="font-semibold text-slate-700 mb-1">Mandatory Security Verification:</div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>A 6-digit Email OTP code will be sent to verify your address.</span>
                </div>
              </div>

              <Button type="submit" className="w-full py-3" isLoading={isLoading}>
                <UserPlus className="w-4 h-4 mr-2" />
                Send OTP &amp; Register Account
              </Button>
            </>
          ) : (
            <div className="space-y-4 animate-in fade-in duration-300">
              <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg text-xs text-blue-800 flex items-center justify-between">
                <span>OTP dispatched to: <strong>{email}</strong></span>
                <button
                  type="button"
                  onClick={() => {
                    setEmailOtpSent(false);
                    setEmailOtpCode('');
                    setError(null);
                  }}
                  className="text-blue-600 underline font-semibold text-xs"
                >
                  Change
                </button>
              </div>

              <Input
                label="Enter 6-Digit Email Verification Code *"
                type="text"
                placeholder="123456"
                value={emailOtpCode}
                onChange={(e) => setEmailOtpCode(e.target.value.replace(/\D/g, ''))}
                maxLength={6}
                required
                autoFocus
              />

              <Button type="submit" className="w-full py-3" isLoading={isLoading}>
                <ShieldCheck className="w-4 h-4 mr-2" />
                Verify OTP &amp; Complete Registration
              </Button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={async () => {
                    setError(null);
                    setSuccess(`A new 6-digit OTP verification code has been dispatched to ${email}`);
                    try {
                      await requestOtp(email.trim());
                    } catch (err: any) {}
                  }}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                >
                  Resend Email OTP Code
                </button>
              </div>
            </div>
          )}
        </form>
      ) : (
        !otpSent ? (
          <form onSubmit={handleSendPhoneOtp} className="space-y-4">
            <Input
              label="Full Legal Name *"
              type="text"
              placeholder="e.g. Aakib Ahmad Bhat"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              autoFocus
            />

            <Input
              label="Mobile Number (10 Digits) *"
              type="tel"
              placeholder="e.g. 9876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              maxLength={10}
              required
            />

            <Button type="submit" className="w-full py-3" isLoading={isLoading}>
              <Phone className="w-4 h-4 mr-2" />
              Send Verification OTP
            </Button>
          </form>
        ) : (
          <form onSubmit={handleVerifyPhoneOtp} className="space-y-4">
            <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg text-xs text-blue-800 flex items-center justify-between">
              <span>OTP sent to: <strong>+91 {phone}</strong></span>
              <button
                type="button"
                onClick={() => {
                  setOtpSent(false);
                  setOtpCode('');
                  setError(null);
                }}
                className="text-blue-600 underline font-semibold text-xs"
              >
                Change
              </button>
            </div>

            <Input
              label="Enter 6-Digit OTP Code *"
              type="text"
              placeholder="123456"
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value)}
              maxLength={6}
              required
              autoFocus
            />

            <Button type="submit" className="w-full py-3" isLoading={isLoading}>
              <ShieldCheck className="w-4 h-4 mr-2" />
              Verify &amp; Complete Registration
            </Button>

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={async () => {
                  setError(null);
                  setSuccess(`A new 6-digit OTP verification code has been dispatched to +91 ${phone}`);
                  try {
                    await requestOtp(phone.trim());
                  } catch (err: any) {}
                }}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
              >
                Resend Mobile OTP Code
              </button>
            </div>
          </form>
        )
      )}

      <div className="mt-6 pt-4 border-t border-slate-100 text-center text-sm text-slate-600">
        Already have a citizen account?{' '}
        <Link href="/login" className="font-semibold text-blue-600 hover:text-blue-800 hover:underline">
          Sign In Here
        </Link>
      </div>
    </div>
  );
}
