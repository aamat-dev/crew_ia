export type Criticity = "critical" | "major" | "minor";

export interface FeedbackItem {
  id: string;
  title: string;
  criticity: Criticity;
  createdAt: string;
  runId?: string;
  sourceAnchor?: string;
  summary?: string;
  resolved?: boolean;
}

let items: FeedbackItem[] = [
  {
    id: "F-1001",
    title: "Réponse LLM incohérente",
    criticity: "critical",
    createdAt: new Date(Date.now() - 5 * 60_000).toISOString(),
    runId: "R-1001",
    sourceAnchor: "#step-3",
    summary: "La sortie ne respecte pas le schéma JSON attendu.",
    resolved: false,
  },
  {
    id: "F-1000",
    title: "Latence élevée observée",
    criticity: "major",
    createdAt: new Date(Date.now() - 60 * 60_000).toISOString(),
    runId: "R-999",
    sourceAnchor: "#metrics",
    summary: "Temps de réponse > 5s pour plusieurs requêtes.",
    resolved: false,
  },
  {
    id: "F-999",
    title: "Suggestion mineure UI",
    criticity: "minor",
    createdAt: new Date(Date.now() - 2 * 60 * 60_000).toISOString(),
    runId: "R-998",
    sourceAnchor: "#notes",
    summary: "Padding insuffisant sur le panneau latéral.",
    resolved: true,
  },
];

export function listFeedbacks(filters?: { q?: string; criticity?: Criticity[] }): FeedbackItem[] {
  let data = items.slice();
  if (filters?.criticity && filters.criticity.length) {
    const allow = new Set(filters.criticity);
    data = data.filter((i) => allow.has(i.criticity));
  }
  if (filters?.q) {
    const q = filters.q.toLowerCase();
    data = data.filter(
      (i) => i.id.toLowerCase().includes(q) || i.title.toLowerCase().includes(q) || (i.summary || "").toLowerCase().includes(q),
    );
  }
  // order: unresolved first, then by criticity (critical, major, minor), then newest
  const weight: Record<Criticity, number> = { critical: 0, major: 1, minor: 2 } as const;
  data.sort((a, b) => {
    if ((a.resolved ? 1 : 0) !== (b.resolved ? 1 : 0)) return (a.resolved ? 1 : 0) - (b.resolved ? 1 : 0);
    const wa = weight[a.criticity];
    const wb = weight[b.criticity];
    if (wa !== wb) return wa - wb;
    return Date.parse(b.createdAt) - Date.parse(a.createdAt);
  });
  return data;
}

export function resolveFeedback(id: string): FeedbackItem | null {
  const it = items.find((x) => x.id === id);
  if (!it) return null;
  it.resolved = true;
  return it;
}

export function lastCritical(): FeedbackItem | null {
  return listFeedbacks({ criticity: ["critical"] })[0] || null;
}

