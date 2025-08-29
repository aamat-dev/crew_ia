import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('config/env', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllEnvs();
    localStorage.clear();
  });

  it('utilise la valeur de l\'env par défaut', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://env-url');
    const { getApiBaseUrl } = await import('../../config/env');
    expect(getApiBaseUrl()).toBe('http://env-url');
  });

  it('utilise la valeur sauvegardée', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://env-url');
    const { getApiBaseUrl, setApiBaseUrl } = await import('../../config/env');
    setApiBaseUrl('http://override/');
    expect(getApiBaseUrl()).toBe('http://override');
  });

  it('retourne le fallback local', async () => {
    const { getApiBaseUrl } = await import('../../config/env');
    expect(getApiBaseUrl()).toBe('http://localhost:8000');
  });
});
