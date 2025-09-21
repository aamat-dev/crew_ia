"use client";
import type { ComponentType, ReactNode } from "react";
import { useEffect, useState } from "react";
import { HydrationBoundary, QueryClientProvider } from "@tanstack/react-query";
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

type DevtoolsComponent = ComponentType<{ initialIsOpen?: boolean }>;

export function Providers({ children }: { children: ReactNode }) {
  const [Devtools, setDevtools] = useState<DevtoolsComponent | null>(null);

  useEffect(() => {
    if (process.env.NODE_ENV === "development") {
      import("@tanstack/react-query-devtools").then((d) =>
        setDevtools(() => d.ReactQueryDevtools)
      );
    }
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <HydrationBoundary state={null}>
        <ThemeProvider>
          <ToastProvider>
            <ToastBridge />
            {children}
            {Devtools && <Devtools initialIsOpen={false} />}
          </ToastProvider>
        </ThemeProvider>
      </HydrationBoundary>
    </QueryClientProvider>
  );
}

export default Providers;
