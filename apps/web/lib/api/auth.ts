import { apiClient } from './client';
import { TokenPair } from '@/types/api';

export async function requestOtp(phoneNumber: string): Promise<void> {
  await apiClient('/auth/otp/request', {
    method: 'POST',
    skipAuth: true,
    body: { phone_number: phoneNumber }
  });
}

export async function verifyOtp(phoneNumber: string, code: string): Promise<TokenPair> {
  return apiClient<TokenPair>('/auth/otp/verify', {
    method: 'POST',
    skipAuth: true,
    body: { phone_number: phoneNumber, code }
  });
}

export async function loginWithEmail(email: string, password: string): Promise<TokenPair> {
  return apiClient<TokenPair>('/auth/login', {
    method: 'POST',
    skipAuth: true,
    body: { email, password }
  });
}

export async function logout(all = false): Promise<void> {
  await apiClient(`/auth/logout?all=${all}`, {
    method: 'POST'
  });
}
