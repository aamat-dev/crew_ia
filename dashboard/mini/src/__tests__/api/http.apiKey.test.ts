import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { fetchJson } from '../../api/http';

describe('fetchJson API key', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    vi.stubEnv('VITE_API_KEY', '');
    vi.stubEnv('VITE_DEMO_API_KEY', '');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("ajoute l'en-tête quand la clé existe", async () => {
    localStorage.setItem('apiKey', 'abc');
    const mock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }));
    global.fetch = mock as unknown as typeof fetch;
    await fetchJson('/runs');
    const headers = (mock.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers['X-API-Key']).toBe('abc');
  });

  it("n'ajoute pas l'en-tête quand la clé est absente", async () => {
    const mock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }));
    global.fetch = mock as unknown as typeof fetch;
    await fetchJson('/runs');
    const headers = (mock.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers['X-API-Key']).toBeUndefined();
  });
});
