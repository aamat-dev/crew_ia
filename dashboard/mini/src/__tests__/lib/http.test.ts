import 'whatwg-fetch';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('uuid', () => ({ v4: vi.fn(() => 'uuid-lib') }));
import { v4 as uuidv4 } from 'uuid';
import { getJSON } from '../../lib/http';

describe('X-Request-ID', () => {
  const realCrypto = globalThis.crypto;
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    window.alert = vi.fn();
    localStorage.clear();
    localStorage.setItem('apiUrl', 'https://api.test');
    global.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    Object.defineProperty(globalThis, 'crypto', {
      value: realCrypto,
      configurable: true,
    });
  });

  it('utilise crypto.randomUUID quand disponible', async () => {
    const rnd = vi.fn(() => 'crypto-id');
    Object.defineProperty(globalThis, 'crypto', {
      value: { randomUUID: rnd },
      configurable: true,
    });
    fetchMock.mockResolvedValue(
      new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );
    const res = await getJSON('/foo');
    expect(rnd).toHaveBeenCalled();
    expect(res.requestId).toBe('crypto-id');
    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers['X-Request-ID']).toBe('crypto-id');
  });

  it("bascule sur uuid.v4 quand crypto.randomUUID absent", async () => {
    Object.defineProperty(globalThis, 'crypto', {
      value: undefined,
      configurable: true,
    });
    fetchMock.mockResolvedValue(
      new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );
    const res = await getJSON('/bar');
    const v4 = uuidv4 as unknown as ReturnType<typeof vi.fn>;
    expect(v4).toHaveBeenCalled();
    expect(res.requestId).toBe('uuid-lib');
    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers['X-Request-ID']).toBe('uuid-lib');
  });
});
