"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { ClayCard } from "@/components/ds/ClayCard";
import { ClayButton } from "@/components/ds/ClayButton";
import { useToast } from "@/components/ds/Toast";

type PlanStatus = "draft" | "ready" | "invalid";

interface PlanResponse {
  id: string;
  task_id: string;
  status: PlanStatus | Status | string;
  version?: number;
  graph: unknown;
}

export default function PlanDetailPage({ params }: { params: { plan_id: string } }) {
  const { plan_id } = params;
  const toast = useToast();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [data, setData] = useState<PlanResponse | null>(null);

  const status: PlanStatus | undefined = useMemo(() => {
    const raw = (data?.status || "").toString().toLowerCase();
    if (raw.includes("ready")) return "ready";
    if (raw.includes("invalid")) return "invalid";
    if (raw.includes("draft")) return "draft";
    return undefined;
  }, [data?.status]);

  useEffect(() => {
    let abort = false;
    (async () => {
      try {
        setLoading(true);
        const res = await fetch(resolveApiUrl(`/plans/${plan_id}`), {
          headers: { ...defaultApiHeaders(), Accept: "application/json" },
        });
        if (!res.ok) throw new Error(res.statusText || `HTTP ${res.status}`);
        const body = (await res.json()) as PlanResponse;
        if (!abort) setData(body);
      } catch (err) {
        if (!abort) toast((err as Error)?.message || "Échec du chargement du plan", "error");
      } finally {
        if (!abort) setLoading(false);
      }
    })();
    return () => {
      abort = true;
    };
  }, [plan_id, toast]);

  const submitValidation = async () => {
    if (!data) return;
    try {
      setSubmitting(true);
      const res = await fetch(resolveApiUrl(`/plans/${plan_id}/submit_for_validation`), {
        method: "POST",
        headers: { ...defaultApiHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ validated: true, errors: [] }),
      });
      if (!res.ok) {
        let msg = res.statusText || `HTTP ${res.status}`;
        try {
          const j = await res.json();
          if (typeof j?.detail === "string") msg = j.detail;
        } catch {}
        throw new Error(msg);
      }
      toast("Plan validé — prêt à démarrer", "default");
      // recharger le plan
      const refreshed = await fetch(resolveApiUrl(`/plans/${plan_id}`), {
        headers: { ...defaultApiHeaders(), Accept: "application/json" },
      });
      setData((await refreshed.json()) as PlanResponse);
    } catch (err) {
      toast((err as Error)?.message || "Échec de la validation", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const startTask = async () => {
    if (!data?.task_id) return;
    try {
      const res = await fetch(resolveApiUrl(`/tasks/${data.task_id}/start`), {
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
      toast("Run démarré", "default");
      router.push(`/runs/${body.run_id}`);
    } catch (err) {
      toast((err as Error)?.message || "Échec du démarrage", "error");
    }
  };

  return (
    <main role="main" className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Plan</h1>
        <div className="flex items-center gap-2">
          {status && (
            <span
              className="inline-flex items-center rounded-full border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-700"
              aria-label={`Statut: ${status}`}
            >
              {status}
            </span>
          )}
          {status !== "ready" && (
            <ClayButton type="button" onClick={submitValidation} disabled={loading || submitting} aria-busy={submitting}>
              Valider le plan
            </ClayButton>
          )}
          {status === "ready" && (
            <ClayButton type="button" onClick={startTask} disabled={loading}>
              Démarrer la tâche
            </ClayButton>
          )}
        </div>
      </div>

      <ClayCard className="p-4">
        {loading && <p role="status" aria-live="polite">Chargement…</p>}
        {!loading && data && (
          <div className="space-y-3">
            <div className="text-sm text-slate-600">Plan ID: {data.id} — Version: {data.version ?? 1}</div>
            <div className="text-sm text-slate-600">Task ID: {data.task_id}</div>
            <pre className="mt-2 max-h-[480px] overflow-auto rounded-xl bg-slate-50 p-3 text-xs text-slate-800">
{JSON.stringify(data.graph, null, 2)}
            </pre>
          </div>
        )}
        {!loading && !data && (
          <p className="text-sm text-red-600">Plan introuvable.</p>
        )}
      </ClayCard>
    </main>
  );
}
