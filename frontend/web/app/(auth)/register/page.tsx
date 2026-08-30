'use client';

import React from 'react';
import { RegisterForm } from '@/components/auth/register-form';

export default function RegisterPage() {
  return (
    <div className="w-full flex justify-center py-6">
      <RegisterForm />
    </div>
  );
}
