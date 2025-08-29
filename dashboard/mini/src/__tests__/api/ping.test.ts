import { describe, it, expect, vi } from 'vitest';
import { pingApi } from '../../api/ping';
import { setCurrentApiKey } from '../../state/ApiKeyContext';

describe('pingApi', () => {
  it('retourne ok=true et le status quand la connexion réussit', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce(new Response('ok', { status: 200 }));
    await expect(pingApi('http://test')).resolves.toEqual({ ok: true, status: 200 });
  });

  it("retourne ok=false en cas d'erreur réseau", async () => {
    global.fetch = vi.fn().mockRejectedValueOnce(new Error('fail'));
    await expect(pingApi('http://fail')).resolves.toEqual({ ok: false });
  });

  it('ajoute l\'en-tête X-API-Key si une clé est définie', async () => {
    setCurrentApiKey('key');
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response('ok', { status: 200 }));
    global.fetch = fetchMock;
    await pingApi('http://test');
    expect(fetchMock).toHaveBeenCalledWith('http://test/runs?limit=1', {
      headers: { 'X-API-Key': 'key' },
    });
    setCurrentApiKey(undefined);
  });
});
