"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { clearApiToken, loadApiToken, setApiToken } from '@/lib/api';

interface AuthTokenContextValue {
  token: string;
  hasToken: boolean;
  saveToken: (token: string) => void;
  clearToken: () => void;
}

const AuthTokenContext = createContext<AuthTokenContextValue | undefined>(undefined);

export function AuthTokenProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState('');

  useEffect(() => {
    const initial = loadApiToken() ?? '';
    setToken(initial);
  }, []);

  const saveToken = useCallback((nextToken: string) => {
    const trimmed = nextToken.trim();
    setApiToken(trimmed);
    setToken(trimmed);
  }, []);

  const clearToken = useCallback(() => {
    clearApiToken();
    setToken('');
  }, []);

  const value = useMemo(
    () => ({ token, hasToken: token.length > 0, saveToken, clearToken }),
    [token, saveToken, clearToken]
  );

  return <AuthTokenContext.Provider value={value}>{children}</AuthTokenContext.Provider>;
}

export function useAuthToken() {
  const context = useContext(AuthTokenContext);
  if (!context) {
    throw new Error('useAuthToken must be used within AuthTokenProvider');
  }
  return context;
}
