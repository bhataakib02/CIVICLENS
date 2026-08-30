'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { AccountInfo } from '@/types/api';
import { tokenStore } from './tokens';
import { loginEmail, logoutAccount, getAccount } from '../api/auth';

interface AuthContextType {
  account: AccountInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [account, setAccount] = useState<AccountInfo | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchAccount = useCallback(async () => {
    const token = tokenStore.getAccessToken();
    if (!token) {
      setAccount(null);
      setIsLoading(false);
      return;
    }

    try {
      const acc = await getAccount();
      if (acc.role === 'citizen') {
        // Citizens are not allowed to log into the Admin / CSC Operations Console
        tokenStore.clearTokens();
        setAccount(null);
      } else {
        setAccount(acc);
      }
    } catch (err) {
      tokenStore.clearTokens();
      setAccount(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAccount();
  }, [fetchAccount]);

  const loginHandler = async (email: string, pass: string) => {
    setIsLoading(true);
    try {
      const tokens = await loginEmail(email, pass);
      tokenStore.setTokens(tokens.access_token, tokens.refresh_token);
      const acc = await getAccount();
      if (acc.role === 'citizen') {
        tokenStore.clearTokens();
        setAccount(null);
        throw new Error('Access denied. Citizens cannot access the Admin Console.');
      }
      setAccount(acc);
    } catch (err) {
      tokenStore.clearTokens();
      setAccount(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logoutHandler = async () => {
    try {
      await logoutAccount();
    } catch (err) {
      // Ignore
    } finally {
      tokenStore.clearTokens();
      setAccount(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        account,
        isAuthenticated: !!account,
        isLoading,
        login: loginHandler,
        logout: logoutHandler,
        refreshAccount: fetchAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
