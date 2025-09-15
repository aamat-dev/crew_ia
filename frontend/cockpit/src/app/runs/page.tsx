"use client";

import { Timeline } from "@/components/Timeline";

interface RunListItem {
  id: string;
  title: string;
  status: string;
  started_at?: string;
  ended_at?: string | null;
}

interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  links?: Record<string, string> | null;
}

export default function RunsPage() {
  return (
    <main role="main" className="p-6 space-y-6">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Runs</h1>
      <Timeline />
    </main>
  );
}
