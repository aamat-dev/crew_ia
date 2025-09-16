"use client";
import * as React from "react";
import { cn } from "@/lib/utils";
import KpiCard from "@/components/ui/KpiCard";
import StatusBadge from "@/components/ui/StatusBadge";
import { Users, GaugeCircle, Activity } from "lucide-react";

type AgentRole = 'Superviseur'|'Manager'|'Exécutant';
type AgentStatus = 'Actif'|'Inactif';

interface AgentItem { id: string; name: string; role: AgentRole; status: AgentStatus; success: number; latency: number; runs: number; }

const MOCK: AgentItem[] = Array.from({ length: 9 }).map((_, i) => ({
  id: `ag-${i+1}`,
  name: `Agent ${i+1}`,
  role: (i % 3 === 0 ? 'Superviseur' : i % 3 === 1 ? 'Manager' : 'Exécutant') as AgentRole,
  status: (i % 4 === 0 ? 'Inactif' : 'Actif') as AgentStatus,
  success: 80 + (i % 5) * 3,
  latency: 1.2 + (i % 4) * 0.3,
  runs: 10 + (i % 7) * 3,
}));

function AgentCard({ item }: { item: AgentItem }) {
  return (
    <div className="clay-card p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={cn("grid h-10 w-10 place-content-center rounded-xl text-white bg-gradient-to-br",
            item.role === 'Superviseur' && 'from-indigo-500 to-indigo-400',
            item.role === 'Manager' && 'from-cyan-500 to-cyan-400',
            item.role === 'Exécutant' && 'from-emerald-500 to-emerald-400'
          )}>
            <Users className="h-5 w-5" />
          </span>
          <div>
            <p className="font-medium text-slate-100">{item.name}</p>
            <p className="text-sm text-slate-400">{item.role} • {item.status}</p>
          </div>
        </div>
        <StatusBadge status={item.status === 'Actif' ? 'completed' : 'paused'} />
      </div>
      <div className="mt-3 grid grid-cols-3 gap-3">
        <KpiCard label="Taux succès" value={item.success} unit="%" accent="emerald" icon={GaugeCircle} />
        <KpiCard label="Latence" value={item.latency} unit="s" accent="amber" icon={Activity} />
        <KpiCard label="Runs récents" value={item.runs} accent="indigo" icon={Users} />
      </div>
      <div className="mt-3 flex gap-2">
        <button className="rounded-xl border border-slate-700 bg-[#2A2D36] px-3 py-2 text-sm text-slate-200 hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]">Profil</button>
        <button className="rounded-xl border border-slate-700 bg-[#2A2D36] px-3 py-2 text-sm text-slate-200 hover:bg-indigo-600/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]">Désactiver</button>
      </div>
    </div>
  );
}

export default function AgentsPage() {
  const [role, setRole] = React.useState<AgentRole | 'Tous'>('Tous');
  const [status, setStatus] = React.useState<AgentStatus | 'Tous'>('Tous');
  const data = MOCK.filter(a => (role === 'Tous' || a.role === role) && (status === 'Tous' || a.status === status));
  return (
    <main role="main" className="p-6 space-y-6">
      <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">Agents</h1>
      <div className="flex flex-wrap items-center gap-2">
        <select aria-label="Filtrer par rôle" value={role} onChange={(e) => setRole(e.target.value as AgentRole | 'Tous')}
          className="px-3 py-2 rounded-2xl border border-slate-700 bg-[#2A2D36] text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]">
          {['Tous','Superviseur','Manager','Exécutant'].map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <select aria-label="Filtrer par statut" value={status} onChange={(e) => setStatus(e.target.value as AgentStatus | 'Tous')}
          className="px-3 py-2 rounded-2xl border border-slate-700 bg-[#2A2D36] text-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]">
          {['Tous','Actif','Inactif'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3" aria-label="Liste des agents">
        {data.map(a => <AgentCard key={a.id} item={a} />)}
      </section>
    </main>
  );
}
