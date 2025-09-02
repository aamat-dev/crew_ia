"use client";
import { useEffect } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { queryClient, setQueryErrorNotifier } from "@/lib/queryClient";
import { ThemeProvider } from "./ThemeProvider";
import { ToastProvider, useToast } from "./ds/Toast";

function ToastBridge() {
  const toast = useToast();
  useEffect(() => {
    setQueryErrorNotifier((msg) => toast(msg, "error"));
  }, [toast]);
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastProvider>
          <ToastBridge />
          {children}
          {process.env.NODE_ENV === "development" && (
            <ReactQueryDevtools initialIsOpen={false} />
          )}
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default Providers;
