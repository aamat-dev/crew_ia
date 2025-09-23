"use client";

import { FormEvent, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { fetchJson } from "@/lib/fetchJson";
import { EmptyState } from "@/components/EmptyState";
import { StatusBadge } from "@/components/ds/StatusBadge";
import type { Status } from "@/components/ds/StatusBadge";
import { ClayCard } from "@/components/ds/ClayCard";
import { ClayButton } from "@/components/ds/ClayButton";
import { useToast } from "@/components/ds/Toast";

interface TaskItem {
  id: string;
  title: string;
  status?: Status;
  created_at?: string;
}

interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  links?: Record<string, string> | null;
}

export default function TasksPage() {
  const toast = useToast();
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery<Page<TaskItem>>({
    queryKey: ["tasks", { limit: 20 }],
    queryFn: ({ signal }) =>
      fetchJson<Page<TaskItem>>(resolveApiUrl(`/tasks?limit=20`), {
        signal,
        headers: defaultApiHeaders(),
      }),
  });

  const [lastRunId, setLastRunId] = useState<string | null>(null);
  const [startingId, setStartingId] = useState<string | null>(null);
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  const generatePlan = async (
    taskId: string,
    { silent = false }: { silent?: boolean } = {}
  ): Promise<{ plan_id: string; status: "ready" | "draft" | "invalid" } | null> => {
    try {
      setGeneratingId(taskId);
      const res = await fetch(resolveApiUrl(`/tasks/${taskId}/plan`), {
        method: "POST",
        headers: { ...defaultApiHeaders() },
      });
      if (!res.ok) {
        let msg = res.statusText || `HTTP ${res.status}`;
        try {
          const j = await res.json();
          if (typeof j?.detail === "string") msg = j.detail;
        } catch {}
        throw new Error(msg);
      }
      const body = (await res.json()) as { plan_id: string; status: "ready" | "draft" | "invalid" };
      if (!silent) {
        if (body.status === "ready") toast("Plan généré (prêt)", "default");
        else if (body.status === "draft") toast("Plan généré (brouillon)", "warning");
        else toast("Plan invalide", "error");
      }
      return body;
    } catch (err) {
      if (!silent) toast((err as Error)?.message || "Échec de la génération du plan", "error");
      return null;
    } finally {
      setGeneratingId(null);
      await qc.invalidateQueries({ queryKey: ["tasks"] });
    }
  };

  const startTask = async (taskId: string) => {
    try {
      setStartingId(taskId);
      const res = await fetch(resolveApiUrl(`/tasks/${taskId}/start`), {
        method: "POST",
        headers: { ...defaultApiHeaders() },
      });
      if (!res.ok) {
        let msg = res.statusText || `HTTP ${res.status}`;
        try {
          const j = await res.json();
          if (typeof j?.detail === "string") msg = j.detail;
        } catch {}
        // Si le plan manque, tentons de le générer automatiquement puis relancer
        if (msg.toLowerCase().includes("plan missing")) {
          const gen = await generatePlan(taskId, { silent: true });
          if (gen && gen.status === "ready") {
            const retry = await fetch(resolveApiUrl(`/tasks/${taskId}/start`), {
              method: "POST",
              headers: { ...defaultApiHeaders() },
            });
            if (!retry.ok) {
              let retryMsg = retry.statusText || `HTTP ${retry.status}`;
              try {
                const rj = await retry.json();
                if (typeof rj?.detail === "string") retryMsg = rj.detail;
              } catch {}
              throw new Error(retryMsg);
            }
            const body = (await retry.json()) as { run_id: string };
            setLastRunId(body.run_id);
            toast("Plan généré et run démarré", "default");
            return;
          }
          if (gen && gen.status === "draft") {
            throw new Error("Plan généré en brouillon — validez le plan");
          }
          throw new Error("Plan introuvable ou invalide");
        }
        throw new Error(msg);
      }
      const body = (await res.json()) as { run_id: string };
      setLastRunId(body.run_id);
      toast("Run démarré", "default");
    } catch (err) {
      toast((err as Error)?.message || "Échec du démarrage", "error");
    } finally {
      setStartingId(null);
      // update data eventually (task status might change)
      await qc.invalidateQueries({ queryKey: ["tasks"] });
    }
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const t = title.trim();
    if (!t) {
      toast("Le titre est requis", "error");
      return;
    }
    try {
      setSubmitting(true);
      const res = await fetch(resolveApiUrl("/tasks"), {
        method: "POST",
        headers: { ...defaultApiHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ title: t, description: description.trim() || undefined }),
      });
      if (!res.ok) {
        let msg = res.statusText || `HTTP ${res.status}`;
        try {
          const j = await res.json();
          if (typeof j?.detail === "string") msg = j.detail;
        } catch {}
        throw new Error(msg);
      }
      setTitle("");
      setDescription("");
      toast("Tâche créée", "default");
      // Rafraîchir la liste
      await qc.invalidateQueries({ queryKey: ["tasks"] });
    } catch (err) {
      toast((err as Error)?.message || "Échec de la création", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main role="main" className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Tasks</h1>
        <ClayButton type="button" onClick={() => refetch()} disabled={isFetching} aria-busy={isFetching}>
          Rafraîchir
        </ClayButton>
      </div>

      {lastRunId && (
        <ClayCard role="status" aria-live="polite" className="p-3">
          Run démarré. {" "}
          <a
            href={`/runs/${lastRunId}`}
            className="underline focus:outline-none focus-visible:ring-2 focus-visible:ring-focus rounded"
          >
            Voir le run
          </a>
        </ClayCard>
      )}

      <ClayCard aria-label="Créer une tâche" className="p-4 space-y-3">
        <h2 className="text-lg font-medium">Créer une tâche</h2>
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="space-y-1">
            <label htmlFor="task-title" className="block text-sm font-medium">Titre</label>
            <input
              id="task-title"
              name="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-slate-900 shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
              placeholder="Ex: Préparer un rapport"
              required
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="task-desc" className="block text-sm font-medium">Description (optionnelle)</label>
            <textarea
              id="task-desc"
              name="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-slate-900 shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
              rows={3}
              placeholder="Détails de la tâche"
            />
          </div>
          <div>
            <ClayButton type="submit" disabled={submitting} aria-busy={submitting}>
              Créer
            </ClayButton>
          </div>
        </form>
      </ClayCard>

      {isLoading && <p role="status" aria-live="polite">Chargement des tasks…</p>}
      {isError && (
        <ClayCard role="alert" className="p-4">
          <p className="font-medium">Erreur lors du chargement des tasks</p>
          <p className="text-sm opacity-80">{(error as Error)?.message || "API indisponible"}</p>
        </ClayCard>
      )}

      {data && data.items.length === 0 && (
        <EmptyState title="Aucune tâche" description="Créez ou lancez une tâche pour démarrer un run." ctaHref="/tasks" ctaLabel="Créer une tâche" />
      )}

      {data && data.items.length > 0 && (
        <ol role="list" className="space-y-2">
          {data.items.map((t) => (
            <ClayCard as="li" key={t.id} className="p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{t.title || t.id}</p>
                  {t.status && (
                    <div className="mt-1">
                      <StatusBadge status={t.status} />
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <ClayButton
                    type="button"
                    onClick={() => generatePlan(t.id)}
                    disabled={generatingId === t.id}
                    aria-busy={generatingId === t.id}
                  >
                    Générer un plan
                  </ClayButton>
                  <ClayButton
                    type="button"
                    onClick={() => startTask(t.id)}
                    disabled={startingId === t.id}
                    aria-busy={startingId === t.id}
                  >
                    Démarrer
                  </ClayButton>
                </div>
              </div>
            </ClayCard>
          ))}
        </ol>
      )}
    </main>
  );
}
