import 'whatwg-fetch';
import { describe, expect, it, vi } from 'vitest';
import * as client from '../../api/client';
import { ApiError } from '../../api/http';

const okBackend = { items: [], total: 0, limit: 1, offset: 0 };

describe('client API', () => {
  it('mappe correctement les paramètres de requête', async () => {
    const mock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(okBackend), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    global.fetch = mock as unknown as typeof fetch;
    await client.listRuns({
      page: 2,
      pageSize: 10,
      status: ['queued', 'running', 'succeeded'],
      dateFrom: '2024-01-01',
      dateTo: '2024-01-31',
      title: 'test',
    });
    const url = new URL(mock.mock.calls[0][0] as string);
    expect(url.searchParams.get('page')).toBe('2');
    expect(url.searchParams.get('page_size')).toBe('10');
    expect(url.searchParams.get('status')).toBe('pending,running,completed');
    expect(url.searchParams.get('date_from')).toBe('2024-01-01');
    expect(url.searchParams.get('date_to')).toBe('2024-01-31');
    expect(url.searchParams.get('title')).toBe('test');
  });

  it('convertit meta backend vers PageMeta', async () => {
    const mock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          items: [
            {
              id: '1',
              title: 't',
              status: 'pending',
              started_at: null,
              ended_at: null,
            },
          ],
          total: 80,
          limit: 50,
          offset: 50,
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    );
    global.fetch = mock as unknown as typeof fetch;
    const res = await client.listRuns({ page: 2, pageSize: 50 });
    expect(res.meta).toEqual({ page: 2, page_size: 50, total: 80 });
    expect(res.items[0].status).toBe('queued');
  });

  it('propage le signal', async () => {
    const mock = vi.fn(
      (_: string, opts: RequestInit) =>
        new Promise((_, reject) => {
          opts.signal?.addEventListener('abort', () =>
            reject(new DOMException('Aborted', 'AbortError')),
          );
        }),
    );
    global.fetch = mock as unknown as typeof fetch;
    const ctrl = new AbortController();
    const prom = client.getRun('1', { signal: ctrl.signal });
    ctrl.abort();
    await expect(prom).rejects.toThrow();
  });

  it('lève ApiError structuré', async () => {
    const mock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'nope' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    global.fetch = mock as unknown as typeof fetch;
    let error: unknown;
    try {
      await client.getRun('42');
    } catch (e) {
      error = e;
    }
    expect(error).toBeInstanceOf(ApiError);
    const err = error as ApiError;
    expect(err.status).toBe(400);
    expect(err.body).toEqual({ detail: 'nope' });
    expect(err.requestId).toBeTruthy();
  });
});
