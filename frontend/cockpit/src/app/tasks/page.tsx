"use client";

import { FormEvent, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { fetchJson } from "@/lib/fetchJson";
import { EmptyState } from "@/components/EmptyState";
import { useToast } from "@/components/ds/Toast";

interface TaskItem {
  id: string;
  title: string;
  status?: string;
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
        <h1 className="text-2xl font-semibold">Tasks</h1>
        <button
          type="button"
          onClick={() => refetch()}
          disabled={isFetching}
          className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-busy={isFetching}
        >
          Rafraîchir
        </button>
      </div>

      {lastRunId && (
        <div role="status" aria-live="polite" className="glass p-3 rounded-md border">
          Run démarré. {" "}
          <a
            href={`/runs/${lastRunId}`}
            className="underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
          >
            Voir le run
          </a>
        </div>
      )}

      <section aria-label="Créer une tâche" className="glass p-4 rounded-md border space-y-3">
        <h2 className="text-lg font-medium">Créer une tâche</h2>
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="space-y-1">
            <label htmlFor="task-title" className="block text-sm font-medium">Titre</label>
            <input
              id="task-title"
              name="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-md border px-3 py-2 bg-background focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
              className="w-full rounded-md border px-3 py-2 bg-background focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              rows={3}
              placeholder="Détails de la tâche"
            />
          </div>
          <div>
            <button
              type="submit"
              disabled={submitting}
              aria-busy={submitting}
              className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              Créer
            </button>
          </div>
        </form>
      </section>

      {isLoading && <p role="status" aria-live="polite">Chargement des tasks…</p>}
      {isError && (
        <div role="alert" className="glass p-4 rounded-md border">
          <p className="font-medium">Erreur lors du chargement des tasks</p>
          <p className="text-sm opacity-80">{(error as Error)?.message || "API indisponible"}</p>
        </div>
      )}

      {data && data.items.length === 0 && (
        <EmptyState title="Aucune tâche" description="Créez ou lancez une tâche pour démarrer un run." ctaHref="/tasks" ctaLabel="Créer une tâche" />
      )}

      {data && data.items.length > 0 && (
        <ol role="list" className="space-y-2">
          {data.items.map((t) => (
            <li key={t.id} className="glass p-3 rounded-md border">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{t.title || t.id}</p>
                  {t.status && (
                    <p className="text-sm opacity-80">{t.status}</p>
                  )}
                </div>
                <div>
                  <button
                    type="button"
                    onClick={() => startTask(t.id)}
                    disabled={startingId === t.id}
                    aria-busy={startingId === t.id}
                    className="glass px-3 py-1 rounded-md border focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    Démarrer
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </main>
  );
}
