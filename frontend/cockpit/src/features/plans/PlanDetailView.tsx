"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { ClayCard } from "@/components/ds/ClayCard";
import { ClayButton } from "@/components/ds/ClayButton";
import { useToast } from "@/components/ds/Toast";
import { fetchPlanVersionDiff, type PlanVersionDiff } from "@/lib/api";

type PlanStatus = "draft" | "ready" | "invalid";

interface PlanResponse {
  id: string;
  task_id: string;
  status: PlanStatus | string;
  version?: number;
  graph: unknown;
}

export interface PlanDetailViewProps {
  planId: string;
  showHeader?: boolean;
}

export function PlanDetailView({ planId, showHeader = true }: PlanDetailViewProps) {
  const toast = useToast();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [data, setData] = useState<PlanResponse | null>(null);
  const [versions, setVersions] = useState<{ numero_version: number; created_at?: string | null; reason?: string | null }[] | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [versionGraph, setVersionGraph] = useState<unknown | null>(null);
  const [diff, setDiff] = useState<PlanVersionDiff | null>(null);
  const [diffLoading, setDiffLoading] = useState(false);
  const [diffError, setDiffError] = useState<string | null>(null);
  const [llmInfo, setLlmInfo] = useState<{ provider?: string; model?: string } | null>(null);
  const [viaFallback, setViaFallback] = useState<boolean>(false);

  const status: PlanStatus | undefined = useMemo(() => {
    const raw = (data?.status || "").toString().toLowerCase();
    if (raw.includes("ready")) return "ready";
    if (raw.includes("invalid")) return "invalid";
    if (raw.includes("draft")) return "draft";
    return undefined;
  }, [data?.status]);
  const statusLabel = useMemo(() => {
    if (!status) return undefined;
    if (status === "ready") return "Prêt";
    if (status === "invalid") return "Invalide";
    return viaFallback ? "Brouillon (fallback)" : "Brouillon";
  }, [status, viaFallback]);

  useEffect(() => {
    let abort = false;
    (async () => {
      try {
        setLoading(true);
        const res = await fetch(resolveApiUrl(`/plans/${planId}`), {
          headers: { ...defaultApiHeaders(), Accept: "application/json" },
        });
        if (!res.ok) throw new Error(res.statusText || `HTTP ${res.status}`);
        const body = (await res.json()) as PlanResponse;
        if (!abort) {
          setData(body);
          try {
            const g = body.graph as Record<string, unknown> | null;
            setViaFallback(!!(g && typeof g === 'object' && (g as Record<string, unknown>)['via_fallback']));
          } catch { setViaFallback(false); }
        }
        // charge les versions
        const vres = await fetch(resolveApiUrl(`/plans/${planId}/versions`), {
          headers: { ...defaultApiHeaders(), Accept: "application/json" },
        });
        if (vres.ok) {
          const vbody = (await vres.json()) as { versions: { numero_version: number; created_at?: string; reason?: string | null }[] };
          if (!abort) setVersions(vbody.versions || []);
        }
        // LLM info (provider/model)
        try {
          const cres = await fetch(resolveApiUrl(`/config/llm`), {
            headers: { ...defaultApiHeaders(), Accept: "application/json" },
          });
          if (cres.ok) {
            const cfg = await cres.json();
            if (!abort) setLlmInfo({ provider: cfg.SUPERVISOR_PROVIDER, model: cfg.SUPERVISOR_MODEL });
          }
        } catch {}
      } catch (err) {
        if (!abort) toast((err as Error)?.message || "Échec du chargement du plan", "error");
      } finally {
        if (!abort) setLoading(false);
      }
    })();
    return () => {
      abort = true;
    };
  }, [planId, toast]);

  const loadVersion = async (numero: number) => {
    setSelectedVersion(numero);
    setVersionGraph(null);
    setDiff(null);
    setDiffError(null);
    setDiffLoading(false);
    try {
      const res = await fetch(resolveApiUrl(`/plans/${planId}/versions/${numero}`), {
        headers: { ...defaultApiHeaders(), Accept: "application/json" },
      });
      if (!res.ok) throw new Error(res.statusText || `HTTP ${res.status}`);
      const body = await res.json();
      setVersionGraph(body.graph);
      const prevEntry = (versions || [])
        ?.filter((v) => v.numero_version < numero)
        .sort((a, b) => a.numero_version - b.numero_version)
        .pop();
      if (prevEntry) {
        setDiffLoading(true);
        try {
          const diffData = await fetchPlanVersionDiff(planId, numero, prevEntry.numero_version);
          setDiff(diffData);
        } catch (err) {
          setDiffError((err as Error)?.message || "Impossible de calculer le diff");
        } finally {
          setDiffLoading(false);
        }
      } else {
        setDiff(null);
      }
    } catch (err) {
      toast((err as Error)?.message || "Impossible de charger la version", "error");
    }
  };

  useEffect(() => {
    if (!versions || versions.length === 0 || selectedVersion !== null) return;
    const latest = versions[versions.length - 1]?.numero_version;
    if (latest) {
      void loadVersion(latest);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [versions]);

  const submitValidation = async () => {
    if (!data) return;
    try {
      setSubmitting(true);
      const res = await fetch(resolveApiUrl(`/plans/${planId}/submit_for_validation`), {
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
      const refreshed = await fetch(resolveApiUrl(`/plans/${planId}`), {
        headers: { ...defaultApiHeaders(), Accept: "application/json" },
      });
      setData((await refreshed.json()) as PlanResponse);
    } catch (err) {
      toast((err as Error)?.message || "Échec de la validation", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const regeneratePlan = async () => {
    if (!data?.task_id) return;
    try {
      setSubmitting(true);
      const res = await fetch(resolveApiUrl(`/tasks/${data.task_id}/plan`), {
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
      // recharger le plan et les versions
      const pref = await fetch(resolveApiUrl(`/plans/${planId}`), {
        headers: { ...defaultApiHeaders(), Accept: "application/json" },
      });
      setData((await pref.json()) as PlanResponse);
      const vres = await fetch(resolveApiUrl(`/plans/${planId}/versions`), {
        headers: { ...defaultApiHeaders(), Accept: "application/json" },
      });
      if (vres.ok) {
        const vbody = (await vres.json()) as { versions: { numero_version: number; created_at?: string; reason?: string | null }[] };
        setVersions(vbody.versions || []);
      }
      toast("Plan régénéré via Ollama", "default");
    } catch (err) {
      toast((err as Error)?.message || "Échec de la régénération", "error");
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

  const containerClass = showHeader ? "space-y-6" : "space-y-4";
  const headerTitle = showHeader ? (
    <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Plan</h1>
  ) : (
    <h2 className="text-xl font-semibold text-[color:var(--text)]">Plan</h2>
  );

  return (
    <div className={containerClass}>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        {headerTitle}
        <div className="flex items-center gap-2">
          {status && (
            <span
              className={
                "inline-flex items-center rounded-full px-2 py-1 text-xs font-medium " +
                (status === "ready"
                  ? "bg-emerald-500/15 text-emerald-700 border border-emerald-500/30"
                  : status === "invalid"
                  ? "bg-rose-500/15 text-rose-700 border border-rose-500/30"
                  : "bg-amber-500/15 text-amber-700 border border-amber-500/30")
              }
              aria-label={`Statut: ${statusLabel}`}
            >
              {statusLabel}
            </span>
          )}
          <ClayButton
            type="button"
            onClick={async () => {
              try {
                setSubmitting(true);
                const res = await fetch(resolveApiUrl(`/plans/${planId}/auto_assign`), {
                  method: "POST",
                  headers: { ...defaultApiHeaders(), "X-Request-ID": crypto.randomUUID() },
                });
                if (!res.ok) {
                  let msg = res.statusText || `HTTP ${res.status}`;
                  try { const j = await res.json(); if (typeof j?.detail === "string") msg = j.detail; } catch {}
                  throw new Error(msg);
                }
                const j = await res.json();
                toast(`Recrutement et assignation: +${j.created} / ${j.updated} mis à jour`, "default");
              } catch (err) {
                toast((err as Error)?.message || "Échec du recrutement/assignation", "error");
              } finally {
                setSubmitting(false);
              }
            }}
            disabled={loading || submitting}
            aria-busy={submitting}
          >
            Recruter et assigner
          </ClayButton>
          {status !== "ready" && (
            <>
              <ClayButton type="button" onClick={submitValidation} disabled={loading || submitting} aria-busy={submitting}>
                Valider le plan
              </ClayButton>
              <ClayButton type="button" onClick={regeneratePlan} disabled={loading || submitting} aria-busy={submitting}>
                Régénérer avec Ollama
              </ClayButton>
            </>
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
            {llmInfo && (
              <div className="text-sm text-slate-600">LLM: {llmInfo.provider || "?"} — {llmInfo.model || "?"}</div>
            )}
            {viaFallback && (
              <div className="text-xs text-amber-700 bg-amber-500/15 border border-amber-500/30 inline-flex items-center rounded-full px-2 py-1 w-fit">
                Plan généré via fallback — le modèle était indisponible; essayez « Régénérer avec Ollama ».
              </div>
            )}
            <pre className="mt-2 max-h-[480px] overflow-auto rounded-xl bg-slate-50 p-3 text-xs text-slate-800">
{JSON.stringify(data.graph, null, 2)}
            </pre>
          </div>
        )}
        {!loading && !data && (
          <p className="text-sm text-red-600">Plan introuvable.</p>
        )}
      </ClayCard>

      {!!versions?.length && (
        <ClayCard className="p-4 space-y-3">
          <h2 className="text-base font-semibold">Versions du plan</h2>
          <div className="flex flex-wrap gap-2">
            {versions.map((v) => (
              <button
                key={v.numero_version}
                type="button"
                onClick={() => loadVersion(v.numero_version)}
                className={`px-2 py-1 text-xs rounded-full border ${selectedVersion === v.numero_version ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-200"}`}
                aria-pressed={selectedVersion === v.numero_version}
              >
                v{v.numero_version}
              </button>
            ))}
          </div>
          {selectedVersion && (
            <div className="space-y-2">
              <div className="text-sm text-slate-600">Version sélectionnée: v{selectedVersion}</div>
              <pre className="mt-2 max-h-[360px] overflow-auto rounded-xl bg-slate-50 p-3 text-xs text-slate-800">
{JSON.stringify(versionGraph, null, 2)}
              </pre>
              {diffLoading && <p className="text-xs text-slate-500">Calcul du diff…</p>}
              {diffError && <p className="text-xs text-rose-600">{diffError}</p>}
              {!diffLoading && !diffError && diff && (
                <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-3">
                  <h3 className="text-sm font-semibold text-[color:var(--text)]">
                    Diff vs v{diff.previous_version}
                  </h3>
                  <div className="grid gap-3 md:grid-cols-2">
                    <DiffSection title="Nœuds ajoutés" items={diff.added_nodes.map((node) => ({
                      id: String(node.id ?? ""),
                      label: String(node.title ?? node.id ?? "(sans titre)"),
                    }))} emptyLabel="Aucun ajout" ariaLabel="Nœuds ajoutés" />
                    <DiffSection title="Nœuds supprimés" items={diff.removed_nodes.map((node) => ({
                      id: String(node.id ?? ""),
                      label: String(node.title ?? node.id ?? "(sans titre)"),
                    }))} emptyLabel="Aucune suppression" ariaLabel="Nœuds supprimés" />
                    <DiffChangesSection title="Nœuds modifiés" changes={diff.changed_nodes} />
                    <DiffSection
                      title="Arêtes ajoutées"
                      items={diff.added_edges.map((edge) => ({
                        id: `${edge.source}->${edge.target}`,
                        label: `${edge.source} → ${edge.target}`,
                      }))}
                      emptyLabel="Aucune arête ajoutée"
                      ariaLabel="Arêtes ajoutées"
                    />
                    <DiffSection
                      title="Arêtes supprimées"
                      items={diff.removed_edges.map((edge) => ({
                        id: `${edge.source}->${edge.target}`,
                        label: `${edge.source} → ${edge.target}`,
                      }))}
                      emptyLabel="Aucune arête supprimée"
                      ariaLabel="Arêtes supprimées"
                    />
                  </div>
                </div>
              )}
              {!diffLoading && !diffError && !diff && selectedVersion > 1 && (
                <p className="text-xs text-slate-500">Aucun diff disponible pour cette version.</p>
              )}
              {!diffLoading && !diffError && selectedVersion === 1 && (
                <p className="text-xs text-slate-500">Version initiale — aucune version précédente à comparer.</p>
              )}
            </div>
          )}
        </ClayCard>
      )}
    </div>
  );
}

interface DiffItemProps {
  title: string;
  items: Array<{ id: string; label: string }>;
  emptyLabel: string;
  ariaLabel: string;
}

function DiffSection({ title, items, emptyLabel, ariaLabel }: DiffItemProps) {
  return (
    <div className="space-y-1">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-secondary">{title}</h4>
      {items.length === 0 ? (
        <p className="text-xs text-slate-500">{emptyLabel}</p>
      ) : (
        <ul className="text-xs text-slate-700 space-y-1" aria-label={ariaLabel}>
          {items.map((item) => (
            <li key={item.id} className="rounded bg-slate-100 px-2 py-1 text-slate-700">
              <span className="font-semibold">{item.id}</span> — {item.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

interface DiffChangesSectionProps {
  title: string;
  changes: PlanVersionDiff["changed_nodes"];
}

function DiffChangesSection({ title, changes }: DiffChangesSectionProps) {
  return (
    <div className="space-y-1 md:col-span-2">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-secondary">{title}</h4>
      {changes.length === 0 ? (
        <p className="text-xs text-slate-500">Aucune modification.</p>
      ) : (
        <ul className="space-y-2 text-xs text-slate-700">
          {changes.map((change) => (
            <li key={change.id} className="rounded bg-slate-100 px-2 py-1">
              <p className="font-semibold text-slate-800">{change.id}</p>
              <ul className="mt-1 space-y-1">
                {Object.entries(change.changes).map(([field, values]) => (
                  <li key={field} className="flex flex-col rounded border border-slate-200 bg-white px-2 py-1">
                    <span className="text-[10px] uppercase tracking-wide text-slate-500">{field}</span>
                    <span className="text-slate-600">Avant: {formatDiffValue(values.previous)}</span>
                    <span className="text-slate-800">Après: {formatDiffValue(values.current)}</span>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function formatDiffValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}
