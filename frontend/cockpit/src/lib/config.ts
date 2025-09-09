// Small runtime config helpers for client-side API access

export const API_URL: string =
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "");

// Optional demo API key to hit protected endpoints in dev environments
export const API_KEY: string | undefined = process.env.NEXT_PUBLIC_API_KEY || undefined;

export function resolveApiUrl(path: string): string {
  if (!API_URL) return path; // let it fail clearly if not configured
  if (!path.startsWith("/")) return `${API_URL}/${path}`;
  return `${API_URL}${path}`;
}

export function defaultApiHeaders(): Record<string, string> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (tz) headers["X-Timezone"] = tz;
  } catch {
    // ignore
  }
  return headers;
}

