import { v4 as uuidv4 } from 'uuid';
import { getApiBaseUrl, API_TIMEOUT_MS } from '../config/env';
import { getCurrentApiKey } from '../state/getApiKey';

export class ApiError extends Error {
  status: number;
  requestId: string;
  body?: unknown;

  constructor(
    message: string,
    status: number,
    requestId: string,
    body?: unknown,
  ) {
    super(message);
    this.status = status;
    this.requestId = requestId;
    this.body = body;
  }
}

export interface FetchOpts {
  query?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
}

export async function fetchJson<T>(
  path: string,
  opts: FetchOpts = {},
): Promise<{ data: T; headers: Headers; requestId: string }> {
  const url = new URL(getApiBaseUrl() + path);
  if (opts.query) {
    for (const [key, value] of Object.entries(opts.query)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const requestId = uuidv4();
  const headers: Record<string, string> = {};
  const apiKey = getCurrentApiKey();
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }

  const timeoutCtrl = new AbortController();
  const timeoutId = setTimeout(() => timeoutCtrl.abort(), API_TIMEOUT_MS);
  if (opts.signal) {
    if (opts.signal.aborted) {
      timeoutCtrl.abort();
    } else {
      opts.signal.addEventListener('abort', () => timeoutCtrl.abort(), {
        once: true,
      });
    }
  }

  const fetchOnce = () =>
    fetch(url.toString(), {
      headers,
      signal: timeoutCtrl.signal,
    });

  const maxRetries = 2;
  const backoff = [200, 500];
  let attempt = 0;
  while (true) {
    try {
      const res = await fetchOnce();
      if (res.ok) {
        clearTimeout(timeoutId);
        const data = (await res.json()) as T;
        return { data, headers: res.headers, requestId };
      }
      let body: unknown;
      const ct = res.headers.get('content-type');
      if (ct && ct.includes('application/json')) {
        try {
          body = await res.json();
        } catch {
          body = undefined;
        }
      }
      if (
        attempt < maxRetries &&
        (res.status === 429 || (res.status >= 500 && res.status < 600))
      ) {
        const delay = backoff[attempt] ?? backoff[backoff.length - 1];
        attempt++;
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }
      clearTimeout(timeoutId);
      throw new ApiError(
        `API Error ${res.status}`,
        res.status,
        requestId,
        body,
      );
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }
}
export async function postJson<T, B = unknown>(
  path: string,
  body: B,
  opts: FetchOpts = {},
): Promise<{ data: T; requestId: string }> {
  const url = new URL(getApiBaseUrl() + path);
  if (opts.query) {
    for (const [key, value] of Object.entries(opts.query)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  const requestId = uuidv4();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const apiKey = getCurrentApiKey();
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  const timeoutCtrl = new AbortController();
  const timeoutId = setTimeout(() => timeoutCtrl.abort(), API_TIMEOUT_MS);
  if (opts.signal) {
    if (opts.signal.aborted) {
      timeoutCtrl.abort();
    } else {
      opts.signal.addEventListener('abort', () => timeoutCtrl.abort(), {
        once: true,
      });
    }
  }
  try {
    const res = await fetch(url.toString(), {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: timeoutCtrl.signal,
    });
    const ct = res.headers.get('content-type');
    const data = ct && ct.includes('application/json') ? await res.json() : undefined;
    if (!res.ok) {
      throw new ApiError(`API Error ${res.status}`, res.status, requestId, data);
    }
    return { data: data as T, requestId };
  } finally {
    clearTimeout(timeoutId);
  }
}
