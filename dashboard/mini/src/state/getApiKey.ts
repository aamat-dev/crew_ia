export function getCurrentApiKey(): string {
  const stored = localStorage.getItem('apiKey') || '';
  if (stored) return stored;
  return (
    (import.meta.env.VITE_API_KEY as string | undefined) ||
    (import.meta.env.VITE_DEMO_API_KEY as string | undefined) ||
    ''
  ).trim();
}
