export type MockRun = {
  id: string;
  title: string;
  status: "queued" | "running" | "completed" | "failed" | "paused";
  startedAt?: string;
  endedAt?: string | null;
};

let runs: MockRun[] = [
  { id: "R-1001", title: "Import données", status: "running", startedAt: new Date(Date.now() - 5 * 60_000).toISOString(), endedAt: null },
  { id: "R-1000", title: "Nettoyage cache", status: "completed", startedAt: new Date(Date.now() - 60 * 60_000).toISOString(), endedAt: new Date(Date.now() - 55 * 60_000).toISOString() },
  { id: "R-999", title: "Rebuild index", status: "failed", startedAt: new Date(Date.now() - 2 * 60 * 60_000).toISOString(), endedAt: new Date(Date.now() - 119 * 60_000).toISOString() },
  { id: "R-998", title: "Analyse logs", status: "queued" },
  { id: "R-997", title: "Sauvegarde", status: "paused", startedAt: new Date(Date.now() - 20 * 60_000).toISOString(), endedAt: null },
];

export function listRuns(filters?: { status?: string[]; q?: string }): MockRun[] {
  let data = runs.slice();
  if (filters?.status && filters.status.length) {
    const allow = new Set(filters.status);
    data = data.filter((r) => allow.has(r.status));
  }
  if (filters?.q) {
    const q = filters.q.toLowerCase();
    data = data.filter((r) => r.id.toLowerCase().includes(q) || r.title.toLowerCase().includes(q));
  }
  // order: running -> queued -> paused -> failed -> completed, newest first by startedAt/id
  const weight: Record<MockRun["status"], number> = { running: 0, queued: 1, paused: 2, failed: 3, completed: 4 } as const;
  data.sort((a, b) => {
    const wa = weight[a.status];
    const wb = weight[b.status];
    if (wa !== wb) return wa - wb;
    const ta = a.startedAt ? Date.parse(a.startedAt) : 0;
    const tb = b.startedAt ? Date.parse(b.startedAt) : 0;
    if (tb !== ta) return tb - ta;
    return b.id.localeCompare(a.id);
  });
  return data;
}

export function pauseRun(id: string): MockRun | null {
  const r = runs.find((x) => x.id === id);
  if (!r) return null;
  if (r.status === "running") r.status = "paused";
  return r;
}

export function resumeRun(id: string): MockRun | null {
  const r = runs.find((x) => x.id === id);
  if (!r) return null;
  if (r.status === "paused" || r.status === "queued") r.status = "running";
  return r;
}

