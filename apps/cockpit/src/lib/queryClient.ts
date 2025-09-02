import { QueryClient, QueryCache, onlineManager } from '@tanstack/react-query';

let notifyError: ((msg: string) => void) | null = null;
export const setQueryErrorNotifier = (fn: (msg: string) => void): void => {
  notifyError = fn;
};

if (typeof window !== 'undefined') {
  onlineManager.setEventListener((setOnline) => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    return () => {
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
    };
  });
  onlineManager.setOnline(navigator.onLine);
}

const retry = (failureCount: number, error: unknown): boolean => {
  const err = error as { status?: number; response?: { status?: number } };
  const status = err.status ?? err.response?.status;
  if (status && status >= 400 && status < 500) return false;
  return failureCount < 5;
};

const retryDelay = (attempt: number) => {
  const base = Math.min(10_000, 500 * 2 ** attempt);
  return base / 2 + Math.random() * (base / 2);
};

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (err) => {
      notifyError?.((err as Error).message);
    },
  }),
  defaultOptions: {
    queries: {
      retry,
      retryDelay,
      staleTime: 30_000,
      gcTime: 5 * 60 * 1000,
      networkMode: 'online',
    },
  },
});

export default queryClient;
