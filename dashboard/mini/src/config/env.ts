// Gestion des variables d'environnement côté front

const STORAGE_KEY = 'apiBaseUrl';

export const DEFAULT_API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
).replace(/\/+$/, '');

export const getApiBaseUrl = (): string =>
  (localStorage.getItem(STORAGE_KEY) ?? DEFAULT_API_BASE_URL).replace(/\/+$/, '');

export const setApiBaseUrl = (url: string): void => {
  const clean = url.trim().replace(/\/+$/, '');
  if (clean) localStorage.setItem(STORAGE_KEY, clean);
  else localStorage.removeItem(STORAGE_KEY);
};

const rawTimeout = Number(import.meta.env.VITE_API_TIMEOUT_MS);
export const API_TIMEOUT_MS =
  Number.isFinite(rawTimeout) && rawTimeout > 0 ? rawTimeout : 15000;

export const DEMO_API_KEY =
  String(import.meta.env.VITE_DEMO_API_KEY ?? '').trim() || undefined;

const rawFbThreshold = Number(import.meta.env.VITE_FEEDBACK_CRITICAL_THRESHOLD);
export const FEEDBACK_CRITICAL_THRESHOLD =
  Number.isFinite(rawFbThreshold) ? rawFbThreshold : 60;

export default {
  getApiBaseUrl,
  setApiBaseUrl,
  DEFAULT_API_BASE_URL,
  API_TIMEOUT_MS,
  DEMO_API_KEY,
};
