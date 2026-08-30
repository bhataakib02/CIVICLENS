import { apiClient } from './client';
import { AccountInfo, TokenPair } from '@/types/api';

export async function loginEmail(email: string, password: string): Promise<TokenPair> {
  return apiClient<TokenPair>('/auth/login', {
    method: 'POST',
    body: { email, password },
    skipAuth: true,
  });
}

export async function logoutAccount(all = false): Promise<void> {
  return apiClient<void>(`/auth/logout?all=${all}`, {
    method: 'POST',
  });
}

export async function getAccount(): Promise<AccountInfo> {
  return apiClient<AccountInfo>('/me/account');
}

export async function requestOtp(target: string): Promise<void> {
  return apiClient<void>('/auth/otp/request', {
    method: 'POST',
    body: { phone_number: target },
    skipAuth: true,
  });
}

export async function verifyOtp(target: string, code: string): Promise<TokenPair> {
  return apiClient<TokenPair>('/auth/otp/verify', {
    method: 'POST',
    body: { phone_number: target, code },
    skipAuth: true,
  });
}
