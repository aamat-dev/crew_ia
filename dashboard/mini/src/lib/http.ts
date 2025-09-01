import { v4 as uuidv4 } from 'uuid';
import { getApiUrl, getApiKey } from '../store/settings';

interface HttpResult<T> {
  data: T | null;
  error: Error | null;
  requestId: string;
}

const ERROR_MESSAGES: Record<number, string> = {
  400: 'Requête invalide',
  401: 'Non autorisé',
  403: 'Interdit',
  404: 'Introuvable',
  500: 'Erreur serveur',
};

function showToast(message: string): void {
  window.alert(message);
}

async function fetchClient<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<HttpResult<T>> {
  const base = getApiUrl();
  const requestId =
    globalThis.crypto?.randomUUID?.() ?? uuidv4();

  const headers: Record<string, string> = {
    'X-Request-ID': requestId,
    'Content-Type': 'application/json',
  };

  const apiKey = getApiKey();
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`;

  try {
    const res = await fetch(base + path, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (res.ok) {
      const data = (await res.json()) as T;
      return { data, error: null, requestId };
    }

    const message = ERROR_MESSAGES[res.status] || `Erreur ${res.status}`;
    showToast(message);
    return { data: null, error: new Error(message), requestId };
  } catch (err) {
    showToast('Erreur réseau');
    return { data: null, error: err as Error, requestId };
  }
}

export function getJSON<T>(path: string): Promise<HttpResult<T>> {
  return fetchClient<T>('GET', path);
}

export function postJSON<T>(
  path: string,
  body: unknown,
): Promise<HttpResult<T>> {
  return fetchClient<T>('POST', path, body);
}

export function patchJSON<T>(
  path: string,
  body: unknown,
): Promise<HttpResult<T>> {
  return fetchClient<T>('PATCH', path, body);
}

export { fetchClient };
