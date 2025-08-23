// Gestion des variables d'environnement côté front

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
).replace(/\/+$/, '');

const rawTimeout = Number(import.meta.env.VITE_API_TIMEOUT_MS);
export const API_TIMEOUT_MS =
  Number.isFinite(rawTimeout) && rawTimeout > 0 ? rawTimeout : 15000;

export const DEMO_API_KEY =
  String(import.meta.env.VITE_DEMO_API_KEY ?? '').trim() || undefined;

export default { API_BASE_URL, API_TIMEOUT_MS, DEMO_API_KEY };
