'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { CitizenProfile } from '@/types/api';
import { tokenStore } from './tokens';
import { verifyOtp, loginWithEmail, registerUser, logout } from '../api/auth';
import { getProfile } from '../api/me';

interface AuthContextType {
  user: CitizenProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginWithOtp: (phoneNumber: string, code: string) => Promise<void>;
  loginWithEmail: (email: string, password: string) => Promise<void>;
  registerUser: (email: string, password: string) => Promise<void>;
  logoutUser: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CitizenProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchProfile = useCallback(async () => {
    const token = tokenStore.getAccessToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const profile = await getProfile();
      setUser(profile);
    } catch (err) {
      tokenStore.clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const loginWithOtpHandler = async (phoneNumber: string, code: string) => {
    setIsLoading(true);
    try {
      const tokens = await verifyOtp(phoneNumber, code);
      tokenStore.setTokens(tokens.access_token, tokens.refresh_token);
      const profile = await getProfile();
      setUser(profile);
    } catch (err) {
      tokenStore.clearTokens();
      setUser(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithEmailHandler = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const tokens = await loginWithEmail(email, password);
      tokenStore.setTokens(tokens.access_token, tokens.refresh_token);
      const profile = await getProfile();
      setUser(profile);
    } catch (err) {
      tokenStore.clearTokens();
      setUser(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const registerUserHandler = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const tokens = await registerUser(email, password);
      tokenStore.setTokens(tokens.access_token, tokens.refresh_token);
      const profile = await getProfile();
      setUser(profile);
    } catch (err) {
      tokenStore.clearTokens();
      setUser(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logoutUserHandler = async () => {
    try {
      await logout();
    } catch (err) {
      // Ignore logout errors
    } finally {
      tokenStore.clearTokens();
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        loginWithOtp: loginWithOtpHandler,
        loginWithEmail: loginWithEmailHandler,
        registerUser: registerUserHandler,
        logoutUser: logoutUserHandler,
        refreshProfile: fetchProfile
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
