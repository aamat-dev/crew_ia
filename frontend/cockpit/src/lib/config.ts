// Small runtime config helpers for client-side API access

// Base URL côté client; peut être surchargé par localStorage pour changer d'environnement sans rebuild
export const API_URL: string =
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "");

// Rôle courant (RBAC). Par défaut: viewer. Peut être surchargé via .env ou localStorage.
const ENV_ROLE = process.env.NEXT_PUBLIC_ROLE || "viewer";

function getLocalStorageItem(key: string): string | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    const value = window.localStorage.getItem(key);
    return value ?? undefined;
  } catch {
    return undefined;
  }
}

export function getRuntimeApiUrl(): string {
  // Permettre un override runtime via localStorage pour le sélecteur d'environnement
  const override = getLocalStorageItem("cockpit-api-url");
  return override && override.trim() ? override : API_URL;
}

export function getRuntimeRole(): string {
  // Permettre un override runtime du rôle (dev/demo)
  const override = getLocalStorageItem("cockpit-role");
  return (override && override.trim()) || ENV_ROLE;
}

// Optional demo API key to hit protected endpoints in dev environments
export const API_KEY: string | undefined = process.env.NEXT_PUBLIC_API_KEY || undefined;

// App name (brand) configurable via env
export const APP_NAME: string = process.env.NEXT_PUBLIC_APP_NAME || "Oria";

export function resolveApiUrl(path: string): string {
  const base = getRuntimeApiUrl();
  if (!base) return path; // laisse échouer clairement si non configuré
  if (!path.startsWith("/")) return `${base}/${path}`;
  return `${base}${path}`;
}

export function defaultApiHeaders(): Record<string, string> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (API_KEY) headers["X-API-Key"] = API_KEY;
  const role = getRuntimeRole();
  if (role) headers["X-Role"] = role;
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (tz) headers["X-Timezone"] = tz;
  } catch {
    // ignore
  }
  return headers;
}
