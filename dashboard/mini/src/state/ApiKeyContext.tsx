import { createContext, ReactNode, useContext, useState } from "react";

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

const defaultState: ApiKeyState = { apiKey: "", useEnvKey: false };

const ApiKeyContext = createContext<ApiKeyContextValue | null>(null);

export const ApiKeyProvider = ({ children }: { children: ReactNode }): JSX.Element => {
  const [apiKey, setApiKey] = useState<string>(defaultState.apiKey);
  const [useEnvKey, setUseEnvKey] = useState<boolean>(defaultState.useEnvKey);

  const reset = (): void => {
    setApiKey(defaultState.apiKey);
    setUseEnvKey(defaultState.useEnvKey);
  };

  return (
    <ApiKeyContext.Provider value={{ apiKey, useEnvKey, setApiKey, setUseEnvKey, reset }}>
      {children}
    </ApiKeyContext.Provider>
  );
};

export const useApiKey = (): ApiKeyContextValue => {
  const ctx = useContext(ApiKeyContext);
  if (!ctx) {
    throw new Error("useApiKey must be used within an ApiKeyProvider");
  }
  return ctx;
};
