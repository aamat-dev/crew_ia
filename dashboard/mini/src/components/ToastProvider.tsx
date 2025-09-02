import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
  type JSX,
} from 'react';

interface Toast {
  id: number;
  message: string;
  type?: 'success' | 'error';
}

interface ToastContextValue {
  add: (msg: string, type?: 'success' | 'error') => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const ToastProvider = ({ children }: { children: ReactNode }): JSX.Element => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const add = useCallback((message: string, type?: 'success' | 'error') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  return (
    <ToastContext.Provider value={{ add }}>
      {children}
      <div aria-live="assertive" style={{ position: 'fixed', top: 0, right: 0 }}>
        {toasts.map((t) => (
          <div
            key={t.id}
            className="toast"
            style={{
              margin: '4px',
              padding: '8px',
              background: t.type === 'error' ? '#fdd' : '#dfd',
              border: '1px solid #ccc',
            }}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ((msg: string, type?: 'success' | 'error') => void) => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx.add;
};

export default ToastProvider;
