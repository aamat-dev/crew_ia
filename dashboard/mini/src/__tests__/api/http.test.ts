import 'whatwg-fetch';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchJson, ApiError } from '../../api/http';

describe('fetchJson', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('aborte après le timeout', async () => {
    vi.useFakeTimers();
    const mock = vi.fn(
      (_: string, opts: RequestInit) =>
        new Promise((_, reject) => {
          opts.signal?.addEventListener('abort', () =>
            reject(new DOMException('Aborted', 'AbortError')),
          );
        }),
    );
    global.fetch = mock as unknown as typeof fetch;
    const prom = fetchJson('/runs');
    const assertion = expect(prom).rejects.toThrow();
    await vi.advanceTimersByTimeAsync(15000);
    await assertion;
    vi.useRealTimers();
  });

  it('peut être annulé via un signal externe', async () => {
    const ctrl = new AbortController();
    const mock = vi.fn(
      (_: string, opts: RequestInit) =>
        new Promise((_, reject) => {
          opts.signal?.addEventListener('abort', () =>
            reject(new DOMException('Aborted', 'AbortError')),
          );
        }),
    );
    global.fetch = mock as unknown as typeof fetch;
    const prom = fetchJson('/runs', { signal: ctrl.signal });
    ctrl.abort();
    await expect(prom).rejects.toThrow();
  });

  it('retry sur 500 puis succès', async () => {
    vi.useFakeTimers();
    const mock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response('err', {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      );
    global.fetch = mock as unknown as typeof fetch;
    const prom = fetchJson<{ ok: boolean }>('/runs');
    await vi.advanceTimersByTimeAsync(200);
    const res = await prom;
    expect(res.data.ok).toBe(true);
    expect(mock).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });

  it('pas de retry sur 401', async () => {
    const mock = vi.fn().mockResolvedValue(
      new Response('no', {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    global.fetch = mock as unknown as typeof fetch;
    await expect(fetchJson('/runs')).rejects.toBeInstanceOf(ApiError);
    expect(mock).toHaveBeenCalledTimes(1);
  });
});
