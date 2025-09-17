"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Activity, GaugeCircle, PlayCircle, Users } from "lucide-react";
import { HeaderBar } from "@/ui/HeaderBar";
import { KpiCard } from "@/ui/KpiCard";
import { MetricChartCard } from "@/ui/MetricChartCard";
import { NoticeCard } from "@/ui/NoticeCard";
import { TimelineItem } from "@/ui/TimelineItem";
import { RunDrawer } from "@/features/runs/RunDrawer";
import { Run } from "@/features/runs/types";
import { Status } from "@/ui/theme";
import { cn } from "@/lib/utils";

const KPI_CARDS = [
  { label: "Runs aujourd'hui", value: 128, delta: "+8%", accent: "indigo" as const, icon: <PlayCircle className="h-5 w-5" /> },
  { label: "Agents actifs", value: 24, delta: "+3", accent: "cyan" as const, icon: <Users className="h-5 w-5" /> },
  { label: "Taux succès", value: "94%", delta: "+2 pts", accent: "emerald" as const, icon: <GaugeCircle className="h-5 w-5" /> },
  { label: "Latence médiane", value: "2.4s", delta: "-0.3s", accent: "amber" as const, icon: <Activity className="h-5 w-5" /> },
];

const AGENT_LOAD = [
  { label: "Superviseurs", value: 76, gradient: "from-[var(--accent-indigo-500)] to-[var(--accent-indigo-400)]" },
  { label: "Managers", value: 58, gradient: "from-[var(--accent-cyan-500)] to-[var(--accent-cyan-400)]" },
  { label: "Exécutants", value: 42, gradient: "from-[var(--accent-emerald-500)] to-[var(--accent-emerald-400)]" },
];

const THROUGHPUT_DATA = [
  { name: "Lun", valeur: 32 },
  { name: "Mar", valeur: 40 },
  { name: "Mer", valeur: 36 },
  { name: "Jeu", valeur: 44 },
  { name: "Ven", valeur: 48 },
  { name: "Sam", valeur: 38 },
  { name: "Dim", valeur: 30 },
];

const FEEDBACK_DATA = [
  { name: "S37", avis: 12 },
  { name: "S38", avis: 18 },
  { name: "S39", avis: 15 },
  { name: "S40", avis: 22 },
  { name: "S41", avis: 19 },
  { name: "S42", avis: 24 },
];

const TIMELINE_RUNS: Run[] = [
  {
    id: "dash-201",
    title: "Veille marché US",
    status: "running",
    date: "Aujourd'hui • 09:32",
    duration: "14m",
    throughput: 38,
    successRate: 88,
    agents: [
      { id: "ag-12", name: "Noé", role: "Manager" },
      { id: "ag-14", name: "Aline", role: "Exécutant" },
    ],
    logs: [
      { timestamp: "09:32", message: "Run démarré" },
      { timestamp: "09:34", message: "Collecte articles" },
    ],
    description: "Collecte quotidienne et tri des sources presse.",
  },
  {
    id: "dash-198",
    title: "Audit sécurité SOC2",
    status: "completed",
    date: "Hier • 18:04",
    duration: "22m",
    throughput: 26,
    successRate: 96,
    agents: [
      { id: "ag-6", name: "Mina", role: "Exécutant" },
      { id: "ag-2", name: "Noah", role: "Manager" },
    ],
    logs: [
      { timestamp: "17:42", message: "Étape 1 terminée" },
      { timestamp: "18:04", message: "Rapport généré" },
    ],
  },
  {
    id: "dash-195",
    title: "Préparation revue trimestrielle",
    status: "queued",
    date: "Hier • 14:48",
    duration: "--",
    throughput: 0,
    successRate: 0,
    agents: [
      { id: "ag-18", name: "Lou", role: "Superviseur" },
    ],
    logs: [{ timestamp: "14:48", message: "En file d'attente" }],
  },
  {
    id: "dash-190",
    title: "Analyse sentiments feedbacks",
    status: "completed",
    date: "16 nov. • 19:22",
    duration: "17m",
    throughput: 31,
    successRate: 91,
    agents: [
      { id: "ag-7", name: "Léa", role: "Exécutant" },
      { id: "ag-3", name: "Maya", role: "Superviseur" },
    ],
    logs: [{ timestamp: "19:05", message: "Extraction des données NPS" }],
  },
  {
    id: "dash-187",
    title: "Migration knowledge base",
    status: "failed",
    date: "16 nov. • 11:10",
    duration: "8m",
    throughput: 12,
    successRate: 35,
    agents: [
      { id: "ag-2", name: "Noah", role: "Manager" },
      { id: "ag-9", name: "Jules", role: "Exécutant" },
    ],
    logs: [
      { timestamp: "11:05", message: "Début migration" },
      { timestamp: "11:10", message: "Erreur connexion S3" },
    ],
    errors: ["Accès bucket restreint", "Quota S3 dépassé"],
  },
  {
    id: "dash-184",
    title: "Synthèse insights clients",
    status: "running",
    date: "15 nov. • 22:14",
    duration: "11m",
    throughput: 24,
    successRate: 74,
    agents: [
      { id: "ag-5", name: "Sacha", role: "Manager" },
      { id: "ag-11", name: "Zoé", role: "Exécutant" },
    ],
    logs: [{ timestamp: "22:14", message: "Analyse keywords" }],
  },
];

const containerVariants = {
  initial: {},
  animate: {
    transition: { staggerChildren: 0.08, delayChildren: 0.12 },
  },
};

export function DashboardPage() {
  const [loading, setLoading] = React.useState(true);
  const [selectedRun, setSelectedRun] = React.useState<Run | null>(null);

  React.useEffect(() => {
    const timer = window.setTimeout(() => setLoading(false), 420);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <div className="space-y-6">
      <HeaderBar title="Dashboard" breadcrumb="Vue générale" />
      <motion.div
        className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4"
        variants={containerVariants}
        initial="initial"
        animate="animate"
      >
        {KPI_CARDS.map((kpi) => (
          <KpiCard
            key={kpi.label}
            label={kpi.label}
            value={kpi.value}
            delta={kpi.delta}
            accent={kpi.accent}
            icon={kpi.icon}
            loading={loading}
          />
        ))}
      </motion.div>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <MetricChartCard
          title="Débit agents"
          type="area"
          data={THROUGHPUT_DATA}
          xKey="name"
          yKey="valeur"
          accent="indigo"
          className="xl:col-span-2"
        />
        <MetricChartCard
          title="Feedbacks"
          type="bar"
          data={FEEDBACK_DATA}
          xKey="name"
          yKey="avis"
          accent="cyan"
        />
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-[color:var(--text)]">Derniers runs</h2>
            <div className="space-y-3">
              {loading ? (
                <div className="grid gap-3">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div key={`timeline-skeleton-${index}`} className="surface shadow-card p-4 animate-pulse">
                      <div className="h-5 w-48 rounded bg-slate-700/40" />
                      <div className="mt-3 h-4 w-32 rounded bg-slate-700/30" />
                    </div>
                  ))}
                </div>
              ) : (
                TIMELINE_RUNS.map((run) => (
                  <TimelineItem
                    key={run.id}
                    title={run.title}
                    date={run.date}
                    status={run.status as Status}
                    description={run.description}
                    onRetry={() => setSelectedRun(run)}
                    onDetails={() => setSelectedRun(run)}
                  />
                ))
              )}
            </div>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <NoticeCard
              type="success"
              title="Déploiement réussi"
              message="Version 1.8 distribuée sur l'ensemble des environnements sans incident."
            />
            <NoticeCard
              type="warning"
              title="Quota API"
              message="Le seuil d'usage API atteint 82% ce mois-ci. Pensez à ajuster les limites."
            />
          </div>
        </div>
        <aside className="space-y-4">
          <div className="surface shadow-card p-4">
            <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Charge agents</h3>
            <div className="mt-4 space-y-4">
              {AGENT_LOAD.map((item) => (
                <div key={item.label} className="space-y-2">
                  <div className="flex items-center justify-between text-sm text-secondary">
                    <span>{item.label}</span>
                    <span>{item.value}%</span>
                  </div>
                  <div className="h-3 w-full rounded-full bg-slate-800">
                    <div
                      className={cn(
                        "h-3 rounded-full bg-gradient-to-r",
                        item.gradient
                      )}
                      style={{ width: `${item.value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
      <div className="surface shadow-card p-4 space-y-3">
            <h3 className="text-sm font-semibold text-[color:var(--text)] uppercase tracking-wide">Notifications</h3>
            <NoticeCard
              type="success"
              message="Intégration CRM synchronisée avec succès."
            />
            <NoticeCard
              type="error"
              message="Une clé API partenaire arrive à expiration dans 3 jours."
            />
          </div>
        </aside>
      </section>

      <RunDrawer
        run={selectedRun}
        open={Boolean(selectedRun)}
        onClose={() => setSelectedRun(null)}
        onRetry={(run) => console.log("Relancer", run.id)}
        onStop={(run) => console.log("Stopper", run.id)}
      />
    </div>
  );
}

export default DashboardPage;
