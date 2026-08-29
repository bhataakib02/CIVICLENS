'use client';

import React, { useState } from 'react';
import { LoginForm } from '@/components/auth/login-form';
import { OtpForm } from '@/components/auth/otp-form';

export default function LoginPage() {
  const [phone, setPhone] = useState<string | null>(null);

  return (
    <div className="w-full flex justify-center">
      {phone ? (
        <OtpForm phone={phone} onBack={() => setPhone(null)} />
      ) : (
        <LoginForm onOtpSent={(p) => setPhone(p)} />
      )}
    </div>
  );
}
