import { getCurrentApiKey } from '../state/getApiKey';

export async function pingApi(
  baseUrl: string,
): Promise<{ ok: boolean; status?: number }> {
  const clean = baseUrl.replace(/\/+$/, '');
  const headers: Record<string, string> = {};
  const apiKey = getCurrentApiKey();
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  try {
    const res = await fetch(`${clean}/runs?limit=1`, { headers });
    return { ok: res.ok, status: res.status };
  } catch {
    return { ok: false };
  }
}

export default pingApi;
