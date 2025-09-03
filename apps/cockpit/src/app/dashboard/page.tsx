"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

function DashboardContent() {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <p data-testid="dashboard-welcome">Bienvenue sur le cockpit.</p>
    </main>
  );
}

export default function DashboardPage() {
  const [client] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={client}>
      <DashboardContent />
    </QueryClientProvider>
  );
}
