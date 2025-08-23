import type { JSX, ReactNode } from 'react';
import { createContext, useContext, useEffect, useState } from 'react';
import { DEMO_API_KEY } from '../config/env';

let currentApiKey: string | undefined;

export const getCurrentApiKey = (): string | undefined => currentApiKey;
export const setCurrentApiKey = (k?: string): void => {
  currentApiKey = k;
};

export type ApiKeyState = {
  apiKey: string;
  useEnvKey: boolean;
};
export type ApiKeyActions = {
  setApiKey: (k: string) => void;
  setUseEnvKey: (v: boolean) => void;
  reset: () => void;
};
export type ApiKeyContextValue = ApiKeyState & ApiKeyActions;

const defaultState: ApiKeyState = { apiKey: '', useEnvKey: false };

const ApiKeyContext = createContext<ApiKeyContextValue | null>(null);

export const ApiKeyProvider = ({
  children,
}: {
  children: ReactNode;
}): JSX.Element => {
  const [apiKey, setApiKey] = useState<string>(defaultState.apiKey);
  const [useEnvKey, setUseEnvKey] = useState<boolean>(defaultState.useEnvKey);

  useEffect(() => {
    setCurrentApiKey(useEnvKey ? DEMO_API_KEY : apiKey || undefined);
  }, [apiKey, useEnvKey]);

  const reset = (): void => {
    setApiKey(defaultState.apiKey);
    setUseEnvKey(defaultState.useEnvKey);
  };

  return (
    <ApiKeyContext.Provider
      value={{ apiKey, useEnvKey, setApiKey, setUseEnvKey, reset }}
    >
      {children}
    </ApiKeyContext.Provider>
  );
};

export const useApiKey = (): ApiKeyContextValue => {
  const ctx = useContext(ApiKeyContext);
  if (!ctx) {
    throw new Error('useApiKey must be used within an ApiKeyProvider');
  }
  return ctx;
};
