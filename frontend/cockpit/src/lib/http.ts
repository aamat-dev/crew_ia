export interface FetchOptions {
  timeoutMs?: number;
  signal?: AbortSignal;
  headers?: Record<string, string>;
}

export async function fetchJson<T>(
  url: string,
  { timeoutMs = 10_000, signal, headers }: FetchOptions = {},
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener('abort', () => controller.abort(), { once: true });
  }
  try {
    const res = await fetch(url, {
      headers: { Accept: 'application/json', ...(headers || {}) },
      signal: controller.signal,
    });
    const text = await res.text();
    if (!res.ok) {
      interface HttpError extends Error {
        status?: number;
      }
      const err: HttpError = new Error(res.statusText || `HTTP ${res.status}`);
      err.status = res.status;
      throw err;
    }
    try {
      return JSON.parse(text) as T;
    } catch {
      throw new Error('Invalid JSON');
    }
  } finally {
    clearTimeout(timer);
  }
}
