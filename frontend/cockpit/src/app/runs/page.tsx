"use client";

import { Timeline } from "@/components/Timeline";
import { Input } from "@/components/ds/Input";
import { useState } from "react";

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
  const [name, setName] = useState("");
  return (
    <main role="main" className="p-6 space-y-6">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">Runs</h1>

      {/* Barre de filtres */}
      <section aria-label="Filtres des runs" className="flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor="run-name">Nom ou ID</label>
        <div className="hidden w-full max-w-sm items-center gap-2 rounded-2xl border border-slate-700 bg-[#2A2D36] px-3 py-2 shadow-[inset_0_2px_6px_rgba(255,255,255,0.04)] sm:flex">
          <Input id="run-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom ou ID" className="w-full border-0 bg-transparent p-0 text-slate-100 placeholder:text-slate-400 focus-visible:ring-0" />
        </div>
      </section>

      <Timeline />
    </main>
  );
}
