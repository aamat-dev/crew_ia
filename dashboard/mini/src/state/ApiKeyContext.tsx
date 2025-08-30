import type { JSX, ReactNode } from 'react';
import { createContext, useContext, useMemo, useState } from 'react';

export type ApiKeyContextValue = {
  apiKey: string;
  setApiKey: (k: string) => void;
  useEnvKey: boolean;
};

const ApiKeyContext = createContext<ApiKeyContextValue | null>(null);

export function ApiKeyProvider({ children }: { children: ReactNode }): JSX.Element {
  const envKey = (
    (import.meta.env.VITE_API_KEY as string | undefined) ||
    (import.meta.env.VITE_DEMO_API_KEY as string | undefined) ||
    ''
  ).trim();
  const stored = localStorage.getItem('apiKey') || '';
  const [apiKey, setApiKeyState] = useState<string>(stored || envKey);
  const [useEnvKey, setUseEnvKey] = useState<boolean>(!stored && !!envKey);

  const setApiKey = (k: string): void => {
    const value = k.trim();
    if (value) {
      localStorage.setItem('apiKey', value);
      setApiKeyState(value);
      setUseEnvKey(false);
    } else {
      localStorage.removeItem('apiKey');
      const fallback = (
        (import.meta.env.VITE_API_KEY as string | undefined) ||
        (import.meta.env.VITE_DEMO_API_KEY as string | undefined) ||
        ''
      ).trim();
      setApiKeyState(fallback);
      setUseEnvKey(!!fallback);
    }
  };

  const value = useMemo(
    () => ({ apiKey, setApiKey, useEnvKey }),
    [apiKey, useEnvKey],
  );

  return <ApiKeyContext.Provider value={value}>{children}</ApiKeyContext.Provider>;
}

export function useApiKey(): ApiKeyContextValue {
  const ctx = useContext(ApiKeyContext);
  if (!ctx) throw new Error('useApiKey must be used within an ApiKeyProvider');
  return ctx;
}
