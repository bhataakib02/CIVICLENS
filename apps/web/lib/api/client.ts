import { tokenStore } from '../auth/tokens';
import { normalizeApiError, NetworkError } from './errors';

const getApiBaseUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
};

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: any;
  skipAuth?: boolean;
  isMultipart?: boolean;
}

let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: any) => void }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token!);
    }
  });
  failedQueue = [];
};

async function refreshAccessToken(): Promise<string> {
  const refreshToken = tokenStore.getRefreshToken();
  if (!refreshToken) {
    throw normalizeApiError(401, { error: { message: 'No refresh token available', code: 'UNAUTHORIZED' } });
  }

  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}/auth/token/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  if (!response.ok) {
    tokenStore.clearTokens();
    const data = await response.json().catch(() => ({}));
    throw normalizeApiError(response.status, data);
  }

  const data = await response.json();
  tokenStore.setTokens(data.access_token, data.refresh_token || refreshToken);
  return data.access_token;
}

export async function apiClient<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { skipAuth = false, isMultipart = false, headers: customHeaders, body, ...customOptions } = options;
  const baseUrl = getApiBaseUrl();
  const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

  const headers: Record<string, string> = { ...((customHeaders as Record<string, string>) || {}) };

  if (!skipAuth) {
    const token = tokenStore.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  if (!isMultipart && !headers['Content-Type'] && body && typeof body !== 'string') {
    headers['Content-Type'] = 'application/json';
  }

  let requestBody: any = body;
  if (body && !isMultipart && typeof body !== 'string' && !(body instanceof FormData)) {
    requestBody = JSON.stringify(body);
  }

  try {
    let response = await fetch(url, {
      ...customOptions,
      headers,
      body: requestBody
    });

    // Handle token refresh on 401
    if (response.status === 401 && !skipAuth && !endpoint.includes('/auth/')) {
      if (isRefreshing) {
        try {
          const newToken = await new Promise<string>((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          });
          headers['Authorization'] = `Bearer ${newToken}`;
          response = await fetch(url, { ...customOptions, headers, body: requestBody });
        } catch (err) {
          throw err;
        }
      } else {
        isRefreshing = true;
        try {
          const newToken = await refreshAccessToken();
          processQueue(null, newToken);
          headers['Authorization'] = `Bearer ${newToken}`;
          response = await fetch(url, { ...customOptions, headers, body: requestBody });
        } catch (refreshErr) {
          processQueue(refreshErr, null);
          throw refreshErr;
        } finally {
          isRefreshing = false;
        }
      }
    }

    if (response.status === 204) {
      return {} as T;
    }

    const contentType = response.headers.get('content-type') || '';

    if (!response.ok) {
      let errorData: any = {};
      if (contentType.includes('application/json')) {
        errorData = await response.json().catch(() => ({}));
      } else {
        const text = await response.text().catch(() => '');
        errorData = { error: { message: text || response.statusText } };
      }
      throw normalizeApiError(response.status, errorData);
    }

    if (contentType.includes('application/pdf') || contentType.includes('octet-stream')) {
      return (await response.blob()) as unknown as T;
    }

    if (contentType.includes('application/json')) {
      return await response.json();
    }

    return (await response.text()) as unknown as T;
  } catch (err: any) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new NetworkError('Unable to connect to CivicLens service. Please check your network.');
    }
    throw err;
  }
}
