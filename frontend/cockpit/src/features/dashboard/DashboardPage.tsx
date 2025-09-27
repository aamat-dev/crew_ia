"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { APP_NAME } from "@/lib/config";
import { useQuery } from "@tanstack/react-query";
import { fetchRuns, fetchAgents, fetchFeedbacks, fetchTasks, type RunListItem, type TaskListItem } from "@/lib/api";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import {
  Activity,
  Clock,
  Calendar,
  Filter,
  Plus,
  ChevronsUpDown,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Play,
  Repeat2,
  Copy,
  X,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  PieChart,
  Pie,
  Cell,
  Brush,
  ReferenceDot,
} from "recharts";

type StatusName = "success" | "failed" | "canceled";
type DrawerPanel = "plan" | "exec" | "logs";

type SeverityItem = {
  name: "Critique" | "Majeur" | "Mineur";
  value: number;
  color: string;
};

type RunRow = {
  id: string;
  task: string;
  agent: string;
  status: StatusName;
  started: string;
  duration: number;
  delta: number;
};

const ACCENT = "#4FD1C5";
const ORGANIC = "#84cc16";

const tabs = ["Dashboard", "Tâches", "Outils"] as const;
const ranges = ["24h", "7j", "30j"] as const;
type TabName = (typeof tabs)[number];
type Range = (typeof ranges)[number];

type SeverityName = "Critique" | "Majeur" | "Mineur" | "Tous";

// Alimenté par l'API
function toStatusName(status: string): StatusName {
  const v = status.toLowerCase();
  if (v.includes("fail") || v === "error") return "failed";
  if (v.includes("cancel")) return "canceled";
  return "success";
}

// Liste de tâches alimentée par l'API (onglet "Opérations")

function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={
        "rounded-2xl bg-[#141821] border border-white/5 shadow-[0_8px_32px_rgba(0,0,0,0.35)] transition-all duration-300 hover:translate-y-[-1px] hover:shadow-[0_12px_40px_rgba(0,0,0,0.45)] " +
        className
      }
    >
      {children}
    </div>
  );
}

function StatBadge({ color, children }: { color: string; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium" style={{ background: `${color}22`, color }}>
      {children}
    </span>
  );
}

function KpiCard({
  title,
  value,
  icon,
  delta,
  suffix,
  trend,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  delta?: string;
  suffix?: string;
  trend?: { d: string; v: number }[];
}) {
  return (
    <Panel className="p-4">
      <div className="flex items-start justify-between">
        <div className="text-[13px] text-white/70">{title}</div>
        <div className="text-white/60">{icon}</div>
      </div>
      <div className="mt-1 flex items-baseline gap-2">
        <div className="text-3xl font-semibold tracking-tight">{value}</div>
        {suffix ? <div className="text-sm text-white/60">{suffix}</div> : null}
        {delta ? <StatBadge color={delta.startsWith("-") ? "#ef4444" : ACCENT}>{delta}</StatBadge> : null}
      </div>
      {trend ? (
        <div className="mt-3 h-10">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trend} margin={{ left: 0, right: 0, top: 4, bottom: 0 }}>
              <YAxis hide domain={[0, "dataMax + 5"]} />
              <XAxis hide dataKey="d" />
              <Line type="monotone" dataKey="v" stroke={ACCENT} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </Panel>
  );
}

function StatusPill({ status }: { status: StatusName }) {
  const map: Record<StatusName, { label: string; color: string; Icon: typeof CheckCircle2 }> = {
    success: { label: "Succès", color: "#22c55e", Icon: CheckCircle2 },
    failed: { label: "Échec", color: "#ef4444", Icon: XCircle },
    canceled: { label: "Annulé", color: "#f59e0b", Icon: AlertTriangle },
  };
  const { label, color, Icon } = map[status];
  return (
    <div className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs" style={{ background: `${color}22`, color }}>
      <Icon size={14} /> {label}
    </div>
  );
}

function Radial({ value, target = 95 }: { value: number; target?: number }) {
  const data = [{ value, target }];
  return (
    <div className="relative h-[140px] w-[140px]">
      <ResponsiveContainer>
        <RadialBarChart data={data} innerRadius="68%" outerRadius="100%" startAngle={90} endAngle={-270}>
          <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
          <RadialBar dataKey="target" fill={ORGANIC} fillOpacity={0.25} cornerRadius={8} />
          <RadialBar dataKey="value" fill={ACCENT} cornerRadius={8} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex items-center justify-center text-center">
        <div>
          <div className="text-2xl font-semibold">{value}%</div>
          <div className="text-[11px] text-white/60">Objectif {target}%</div>
        </div>
      </div>
    </div>
  );
}

function SeverityDonut({
  data,
  onSelect,
  selected,
}: {
  data: SeverityItem[];
  onSelect?: (name: SeverityName) => void;
  selected?: SeverityName;
}) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const total = useMemo(() => data.reduce((a, d) => a + d.value, 0), [data]);

  const handleSelect = (name: SeverityName) => {
    onSelect?.(name);
  };

  return (
    <div className="relative h-[260px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <defs>
            {data.map((s, i) => (
              <linearGradient key={String(i)} id={`grad-${i}`} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={s.color} stopOpacity={0.95} />
                <stop offset="100%" stopColor={s.color} stopOpacity={0.4} />
              </linearGradient>
            ))}
          </defs>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius="70%"
            outerRadius="95%"
            paddingAngle={4}
            cornerRadius={10}
            isAnimationActive
            onMouseLeave={() => setActiveIndex(null)}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={`url(#grad-${index})`}
                stroke={activeIndex === index || selected === entry.name ? "#ffffff33" : "#00000000"}
                strokeWidth={activeIndex === index || selected === entry.name ? 2 : 0}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => handleSelect(selected === entry.name ? "Tous" : (entry.name as SeverityName))}
              />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-center">
        <div>
          <div className="text-xs text-white/60">Total feedbacks</div>
          <div className="text-2xl font-semibold">{total}</div>
          <div className="mt-1 text-xs text-white/60">
            {activeIndex !== null ? (
              <span style={{ color: data[activeIndex].color }}>
                {data[activeIndex].name} • {Math.round((data[activeIndex].value / total) * 100)}%
              </span>
            ) : selected && selected !== "Tous" ? (
              <span style={{ color: data.find((d) => d.name === selected)?.color }}>{selected}</span>
            ) : (
              <span>sur la période</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function TaskList({ tasks, onOpen, filter }: { tasks: any[]; onOpen: (id: string) => void; filter?: (task: any) => boolean }) {
  const data = filter ? tasks.filter(filter) : tasks;
  return (
    <Panel className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium text-white/80">Tâches</h2>
        <div className="text-xs text-white/60">{data.length} éléments</div>
      </div>
      <div className="max-h-[360px] overflow-auto rounded-xl border border-white/5">
        <table className="w-full text-sm">
          <thead className="sticky top-0 z-10 bg-white/5 text-left text-xs text-white/60 backdrop-blur">
            <tr>
              <th className="px-4 py-2">Tâche</th>
              <th className="px-4 py-2">Statut</th>
              <th className="px-4 py-2">MAJ</th>
              <th className="px-4 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.map((task, index) => (
              <tr key={task.id} className={index % 2 ? "bg-white/[0.02]" : ""}>
                <td className="px-4 py-2 font-medium text-white/90">{task.title}</td>
                <td className="px-4 py-2 text-white/80">{task.status}</td>
                <td className="px-4 py-2 text-white/70">{task.updatedAt}</td>
                <td className="px-4 py-2 text-right">
                  <button
                    className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]"
                    onClick={() => onOpen(task.id)}
                  >
                    Ouvrir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function TaskDetailDrawer({
  task,
  onClose,
  onValidate,
  onLaunch,
  onUpdatePlan,
  panel,
  setPanel,
}: {
  task: any;
  onClose: () => void;
  onValidate: () => void;
  onLaunch: () => void;
  onUpdatePlan: (nodes: any[]) => void;
  panel: DrawerPanel;
  setPanel: (panel: DrawerPanel) => void;
}) {
  return (
    <div className="fixed inset-0 z-40">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <aside className="absolute right-0 top-0 h-full w-[720px] border-l border-white/10 bg-[#0e1116] shadow-2xl">
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <div>
            <div className="text-xs text-white/60">{task.id}</div>
            <div className="text-lg font-semibold">{task.title}</div>
          </div>
          <button
            className="rounded-lg border border-white/10 bg-white/[0.04] p-2 hover:bg-white/[0.07]"
            onClick={onClose}
            aria-label="Fermer"
            type="button"
          >
            <X size={16} />
          </button>
        </div>

        <div className="flex gap-2 border-b border-white/10 px-5 py-2 text-sm">
          {(['plan', 'exec', 'logs'] as const).map((value) => (
            <button
              key={value}
              onClick={() => setPanel(value)}
              className={`${panel === value ? "text-[#0b0f14]" : "text-white/80 hover:text-white"} rounded-xl px-3 py-1.5`}
              style={panel === value ? { background: `linear-gradient(180deg, ${ACCENT}, ${ACCENT})` } : {}}
              type="button"
            >
              {value === "plan" ? "Plan" : value === "exec" ? "Exécution" : "Logs"}
            </button>
          ))}
          <span className="ml-auto inline-flex items-center gap-2 text-xs text-white/60">
            Statut : <span className="rounded-full bg-white/10 px-2 py-0.5">{task.status}</span>
          </span>
        </div>

        <div className="h-[calc(100%-160px)] overflow-auto p-5">
          {panel === "plan" ? (
            <div>
              <div className="mb-3 text-sm text-white/70">Éditez le plan puis validez.</div>
              <PlanEditorLite nodes={task.plan} onChange={onUpdatePlan} />
            </div>
          ) : null}
          {panel === "exec" ? <div className="text-sm text-white/70">Exécution en cours/à venir. (démo)</div> : null}
          {panel === "logs" ? <div className="text-sm text-white/70">Logs et livrables (démo).</div> : null}
        </div>

        <div className="flex items-center justify-between border-t border-white/10 px-5 py-4">
          <div className="text-xs text-white/60">Version du plan : v{task.planVersion}</div>
          <div className="flex items-center gap-2">
            <button
              onClick={onValidate}
              disabled={task.status !== "Plan à valider" && task.status !== "Brouillon"}
              className="rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white/90 enabled:hover:bg-white/[0.07] disabled:opacity-50"
              type="button"
            >
              Valider le plan
            </button>
            <button
              onClick={onLaunch}
              disabled={task.status !== "Validé"}
              className="rounded-xl px-3 py-2 text-sm font-medium text-[#0b0f14] disabled:opacity-50"
              style={{ background: `linear-gradient(90deg, ${ACCENT}, ${ORGANIC})` }}
              type="button"
            >
              <Play size={16} className="mr-1 inline" /> Lancer l'exécution
            </button>
          </div>
        </div>
      </aside>
    </div>
  );
}

function PlanEditorLite({ nodes, onChange }: { nodes: any[]; onChange: (nodes: any[]) => void }) {
  const [local, setLocal] = useState<any[]>(() => sortNodes(nodes));

  useEffect(() => {
    setLocal(sortNodes(nodes));
  }, [nodes]);

  const update = (next: any[]) => {
    const sorted = sortNodes(next);
    setLocal(sorted);
    onChange(sorted);
  };

  const addChild = (parentId: string | null) => {
    const id = `n${Math.random().toString(36).slice(2, 7)}`;
    const siblings = local.filter((node) => (parentId ? node.parentId === parentId : !node.parentId));
    const next: any[] = [
      ...local,
      { id, parentId: parentId ?? null, title: "Nouvelle étape", order: siblings.length },
    ];
    update(next);
  };

  const removeNode = (id: string) => {
    update(local.filter((node) => node.id !== id && node.parentId !== id));
  };

  const renameNode = (id: string, title: string) => {
    update(local.map((node) => (node.id === id ? { ...node, title } : node)));
  };

  const move = (id: string, dir: -1 | 1) => {
    const node = local.find((item) => item.id === id);
    if (!node) return;
    const siblings = local
      .filter((item) => (node.parentId ? item.parentId === node.parentId : !item.parentId))
      .sort((a, b) => a.order - b.order);
    const index = siblings.findIndex((item) => item.id === id);
    const swap = siblings[index + dir];
    if (!swap) return;
    const next = local.map((item) => {
      if (item.id === node.id) return { ...item, order: swap.order };
      if (item.id === swap.id) return { ...item, order: node.order };
      return item;
    });
    update(next);
  };

  const render = (parentId: string | null, depth = 0): React.ReactNode => {
    const items = local
      .filter((node) => (parentId ? node.parentId === parentId : !node.parentId))
      .sort((a, b) => a.order - b.order);

    return (
      <div>
        {items.map((node) => (
          <div
            key={node.id}
            className="group mb-1 flex items-center gap-2 rounded-lg px-2 py-1 hover:bg-white/5"
            style={{ marginLeft: depth * 16 }}
          >
            <div className="text-white/40">{depth > 0 ? "↳" : "•"}</div>
            <input
              value={node.title}
              onChange={(event) => renameNode(node.id, event.target.value)}
              className="w-full rounded-md border border-white/10 bg-transparent px-2 py-1 text-sm outline-none focus:border-white/20"
            />
            <div className="invisible ml-2 flex items-center gap-1 group-hover:visible">
              <button
                className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]"
                onClick={() => addChild(node.id)}
                type="button"
              >
                + sous-tâche
              </button>
              <button
                className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]"
                onClick={() => move(node.id, -1)}
                type="button"
              >
                ↑
              </button>
              <button
                className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]"
                onClick={() => move(node.id, 1)}
                type="button"
              >
                ↓
              </button>
              <button
                className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs text-red-300 hover:bg-white/[0.07]"
                onClick={() => removeNode(node.id)}
                type="button"
              >
                Supprimer
              </button>
            </div>
          </div>
        ))}
        <div style={{ marginLeft: depth * 16 }}>
          {depth === 0 ? (
            <button
              className="mt-1 rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]"
              onClick={() => addChild(null)}
              type="button"
            >
              + étape racine
            </button>
          ) : null}
        </div>
        {items.map((node) => (
          <div key={`${node.id}-children`}>{render(node.id, depth + 1)}</div>
        ))}
      </div>
    );
  };

  return <div>{render(null, 0)}</div>;
}

function sortNodes(nodes: any[]) {
  return [...nodes].sort((a, b) => {
    const parentCompare = (a.parentId ?? "").localeCompare(b.parentId ?? "");
    return parentCompare !== 0 ? parentCompare : a.order - b.order;
  });
}

function TabsBar({ tabs, active, onChange, counts }: { tabs: readonly string[]; active: string; onChange: (tab: string) => void; counts?: Record<string, number> }) {
  return (
    <div className="hidden items-center gap-1 rounded-2xl border border-white/10 bg-white/[0.04] p-1 md:flex">
      {tabs.map((tab) => (
        <TabButton key={tab} active={tab === active} onClick={() => onChange(tab)} count={counts?.[tab]}>
          {tab}
        </TabButton>
      ))}
    </div>
  );
}

function TabButton({ active, onClick, children, count }: { active?: boolean; onClick?: () => void; children: React.ReactNode; count?: number }) {
  return (
    <button
      onClick={onClick}
      className={`relative inline-flex items-center gap-2 rounded-xl px-3 py-1.5 text-sm transition-all ${active ? "text-[#0b0f14]" : "text-white/80 hover:text-white"}`}
      style={active ? { background: `linear-gradient(180deg, ${ACCENT}, ${ACCENT})`, boxShadow: "0 8px 20px rgba(0,0,0,.25)" } : {}}
      aria-current={active ? "page" : undefined}
      type="button"
    >
      {children}
      {typeof count === "number" ? <span className="rounded-full bg-white/10 px-1.5 py-0.5 text-[11px] text-white/80">{count}</span> : null}
    </button>
  );
}

function ToolbarButton({ icon, label, onClick }: { icon: React.ReactNode; label: string; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white/90 hover:bg-white/[0.07]"
      type="button"
    >
      {icon}
      <span>{label}</span>
      <ChevronsUpDown size={14} className="text-white/50" />
    </button>
  );
}

function IconButton({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <button
      title={title}
      className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] hover:bg-white/[0.07]"
      type="button"
    >
      {children}
    </button>
  );
}

function HealthPanel({
  apiStatus,
  apiLatencyMs,
  dbOk,
  orchStatus,
  orchUptime,
}: {
  apiStatus?: string;
  apiLatencyMs?: number;
  dbOk?: boolean;
  orchStatus?: string;
  orchUptime?: number;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
      <h2 className="mb-3 text-sm font-medium text-white/80">Santé système</h2>
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-xl border border-white/10 bg-white/[0.04] p-3">
          <div className="flex items-center justify-between text-xs text-white/60">
            <span>API</span>
            <CheckCircle2 size={16} className={apiStatus === "ok" ? "text-emerald-400" : "text-amber-400"} />
          </div>
          <div className="mt-1 text-lg font-semibold">{typeof apiLatencyMs === "number" ? `${apiLatencyMs} ms` : "—"}</div>
          <div className="text-[11px] text-white/60">Statut: {apiStatus ?? "?"}</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/[0.04] p-3">
          <div className="flex items-center justify-between text-xs text-white/60">
            <span>Base de données</span>
            {dbOk ? <CheckCircle2 size={16} className="text-emerald-400" /> : <XCircle size={16} className="text-red-400" />}
          </div>
          <div className="mt-1 text-lg font-semibold">{dbOk ? "OK" : "Degraded"}</div>
          <div className="text-[11px] text-white/60">Depuis /health</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/[0.04] p-3">
          <div className="flex items-center justify-between text-xs text-white/60">
            <span>Orchestrateur</span>
            {orchStatus === "ok" ? <CheckCircle2 size={16} className="text-emerald-400" /> : <AlertTriangle size={16} className="text-amber-400" />}
          </div>
          <div className="mt-1 text-lg font-semibold capitalize">{orchStatus ?? "?"}</div>
          <div className="text-[11px] text-white/60">Uptime: {typeof orchUptime === "number" ? `${Math.floor(orchUptime / 60)}m` : "—"}</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/[0.04] p-3">
          <div className="flex items-center justify-between text-xs text-white/60">
            <span>Serveur</span>
            <Activity size={16} className="text-white/50" />
          </div>
          <div className="mt-1 text-lg font-semibold">—</div>
          <div className="text-[11px] text-white/60">Réservé</div>
        </div>
      </div>
    </div>
  );
}

function nextOf<T>(cur: T, arr: readonly T[]): T {
  const index = arr.indexOf(cur);
  return arr[(index + 1) % arr.length];
}

function inferSeverityFromRun(run: RunRow): SeverityName {
  if (run.status === "failed") return "Critique";
  if (run.status === "canceled") return "Majeur";
  return "Mineur";
}

function formatSeconds(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}m${String(remainder).padStart(2, "0")}s`;
}

export function DashboardPage() {
  const tabs = ["Dashboard", "Tâches", "Outils"] as const;
  const ranges = ["24h", "7j", "30j"] as const;
  type Range = (typeof ranges)[number];
  type TabName = (typeof tabs)[number];

  const searchParams = useMemo(() => {
    if (typeof window === "undefined") return new URLSearchParams();
    return new URLSearchParams(window.location.search);
  }, []);

  const r0 = (searchParams.get("range") as Range) || "7j";
  const t0 = searchParams.get("tab");
  const s0 = (searchParams.get("severity") as SeverityName) || "Tous";
  const taskId0 = searchParams.get("taskId");
  const panel0 = (searchParams.get("panel") as DrawerPanel) || "plan";

  const initRange: Range = (ranges as readonly string[]).includes(r0) ? (r0 as Range) : "7j";
  const initTab: TabName = t0 && (tabs as readonly string[]).includes(t0) ? (t0 as TabName) : "Dashboard";

  const [range, setRange] = useState<Range>(initRange);
  const [selectedSeverity, setSelectedSeverity] = useState<SeverityName>(s0);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [tab, setTab] = useState<TabName>(initTab);
  const [openTaskId, setOpenTaskId] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const sp = new URLSearchParams(window.location.search);
    sp.set("range", range);
    sp.set("tab", tab);
    sp.set("severity", selectedSeverity);
    sp.delete("taskId");
    sp.delete("panel");
    const url = `${window.location.pathname}?${sp.toString()}`;
    window.history.replaceState({}, "", url);
  }, [range, selectedSeverity, tab]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const handler = () => {
      const sp = new URLSearchParams(window.location.search);
      const r = sp.get("range");
      const t = sp.get("tab");
      const p = null;
      const a = null;
      const s = sp.get("severity") as SeverityName | null;
      const tk = null;
      const pn = null;
      if (r && (ranges as readonly string[]).includes(r)) setRange(r as Range);
      if (t && (tabs as readonly string[]).includes(t)) setTab(t as TabName);
      if (s) setSelectedSeverity(s);
      setOpenTaskId(tk);
    };
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);

  // Fenêtre temporelle pour l'API selon le range sélectionné
  const fromDate = useMemo(() => {
    const now = new Date();
    const d = new Date(now);
    if (range === "24h") d.setDate(d.getDate() - 1);
    else if (range === "7j") d.setDate(d.getDate() - 7);
    else d.setDate(d.getDate() - 30);
    return d;
  }, [range]);
  const fromIso = useMemo(() => fromDate.toISOString(), [fromDate]);

  // Runs pour KPIs + timeline
  const runsQuery = useQuery({
    queryKey: ["dashboard:runs", { from: fromIso, range }],
    queryFn: ({ signal }) =>
      fetchRuns({ limit: range === "30j" ? 1000 : 500, orderBy: "started_at", orderDir: "desc", startedFrom: fromIso }, { signal }),
    refetchInterval: 30_000,
    staleTime: 30_000,
  });

  // Agents connectés
  const agentsQuery = useQuery({
    queryKey: ["dashboard:agents", { limit: 200 }],
    queryFn: ({ signal }) => fetchAgents({ limit: 200, orderBy: "name", orderDir: "asc" }, { signal }),
    staleTime: 60_000,
  });

  // Feedbacks pour la distribution de sévérité
  const feedbacksQuery = useQuery({
    queryKey: ["dashboard:feedbacks", { from: fromIso }],
    queryFn: ({ signal }) => fetchFeedbacks({ limit: 200, orderBy: "created_at", orderDir: "desc" }, { signal }),
    staleTime: 60_000,
  });

  // Tâches récentes
  const tasksQuery = useQuery({
    queryKey: ["dashboard:tasks", { limit: 20 }],
    queryFn: ({ signal }) => fetchTasks({ limit: 20, orderBy: "-updated_at" }, { signal }),
    staleTime: 30_000,
  });

  // Santé API
  const healthQuery = useQuery({
    queryKey: ["dashboard:health"],
    queryFn: async ({ signal }) => {
      const url = resolveApiUrl(`/health`);
      const t0 = (typeof performance !== "undefined" && performance.now) ? performance.now() : Date.now();
      const res = await fetch(url, { headers: { ...defaultApiHeaders(), Accept: "application/json" }, signal });
      const t1 = (typeof performance !== "undefined" && performance.now) ? performance.now() : Date.now();
      const latency_ms = Math.round(t1 - t0);
      let body: any = {};
      try { body = await res.json(); } catch {}
      if (!res.ok) {
        const message = (body && typeof body.detail === "string") ? body.detail : res.statusText || `HTTP ${res.status}`;
        throw new Error(message);
      }
      return { ...body, latency_ms } as { status?: string; db_ok?: boolean; uptime_s?: number; orchestrator?: { status?: string; uptime_s?: number }; latency_ms: number };
    },
    refetchInterval: 30_000,
    staleTime: 10_000,
  });

  // Mapping et calculs
  const recentRuns: RunRow[] = useMemo(() => {
    const items = runsQuery.data?.items ?? [];
    return items.slice(0, 20).map((r: RunListItem) => {
      const startedAt = r.started_at ? new Date(r.started_at) : null;
      const endedAt = r.ended_at ? new Date(r.ended_at) : null;
      const durationSec = startedAt && endedAt ? Math.max(0, Math.round((endedAt.getTime() - startedAt.getTime()) / 1000)) : 0;
      return {
        id: r.id,
        task: r.title || r.id,
        agent: "—",
        status: toStatusName(r.status),
        started: startedAt ? startedAt.toLocaleString() : "—",
        duration: durationSec,
        delta: 0,
      } as RunRow;
    });
  }, [runsQuery.data]);

  // Buckets de runs (jour ou heure)
  type Bucket = { d: string; start: Date; end: Date; success: number; failed: number; canceled: number };
  const runsBuckets: Bucket[] = useMemo(() => {
    const granularity: "hour" | "day" = range === "24h" ? "hour" : "day";
    const bucketCount = range === "30j" ? 30 : range === "7j" ? 7 : 24;
    const now = new Date();
    const buckets: Bucket[] = [];
    for (let i = bucketCount - 1; i >= 0; i--) {
      if (granularity === "day") {
        const start = new Date(now);
        start.setHours(0, 0, 0, 0);
        start.setDate(start.getDate() - i);
        const end = new Date(start);
        end.setHours(23, 59, 59, 999);
        const d = start.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });
        buckets.push({ d, start, end, success: 0, failed: 0, canceled: 0 });
      } else {
        const start = new Date(now);
        start.setMinutes(0, 0, 0);
        start.setHours(start.getHours() - i);
        const end = new Date(start);
        end.setMinutes(59, 59, 999);
        const d = `${String(start.getHours()).padStart(2, "0")}h`;
        buckets.push({ d, start, end, success: 0, failed: 0, canceled: 0 });
      }
    }
    const items = runsQuery.data?.items ?? [];
    for (const r of items) {
      if (!r.started_at) continue;
      const startedAt = new Date(r.started_at);
      for (const b of buckets) {
        if (startedAt >= b.start && startedAt <= b.end) {
          const s = toStatusName(r.status);
          b[s] += 1;
          break;
        }
      }
    }
    return buckets;
  }, [runsQuery.data, range]);

  const kpiTrend = useMemo(() => runsBuckets.map((b) => ({ d: b.d, v: b.success + b.failed + b.canceled })), [runsBuckets]);

  const successRate = useMemo(() => {
    const counts = runsBuckets.reduce(
      (acc, b) => {
        acc.success += b.success;
        acc.total += b.success + b.failed + b.canceled;
        return acc;
      },
      { success: 0, total: 0 }
    );
    if (counts.total === 0) return 0;
    return Math.round((counts.success / counts.total) * 100);
  }, [runsBuckets]);

  const medianDuration = useMemo(() => {
    const items = runsQuery.data?.items ?? [];
    const durations: number[] = [];
    for (const r of items) {
      if (!r.started_at || !r.ended_at) continue;
      const s = new Date(r.started_at).getTime();
      const e = new Date(r.ended_at).getTime();
      if (e > s) durations.push(Math.round((e - s) / 1000));
    }
    if (durations.length === 0) return "—";
    durations.sort((a, b) => a - b);
    const mid = Math.floor(durations.length / 2);
    const value = durations.length % 2 ? durations[mid] : Math.round((durations[mid - 1] + durations[mid]) / 2);
    return formatSeconds(value);
  }, [runsQuery.data]);

  const totalRuns = useMemo(() => runsBuckets.reduce((acc, b) => acc + b.success + b.failed + b.canceled, 0), [runsBuckets]);

  const severityData: SeverityItem[] = useMemo(() => {
    const data = feedbacksQuery.data?.items ?? [];
    const counts = { Critique: 0, Majeur: 0, Mineur: 0 } as Record<Exclude<SeverityName, "Tous">, number>;
    for (const f of data) {
      const score = typeof f.score === "number" ? f.score : undefined;
      const name: Exclude<SeverityName, "Tous"> = !score || score <= 40 ? "Critique" : score <= 70 ? "Majeur" : "Mineur";
      counts[name] += 1;
    }
    return [
      { name: "Critique", value: counts.Critique, color: "#ef4444" },
      { name: "Majeur", value: counts.Majeur, color: "#f59e0b" },
      { name: "Mineur", value: counts.Mineur, color: ACCENT },
    ];
  }, [feedbacksQuery.data]);

  const feedbackCount = useMemo(() => severityData.reduce((acc, item) => acc + item.value, 0), [severityData]);

  const tasksCount = tasksQuery.data?.items?.length ?? 0;

  const runsIndexed = useMemo(() => runsBuckets.map((day, index) => ({ ...day, index })), [runsBuckets]);
  const [xDomain, setXDomain] = useState<[number, number]>([0, 0]);
  useEffect(() => {
    setXDomain([0, Math.max(0, runsBuckets.length - 1)]);
  }, [runsBuckets.length]);

  const filteredRuns = useMemo(() => {
    if (selectedSeverity === "Tous") return recentRuns;
    return recentRuns.filter((run) => inferSeverityFromRun(run) === selectedSeverity);
  }, [selectedSeverity]);

  

  const anomalies = useMemo(() => {
    return runsIndexed.flatMap((day) => {
      const output: { x: number; y: number; color: string }[] = [];
      if (day.failed >= 3) output.push({ x: day.index, y: day.failed, color: "#ef4444" });
      if (day.success <= 5) output.push({ x: day.index, y: day.success, color: "#f59e0b" });
      return output;
    });
  }, [runsIndexed]);

  const clamp = (n: number, min: number, max: number) => Math.max(min, Math.min(max, n));

  const onBrushChange = (eventData: unknown) => {
    if (!eventData || typeof eventData !== "object") return;
    const startIndex = (eventData as { startIndex?: number }).startIndex;
    const endIndex = (eventData as { endIndex?: number }).endIndex;
    if (typeof startIndex === "number" && typeof endIndex === "number") {
      setXDomain([startIndex, endIndex]);
    }
  };

  const zoomIn = () => setXDomain(([start, end]) => (end - start > 1 ? [start + 1, end - 1] : [start, end]));
  const zoomOut = () =>
    setXDomain(([start, end]) => [clamp(start - 1, 0, runsBuckets.length - 2), clamp(end + 1, 1, runsBuckets.length - 1)]);
  const panLeft = () =>
    setXDomain(([start, end]) => [clamp(start - 1, 0, runsBuckets.length - 2), clamp(end - 1, 1, runsBuckets.length - 1)]);
  const panRight = () =>
    setXDomain(([start, end]) => [clamp(start + 1, 0, runsBuckets.length - 2), clamp(end + 1, 1, runsBuckets.length - 1)]);
  const resetZoom = () => setXDomain([0, Math.max(0, runsBuckets.length - 1)]);

  const tabCounts: Record<string, number> = {
    Tâches: tasksCount,
  };

  const handleCopy = async (id: string) => {
    try {
      await navigator.clipboard?.writeText(id);
      setCopiedId(id);
      setTimeout(() => {
        setCopiedId((prev) => (prev === id ? null : prev));
      }, 1200);
    } catch {
      /* noop */
    }
  };

  const openTask = (id: string) => {
    window.location.href = `/tasks/${id}`;
  };

  return (
    <div className="min-h-screen bg-[#0e1116] text-[#e9eef5]">
      <header className="relative sticky top-0 z-30 overflow-hidden border-b border-white/10 bg-[#0e1116]/80 backdrop-blur">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -top-24 left-1/4 h-48 w-[40rem] rounded-full blur-3xl" style={{ background: `${ACCENT}33` }} />
          <div className="absolute -top-28 right-1/6 h-40 w-[30rem] rounded-full blur-3xl" style={{ background: `${ORGANIC}22` }} />
        </div>

        <div className="mx-auto max-w-7xl px-6">
          <div className="flex items-center justify-between py-3">
            <div className="flex min-w-0 items-center gap-3">
              <div className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-gradient-to-br from-white/[0.08] to-white/[0.02] shadow-inner overflow-hidden">
                <img src="/lion.png" alt="Logo Oria" className="h-6 w-6 object-contain" />
                <div className="absolute -bottom-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full border border-white/10 bg-emerald-500/20 backdrop-blur">
                  <span className="h-2 w-2 rounded-full bg-emerald-300" />
                </div>
              </div>
              <div className="min-w-0">
                <h1 className="text-2xl font-semibold tracking-tight">{APP_NAME}</h1>
              </div>
            </div>

            <TabsBar tabs={tabs} active={tab} onChange={(value) => setTab(value as TabName)} counts={tabCounts} />

            <div className="flex items-center gap-2">
              <Link
                aria-label="Créer"
                href="/tasks/new"
                className="inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-[#0b0f14] shadow hover:opacity-90"
                style={{ background: `linear-gradient(90deg, ${ACCENT}, ${ORGANIC})` }}
              >
                <Plus size={16} /> Nouvelle tâche
              </Link>
            </div>
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] p-2">
            <ToolbarButton icon={<Calendar size={16} />} label={range} onClick={() => setRange(nextOf(range, ranges))} />
            {selectedSeverity !== "Tous" ? (
              <span className="ml-auto inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.06] px-2.5 py-1 text-xs text-white/80">
                Filtre: {selectedSeverity}
                <button
                  aria-label="Retirer filtre"
                  className="rounded-full p-0.5 hover:bg-white/10"
                  onClick={() => setSelectedSeverity("Tous")}
                  type="button"
                >
                  <X size={12} />
                </button>
              </span>
            ) : null}
          </div>

          <div className="mt-2 h-[2px] w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {tab === "Dashboard" ? (
          <div className="grid grid-cols-12 gap-5">
            <div className="col-span-12 gap-5 md:col-span-6 lg:col-span-3">
              <KpiCard title={`Runs (${range})`} value={totalRuns} icon={<Activity size={18} />} trend={kpiTrend} />
            </div>
            <div className="col-span-12 gap-5 md:col-span-6 lg:col-span-3">
              <KpiCard
                title="Agents connectés"
                value={(agentsQuery.data?.items ?? []).filter((a: any) => (a as { is_active?: boolean }).is_active).length}
                icon={<Activity size={18} />}
                
                trend={kpiTrend.map((item) => ({ d: item.d, v: Math.max(1, Math.round(item.v / 3)) }))}
              />
            </div>
            <div className="col-span-12 gap-5 md:col-span-6 lg:col-span-3">
              <Panel className="flex items-center justify-between p-4">
                <div>
                  <div className="text-[13px] text-white/70">Taux de succès</div>
                  <div className="mt-1 text-sm text-white/60">
                    Δ vs 7j : <span style={{ color: ACCENT }}>+3.2%</span>
                  </div>
                </div>
                <Radial value={successRate} target={95} />
              </Panel>
            </div>
            <div className="col-span-12 gap-5 md:col-span-6 lg:col-span-3">
              <KpiCard
                title="Durée médiane"
                value={medianDuration}
                icon={<Clock size={18} />}
                suffix="/ run"
                
                trend={kpiTrend.map((item) => ({ d: item.d, v: 20 + Math.max(5, 15 - (item.v % 10)) }))}
              />
            </div>

            <Panel className="col-span-12 lg:col-span-8 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-medium text-white/80">Runs par jour</h2>
                <div className="text-xs text-white/60">Moyenne mobile 7j</div>
              </div>
              <div className="mb-2 flex items-center gap-2 text-xs">
                <button onClick={panLeft} className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 hover:bg-white/[0.07]" type="button">
                  ◀
                </button>
                <button onClick={zoomOut} className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 hover:bg-white/[0.07]" type="button">
                  −
                </button>
                <button onClick={resetZoom} className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 hover:bg-white/[0.07]" type="button">
                  Reset
                </button>
                <button onClick={zoomIn} className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 hover:bg-white/[0.07]" type="button">
                  +
                </button>
                <button onClick={panRight} className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 hover:bg-white/[0.07]" type="button">
                  ▶
                </button>
                <span className="ml-auto text-white/50">Fenêtre: {xDomain[0]}–{xDomain[1]}</span>
              </div>
              <div className="h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={runsIndexed} margin={{ left: 6, right: 6, top: 6, bottom: 0 }}>
                    <defs>
                      <linearGradient id="s1" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="5%" stopColor={ACCENT} stopOpacity={0.7} />
                        <stop offset="95%" stopColor={ACCENT} stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#ffffff11" vertical={false} />
                  <XAxis dataKey="index" type="number" domain={xDomain} allowDecimals={false} tickFormatter={(index) => runsBuckets[index as number]?.d ?? ""} stroke="#99a6b2" fontSize={12} />
                    <YAxis stroke="#99a6b2" fontSize={12} />
                    <Tooltip contentStyle={{ background: "#0f131a", border: "1px solid #2a3140" }} />
                    <Area type="monotone" dataKey="success" stroke={ACCENT} fill="url(#s1)" strokeWidth={2} />
                    <Area type="monotone" dataKey="failed" stroke="#ef4444" fill="#ef444422" strokeWidth={2} />
                    <Area type="monotone" dataKey="canceled" stroke="#f59e0b" fill="#f59e0b22" strokeWidth={2} />
                    {anomalies.map((anomaly, idx) => (
                      <ReferenceDot key={String(idx)} x={anomaly.x} y={anomaly.y} r={4} fill={anomaly.color} stroke="#000000" strokeOpacity={0.25} isFront />
                    ))}
                    <Brush dataKey="index" height={18} travellerWidth={8} stroke="#ffffff33" onChange={onBrushChange} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Panel>

            <Panel className="col-span-12 lg:col-span-4 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-medium text-white/80">Feedbacks par sévérité</h2>
                <div className="flex gap-2 text-xs">
                  {severityData.map((severity) => (
                    <button
                      key={severity.name}
                      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 hover:bg-white/10"
                      style={{ background: `${severity.color}${selectedSeverity === severity.name ? "33" : "22"}`, color: severity.color }}
                      onClick={() => setSelectedSeverity(selectedSeverity === severity.name ? "Tous" : severity.name)}
                      aria-pressed={selectedSeverity === severity.name}
                      type="button"
                    >
                      <span className="h-1.5 w-1.5 rounded-full" style={{ background: severity.color }} /> {severity.name}
                    </button>
                  ))}
                </div>
              </div>
              <SeverityDonut data={Array.from(severityData)} selected={selectedSeverity} onSelect={setSelectedSeverity} />
            </Panel>

            <Panel className="col-span-12 lg:col-span-8 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-medium text-white/80">Derniers runs</h2>
                <div className="text-xs text-white/60">Cliquez un run pour détails</div>
              </div>
              <div className="max-h-[360px] overflow-auto rounded-xl border border-white/5">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 z-10 bg-white/5 text-left text-xs text-white/60 backdrop-blur">
                    <tr>
                      <th className="px-4 py-2">Run</th>
                      <th className="px-4 py-2">Tâche</th>
                      <th className="px-4 py-2">Agent</th>
                      <th className="px-4 py-2">Statut</th>
                      <th className="px-4 py-2">Durée</th>
                      <th className="px-4 py-2">Démarré</th>
                      <th className="px-4 py-2">Δ médiane</th>
                      <th className="px-4 py-2 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRuns.map((run, index) => (
                      <tr key={run.id} className={index % 2 ? "bg-white/[0.02]" : ""}>
                        <td className="px-4 py-2 font-medium text-white/90">
                          <button
                            className="inline-flex items-center gap-1 hover:underline"
                            onClick={() => handleCopy(run.id)}
                            aria-label={`Copier ${run.id}`}
                            title={copiedId === run.id ? "Copié !" : "Copier l'ID"}
                            type="button"
                          >
                            {run.id}
                            <Copy size={14} className="text-white/60" />
                          </button>
                        </td>
                        <td className="px-4 py-2">{run.task}</td>
                        <td className="px-4 py-2 text-white/80">{run.agent}</td>
                        <td className="px-4 py-2">
                          <StatusPill status={run.status} />
                        </td>
                        <td className="px-4 py-2">{run.duration ? formatSeconds(run.duration) : "—"}</td>
                        <td className="px-4 py-2 text-white/70">{run.started}</td>
                        <td className="px-4 py-2">
                          <StatBadge color={run.delta >= 0 ? ACCENT : "#ef4444"}>
                            {run.delta >= 0 ? "+" : ""}
                            {run.delta}%
                          </StatBadge>
                        </td>
                        <td className="px-4 py-2 text-right">
                          <div className="inline-flex items-center gap-1.5">
                            <IconButton title="Relancer">
                              <Play size={16} />
                            </IconButton>
                            <IconButton title="Rerun avec mêmes paramètres">
                              <Repeat2 size={16} />
                            </IconButton>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Panel>

            <Panel className="col-span-12 lg:col-span-4 p-4">
              <HealthPanel
                apiStatus={healthQuery.data?.status}
                apiLatencyMs={healthQuery.data?.latency_ms}
                dbOk={healthQuery.data?.db_ok}
                orchStatus={healthQuery.data?.orchestrator?.status}
                orchUptime={healthQuery.data?.orchestrator?.uptime_s}
              />
            </Panel>
          </div>
        ) : null}

        {tab === "Tâches" ? (
          <div className="grid grid-cols-12 gap-5">
            <div className="col-span-12 lg:col-span-8">
              <Panel className="p-0">
                <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                  <h2 className="text-sm font-medium text-white/80">Tâches récentes</h2>
                  <button className="text-xs text-indigo-300 hover:text-indigo-200 underline decoration-dotted" onClick={() => (window.location.href = "/tasks")} type="button">
                    Voir tout
                  </button>
                </div>
                <div className="max-h-[420px] overflow-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 z-10 bg-white/5 text-left text-xs text-white/60 backdrop-blur">
                      <tr>
                        <th className="px-4 py-2">ID</th>
                        <th className="px-4 py-2">Titre</th>
                        <th className="px-4 py-2">Statut</th>
                        <th className="px-4 py-2">Mise à jour</th>
                        <th className="px-4 py-2 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(tasksQuery.data?.items ?? []).map((t: TaskListItem) => (
                        <tr key={t.id} className="border-t border-white/5">
                          <td className="px-4 py-2 text-white/60">{t.id}</td>
                          <td className="px-4 py-2 font-medium text-white/90">{t.title}</td>
                          <td className="px-4 py-2 text-white/80">{t.status ?? "—"}</td>
                          <td className="px-4 py-2 text-white/70">{t.updated_at ? new Date(t.updated_at).toLocaleString() : "—"}</td>
                          <td className="px-4 py-2 text-right">
                            <button className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]" onClick={() => openTask(t.id)} type="button">
                              Ouvrir
                            </button>
                          </td>
                        </tr>
                      ))}
                      {tasksQuery.isLoading ? (
                        <tr><td colSpan={5} className="px-4 py-3 text-white/60">Chargement…</td></tr>
                      ) : null}
                      {tasksQuery.isError ? (
                        <tr><td colSpan={5} className="px-4 py-3 text-red-300">Erreur de chargement des tâches</td></tr>
                      ) : null}
                      {(tasksQuery.data?.items ?? []).length === 0 && !tasksQuery.isLoading && !tasksQuery.isError ? (
                        <tr><td colSpan={5} className="px-4 py-3 text-white/60">Aucune tâche</td></tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </Panel>
            </div>
            <Panel className="col-span-12 lg:col-span-4 p-4">
              <h2 className="mb-3 text-sm font-medium text-white/80">Aide</h2>
              <ul className="list-disc space-y-1 pl-5 text-sm text-white/70">
                <li>Consultez une tâche pour générer/valider son plan.</li>
                <li>Lancez l'exécution depuis la page Tâches.</li>
              </ul>
            </Panel>
          </div>
        ) : null}

        {tab === "Outils" ? (
          <div className="grid grid-cols-12 gap-5">
            <Panel className="col-span-12 p-4">
              <h2 className="text-sm font-medium text-white/80">Outils IA</h2>
              <p className="mt-2 text-sm text-white/70">Espace réservé pour intégrer vos outils IA. Ouvrir la page Outils dédiée pour gérer et ajouter de nouveaux modules.</p>
              <div className="mt-3">
                <button className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm hover:bg-white/[0.07]" onClick={() => (window.location.href = "/tools")} type="button">
                  Aller à Outils
                </button>
              </div>
            </Panel>
          </div>
        ) : null}

        {tab === "Opérations" ? (
          <div className="grid grid-cols-12 gap-5">
            <div className="col-span-12 lg:col-span-8">
              <Panel className="p-0">
                <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                  <h2 className="text-sm font-medium text-white/80">Tâches récentes</h2>
                  <button className="text-xs text-indigo-300 hover:text-indigo-200 underline decoration-dotted" onClick={() => (window.location.href = "/tasks")} type="button">
                    Voir tout
                  </button>
                </div>
                <div className="max-h-[420px] overflow-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 z-10 bg-white/5 text-left text-xs text-white/60 backdrop-blur">
                      <tr>
                        <th className="px-4 py-2">ID</th>
                        <th className="px-4 py-2">Titre</th>
                        <th className="px-4 py-2">Statut</th>
                        <th className="px-4 py-2">Mise à jour</th>
                        <th className="px-4 py-2 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(tasksQuery.data?.items ?? []).map((t: TaskListItem) => (
                        <tr key={t.id} className="border-t border-white/5">
                          <td className="px-4 py-2 text-white/60">{t.id}</td>
                          <td className="px-4 py-2 font-medium text-white/90">{t.title}</td>
                          <td className="px-4 py-2 text-white/80">{t.status ?? "—"}</td>
                          <td className="px-4 py-2 text-white/70">{t.updated_at ? new Date(t.updated_at).toLocaleString() : "—"}</td>
                          <td className="px-4 py-2 text-right">
                            <button className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]" onClick={() => openTask(t.id)} type="button">
                              Ouvrir
                            </button>
                          </td>
                        </tr>
                      ))}
                      {tasksQuery.isLoading ? (
                        <tr><td colSpan={5} className="px-4 py-3 text-white/60">Chargement…</td></tr>
                      ) : null}
                      {tasksQuery.isError ? (
                        <tr><td colSpan={5} className="px-4 py-3 text-red-300">Erreur de chargement des tâches</td></tr>
                      ) : null}
                      {(tasksQuery.data?.items ?? []).length === 0 && !tasksQuery.isLoading && !tasksQuery.isError ? (
                        <tr><td colSpan={5} className="px-4 py-3 text-white/60">Aucune tâche</td></tr>
                      ) : null}
                    </tbody>
                  </table>
                </div>
              </Panel>
            </div>
            <Panel className="col-span-12 lg:col-span-4 p-4">
              <h2 className="mb-3 text-sm font-medium text-white/80">Aide</h2>
              <ul className="list-disc space-y-1 pl-5 text-sm text-white/70">
                <li>Consultez une tâche pour générer/valider son plan.</li>
                <li>Lancez l'exécution depuis la page Tâches.</li>
              </ul>
            </Panel>
          </div>
        ) : null}
      </main>
    </div>
  );
}

export default DashboardPage;
