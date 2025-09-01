import { useState } from 'react';

export interface Settings {
  apiUrl: string;
  apiKey: string;
}

const URL_KEY = 'apiUrl';
const KEY_KEY = 'apiKey';

export function getApiUrl(): string {
  return localStorage.getItem(URL_KEY) || '';
}

export function getApiKey(): string {
  return localStorage.getItem(KEY_KEY) || '';
}

export function saveSettings({ apiUrl, apiKey }: Settings): void {
  localStorage.setItem(URL_KEY, apiUrl);
  localStorage.setItem(KEY_KEY, apiKey);
}

export function useSettings(): [Settings, (s: Settings) => void] {
  const [state, setState] = useState<Settings>({
    apiUrl: getApiUrl(),
    apiKey: getApiKey(),
  });

  const update = (s: Settings): void => {
    saveSettings(s);
    setState(s);
  };

  return [state, update];
}
