"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { ClayButton } from "@/components/ds/ClayButton";
import { useToast } from "@/components/ds/Toast";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { PlanDetailView } from "@/features/plans/PlanDetailView";

export default function NewTaskPage() {
  const router = useRouter();
  const toast = useToast();
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [prompt, setPrompt] = React.useState("");
  const [agents, setAgents] = React.useState<string[]>(["writer-pro", "qa-bot", "indexer-1"]);
  const [defaultAgent, setDefaultAgent] = React.useState<string>("writer-pro");
  // Étapes du flux
  const [createdTaskId, setCreatedTaskId] = React.useState<string | null>(null);
  const [createdPlanId, setCreatedPlanId] = React.useState<string | null>(null);
  const [taskValidated, setTaskValidated] = React.useState(false);
  const [planNodes, setPlanNodes] = React.useState<Array<{ id: string; title: string }>>([]);
  const [assignments, setAssignments] = React.useState<Array<{ node_id: string; title: string; role: string; agent_id?: string; llm_backend?: string; llm_model?: string; params?: Record<string, unknown>; prompt?: string }>>([]);
  const [editAgentId, setEditAgentId] = React.useState<string | null>(null);
  const [editAgent, setEditAgent] = React.useState<{ id: string; name: string; role: string; domain: string; default_model?: string | null; prompt_system?: string | null; prompt_user?: string | null; is_active: boolean } | null>(null);
  const [savingAgent, setSavingAgent] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [recurring, setRecurring] = React.useState(false);
  const [frequency, setFrequency] = React.useState<"Quotidien" | "Hebdomadaire" | "Mensuel">("Quotidien");
  const [time, setTime] = React.useState("09:00");
  const [weekday, setWeekday] = React.useState("Lun");
  const [monthday, setMonthday] = React.useState(1);

  // Plan (suggestion) — non imposé à l'API, utilisé pour guider la génération via la description
  type PlanNode = { id: string; parentId?: string | null; title: string; order: number; agentId?: string | null };
  const [plan, setPlan] = React.useState<PlanNode[]>([]);

  // Empêche les gestionnaires clavier globaux d'interférer avec la saisie
  const stopKeyDownPropagation = React.useCallback((e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    e.stopPropagation();
  }, []);

  // Hack de stabilisation du caret en cas de remount inattendu
  const stabilizeCaret = React.useCallback((id: string) => (
    e: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    try {
      const el = e.currentTarget as HTMLInputElement | HTMLTextAreaElement;
      const start = (el as HTMLInputElement | HTMLTextAreaElement).selectionStart ?? el.value.length;
      const end = (el as HTMLInputElement | HTMLTextAreaElement).selectionEnd ?? start;
      requestAnimationFrame(() => {
        const next = document.getElementById(id) as HTMLInputElement | HTMLTextAreaElement | null;
        if (next) {
          try {
            next.focus({ preventScroll: true } as any);
            if (typeof (next as HTMLInputElement | HTMLTextAreaElement).setSelectionRange === 'function') {
              (next as HTMLInputElement | HTMLTextAreaElement).setSelectionRange(start, end);
            }
          } catch {}
        }
      });
    } catch {}
  }, []);

  // Aperçu basé sur l'état courant (live)

  React.useEffect(() => {
    // preset simple
    if (plan.length === 0) {
      setPlan([
        { id: uid(), parentId: null, title: "Collecte des données", order: 0 },
        { id: uid(), parentId: null, title: "Analyse & rédaction", order: 1 },
        { id: uid(), parentId: null, title: "QA & corrections", order: 2 },
      ]);
    }
  }, []);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const t = title.trim();
    if (!t) {
      toast("Le titre est requis", "error");
      return;
    }
    // Concatène les hints optionnels dans la description pour guider la génération
    const suggestedSteps = plan
      .filter((n) => !n.parentId)
      .sort((a, b) => a.order - b.order)
      .map((n, i) => `  ${i + 1}. ${n.title}${n.agentId ? ` (agent: ${n.agentId})` : ""}`)
      .join("\n");
    const extra: string[] = [];
    if (prompt.trim()) extra.push(`Prompt:\n${prompt.trim()}`);
    if (recurring) {
      const when = frequency === "Quotidien" ? `tous les jours à ${time}` : frequency === "Hebdomadaire" ? `${weekday} à ${time}` : `jour ${monthday} à ${time}`;
      extra.push(`Récurrence: ${when}`);
    }
    if (suggestedSteps) extra.push(`Plan suggéré:\n${suggestedSteps}`);
    const finalDescription = [description.trim(), ...extra].filter(Boolean).join("\n\n");
    try {
      setSubmitting(true);
      const reqId = (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const res = await fetch(resolveApiUrl("/tasks"), {
        method: "POST",
        headers: { ...defaultApiHeaders(), "Content-Type": "application/json", "X-Request-ID": reqId },
        body: JSON.stringify({ title: t, description: finalDescription || undefined }),
      });
      let body: any = null;
      try { body = await res.json(); } catch {}
      if (!res.ok) {
        let msg = res.statusText || `HTTP ${res.status}`;
        if (res.status === 401) {
          msg = "Accès refusé (401). Vérifiez NEXT_PUBLIC_API_KEY côté UI et API_KEY côté backend.";
        } else if (res.status === 409) {
          msg = "Conflit: une tâche avec ce titre existe déjà.";
        } else if (body && typeof body.detail === "string") {
          msg = body.detail;
        } else if (body && Array.isArray(body.detail) && body.detail.length > 0) {
          msg = body.detail[0]?.msg || msg;
        }
        throw new Error(msg);
      }
      if (body && body.id) {
        toast("Tâche créée", "default");
        setCreatedTaskId(body.id as string);
        // Laisser l'utilisateur déclencher la génération du plan (Étape 2)
        return;
      }
      toast("Tâche créée", "default");
      setCreatedTaskId(String(body?.id || ""));
    } catch (error) {
      const message = (error as Error)?.message || "Échec de la création";
      toast(message, "error");
    } finally {
      setSubmitting(false);
    }
  };

  // Panel style inspiré du Dashboard
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

  return (
    <main className="text-[color:var(--text)]">
      <header className="relative sticky top-0 z-20 overflow-hidden border-b border-white/10 bg-[#0e1116]/80 backdrop-blur">
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -top-20 left-1/3 h-48 w-[36rem] rounded-full blur-3xl" style={{ background: "rgba(99,102,241,0.18)" }} />
          <div className="absolute -top-16 right-1/4 h-40 w-[28rem] rounded-full blur-3xl" style={{ background: "rgba(79,220,197,0.14)" }} />
        </div>
        <div className="mx-auto max-w-7xl px-6 py-4">
          <h1 className="text-2xl font-semibold tracking-tight">Nouvelle tâche</h1>
          <p className="mt-1 text-sm text-secondary">Renseignez le contexte. Soumettez au superviseur pour générer un plan, puis validez et démarrez.</p>
          <div className="mt-2 h-[2px] w-full bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Colonne gauche: infos */}
        <Panel className="lg:col-span-2 p-5 space-y-4">
          <form onSubmit={onSubmit} className="space-y-5" aria-disabled={Boolean(createdTaskId)}>
            <div className="space-y-2">
              <label htmlFor="task-title" className="block text-sm font-medium">Titre</label>
              <input
                id="task-title"
                name="title"
                defaultValue={title}
                onChange={(e) => setTitle(e.target.value)}
                onKeyDownCapture={stopKeyDownPropagation}
                onInputCapture={stabilizeCaret('task-title')}
                className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 outline-none focus:border-white/20"
                placeholder="Ex. Rédiger note de cadrage"
                required
                disabled={Boolean(createdTaskId)}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="task-desc" className="block text-sm font-medium">Description (optionnelle)</label>
              <textarea
                id="task-desc"
                name="description"
                defaultValue={description}
                onChange={(e) => setDescription(e.target.value)}
                onKeyDownCapture={stopKeyDownPropagation}
                onInputCapture={stabilizeCaret('task-desc')}
                rows={4}
                className="w-full resize-y rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 outline-none focus:border-white/20"
                placeholder="Contexte, objectifs, contraintes…"
                disabled={Boolean(createdTaskId)}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="task-prompt" className="block text-sm font-medium">Prompt (hint LLM, optionnel)</label>
              <textarea
                id="task-prompt"
                defaultValue={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDownCapture={stopKeyDownPropagation}
                onInputCapture={stabilizeCaret('task-prompt')}
                rows={4}
                className="w-full resize-y rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 outline-none focus:border-white/20"
                placeholder="Décrivez l'objectif, le contexte, les contraintes…"
                disabled={Boolean(createdTaskId)}
              />
            </div>

            <fieldset className="space-y-3">
              <legend className="text-sm font-medium">Récurrence</legend>
              <button
                type="button"
                role="switch"
                aria-checked={recurring}
                onClick={() => setRecurring((v) => !v)}
                className="flex w-full items-center justify-between rounded-2xl border border-white/10 bg-white/[0.02] px-4 py-3"
                disabled={Boolean(createdTaskId)}
              >
                <span className="text-sm">Exécuter automatiquement</span>
                <span aria-hidden className="relative h-6 w-12 rounded-full bg-slate-700">
                  <span className="absolute top-1 h-4 w-4 rounded-full bg-white transition-all" style={{ left: recurring ? "calc(100% - 1.5rem)" : "0.25rem" }} />
                </span>
              </button>
              {recurring && (
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="mb-1 block text-xs text-white/60">Fréquence</label>
                    <select value={frequency} onChange={(e) => setFrequency(e.target.value as any)} className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2" disabled={Boolean(createdTaskId)}>
                      <option value="Quotidien">Quotidien</option>
                      <option value="Hebdomadaire">Hebdomadaire</option>
                      <option value="Mensuel">Mensuel</option>
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs text-white/60">Heure</label>
                    <input type="time" value={time} onChange={(e) => setTime(e.target.value)} className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2" disabled={Boolean(createdTaskId)} />
                  </div>
                  {frequency === "Hebdomadaire" && (
                    <div>
                      <label className="mb-1 block text-xs text-white/60">Jour</label>
                      <select value={weekday} onChange={(e) => setWeekday(e.target.value)} className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2" disabled={Boolean(createdTaskId)}>
                        {["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"].map((j) => (<option key={j} value={j}>{j}</option>))}
                      </select>
                    </div>
                  )}
                  {frequency === "Mensuel" && (
                    <div>
                      <label className="mb-1 block text-xs text-white/60">Jour du mois</label>
                      <input type="number" min={1} max={28} value={monthday} onChange={(e) => setMonthday(Number(e.target.value))} className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2" disabled={Boolean(createdTaskId)} />
                    </div>
                  )}
                </div>
              )}
            </fieldset>

            <div className="flex flex-wrap items-center gap-2">
              <ClayButton type="submit" disabled={submitting || Boolean(createdTaskId)} aria-busy={submitting}>
                {createdTaskId ? "Tâche créée" : "Valider la tâche"}
              </ClayButton>
              {createdTaskId && (
                <button
                  type="button"
                  role="switch"
                  aria-checked={taskValidated}
                  onClick={() => setTaskValidated((v) => !v)}
                  className="inline-flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.02] px-4 py-2 text-sm"
                >
                  <span>Validation finale</span>
                  <span aria-hidden className="relative ml-3 h-6 w-12 rounded-full bg-slate-700">
                    <span className="absolute top-1 h-4 w-4 rounded-full bg-white transition-all" style={{ left: taskValidated ? "calc(100% - 1.5rem)" : "0.25rem" }} />
                  </span>
                </button>
              )}
              <ClayButton type="button" variant="outline" onClick={() => router.back()} disabled={submitting}>
                Annuler
              </ClayButton>
            </div>
          </form>
        </Panel>

        {/* Colonne droite */}
        <Panel className="lg:col-span-1 p-5 space-y-4">
          {/* Aperçu – non lié au plan */}
          <div className="space-y-2">
            <div className="text-xs text-secondary">Aperçu</div>
            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3 text-sm" aria-live="off" role="presentation" tabIndex={-1}>
              <div className="text-white/80">{title || "Titre…"}</div>
              <div className="mt-1 text-secondary line-clamp-3 whitespace-pre-wrap">{(description + (prompt ? "\n\n" + prompt : "")).trim() || "Description / prompt (optionnel)"}</div>
            </div>
          </div>

          {/* Paramètres plan & suggestions – cachés tant que la tâche n'est pas validée */}
          {createdTaskId && taskValidated && (
            <>
              <div className="space-y-2">
                <label className="block text-sm font-medium">Agent par défaut</label>
                <div className="flex gap-2">
                  <select value={defaultAgent} onChange={(e) => setDefaultAgent(e.target.value)} className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2">
                    {agents.map((a) => (<option key={a} value={a}>{a}</option>))}
                  </select>
                  <button type="button" onClick={() => { const name = window.prompt("Nom du nouvel agent"); if (name) setAgents((arr) => (arr.includes(name) ? arr : [...arr, name])); }} className="whitespace-nowrap rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white/90 hover:bg-white/[0.07]">+ Nouvel agent</button>
                </div>
              </div>

              <details className="rounded-2xl border border-white/10 bg-white/[0.02] p-3">
                <summary className="cursor-pointer text-sm font-medium">Avancé — Suggestions d'étapes (non obligatoires)</summary>
                <p className="mt-2 text-xs text-secondary">Ces suggestions aident le superviseur à structurer le plan. Elles ne seront pas affichées comme plan tant que la génération n'est pas effectuée.</p>
                <div className="mt-3 rounded-xl border border-white/10 bg-white/[0.02] p-3 max-h-[300px] overflow-auto">
                  <PlanEditorInline value={plan} onChange={(nodes) => setPlan(nodes)} defaultAgent={defaultAgent} />
                </div>
              </details>
            </>
          )}

          {/* Étape 2: Générer le plan / Auto-assign */}
          {createdTaskId && taskValidated && !createdPlanId && (
            <div className="space-y-2">
              <div className="text-sm text-secondary">Étape 2 — Générer le plan</div>
              <p className="text-xs text-secondary">Génère un plan à partir des informations de la tâche, puis assigne automatiquement des agents.</p>
              <ClayButton
                type="button"
                onClick={async () => {
                  try {
                    setSubmitting(true);
                    // 1) Générer le plan
                    const gen = await fetch(resolveApiUrl(`/tasks/${createdTaskId}/plan`), { method: "POST", headers: { ...defaultApiHeaders() } });
                    if (!gen.ok) {
                      let msg = gen.statusText || `HTTP ${gen.status}`;
                      try { const j = await gen.json(); if (typeof j?.detail === "string") msg = j.detail; } catch {}
                      throw new Error(msg);
                    }
                    const payload = await gen.json() as { plan_id: string; status: string; graph?: { plan?: any[]; nodes?: any[] } };
                    const pid = payload.plan_id;
                    // Utiliser le graph renvoyé pour l'aperçu immédiat
                    let nodesForMap: Array<{ id: string; title: string }> = [];
                    try {
                      const nodesRaw = (payload.graph?.plan || payload.graph?.nodes || []) as any[];
                      if (Array.isArray(nodesRaw)) {
                        nodesForMap = nodesRaw.map((n) => ({ id: String(n.id), title: String((n as any).title || (n as any).id) }));
                        setPlanNodes(nodesForMap);
                      }
                    } catch {}

                    // 2) Auto-assign avec X-Request-ID et petites tentatives de retry si 404
                    const reqId = (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
                    let recResp: Response | null = null;
                    let attempts = 0;
                    let lastError: string | null = null;
                    while (attempts < 3) {
                      attempts += 1;
                      const rr = await fetch(resolveApiUrl(`/plans/${pid}/auto_assign`), { method: "POST", headers: { ...defaultApiHeaders(), "X-Request-ID": reqId } });
                      if (rr.ok) { recResp = rr; break; }
                      let msg = rr.statusText || `HTTP ${rr.status}`;
                      try { const j = await rr.json(); if (typeof j?.detail === "string") msg = j.detail; } catch {}
                      if (rr.status === 404) {
                        lastError = msg;
                        await new Promise((r) => setTimeout(r, 180));
                        continue;
                      }
                      // 401/403/422 etc: remonter directement
                      throw new Error(msg);
                    }
                    if (!recResp) throw new Error(lastError || "Plan introuvable pour l'assignation (réessayez)." );
                    const recBody = await recResp.json() as { created?: number; updated?: number; items?: Array<{ node_id: string; role: string; agent_id?: string; llm_backend?: string; llm_model?: string; params?: Record<string, unknown> }> };
                    const nodeMap = new Map((nodesForMap.length ? nodesForMap : planNodes).map((n) => [n.id, n.title]));
                    const mapped = (recBody.items || []).map((it) => ({ ...it, title: nodeMap.get(it.node_id) || it.node_id, prompt: typeof it.params?.prompt === 'string' ? String(it.params?.prompt) : '' }));
                    setAssignments(mapped);
                    setCreatedPlanId(pid);
                    const created = typeof recBody.created === 'number' ? recBody.created : (recBody.items ? recBody.items.length : 0);
                    const updated = typeof recBody.updated === 'number' ? recBody.updated : 0;
                    toast(`Plan généré. Agents créés: ${created}${updated ? ", mis à jour: " + updated : ""}`, "default");
                  } catch (e) {
                    const msg = (e as Error)?.message || "Échec de la génération/assignation";
                    if (/401|Invalid or missing API key/i.test(msg)) {
                      toast("Accès refusé. Vérifiez NEXT_PUBLIC_API_KEY côté UI et API_KEY côté backend.", "error");
                    } else if (/RBAC|403/i.test(msg)) {
                      toast("Rôle insuffisant pour l'auto-assignation. Utilisez un rôle 'editor' ou 'admin'.", "error");
                    } else {
                      toast(msg, "error");
                    }
                  } finally {
                    setSubmitting(false);
                  }
                }}
                disabled={submitting}
                aria-busy={submitting}
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Génération...
                  </>
                ) : (
                  "Générer le plan"
                )}
              </ClayButton>
            </div>
          )}
        </Panel>
      </div>

      {/* Étape 3: Affichage/édition/validation/lancement */}
      {createdTaskId && taskValidated && createdPlanId && (
        <div className="mx-auto max-w-7xl px-6 grid grid-cols-1 gap-6 lg:grid-cols-3 pb-6">
          <Panel className="lg:col-span-2 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Plan</h2>
              <div className="flex items-center gap-2">
                <ClayButton
                  type="button"
                  onClick={async () => {
                    try {
                      setSubmitting(true);
                      const res = await fetch(resolveApiUrl(`/plans/${createdPlanId}/submit_for_validation`), {
                        method: "POST",
                        headers: { ...defaultApiHeaders(), "Content-Type": "application/json" },
                        body: JSON.stringify({ validated: true, errors: [] }),
                      });
                      if (!res.ok) throw new Error(res.statusText || `HTTP ${res.status}`);
                      const run = await fetch(resolveApiUrl(`/tasks/${createdTaskId}/start`), { method: "POST", headers: { ...defaultApiHeaders() } });
                      if (!run.ok) throw new Error(run.statusText || `HTTP ${run.status}`);
                      const body = await run.json() as { run_id: string };
                      toast("Run démarré", "default");
                      router.push(`/runs/${body.run_id}`);
                    } catch (e) {
                      toast((e as Error)?.message || "Échec de la validation/démarrage", "error");
                    } finally {
                      setSubmitting(false);
                    }
                  }}
                  disabled={submitting}
                  aria-busy={submitting}
                >
                  Valider et démarrer
                </ClayButton>
              </div>
            </div>
            <PlanDetailView planId={createdPlanId} showHeader={false} />
          </Panel>
          <Panel className="lg:col-span-1 p-5 space-y-3">
            <h3 className="text-base font-semibold">Modifier le plan (optionnel)</h3>
            <p className="text-sm text-secondary">Ajustez les étapes puis appliquez pour créer une nouvelle version rattachée à la tâche.</p>
            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-3">
              <PlanEditorInline value={plan} onChange={setPlan} defaultAgent={defaultAgent} />
            </div>
            <div className="flex items-center justify-end gap-2">
              <ClayButton
                type="button"
                variant="outline"
                onClick={async () => {
                  try {
                    setSubmitting(true);
                    // Transforme le plan local en PlanGraph minimal
                    const nodes = plan
                      .filter((n) => n.title && n.title.trim())
                      .sort((a, b) => a.order - b.order)
                      .map((n) => ({
                        id: n.id,
                        title: n.title.trim(),
                        deps: [],
                        suggested_agent_role: "executor",
                        acceptance: [],
                        risks: [],
                        assumptions: [],
                        notes: [],
                      }));
                    const payload = { task_id: createdTaskId, graph: { version: "1.0", plan: nodes, edges: [] }, status: "draft" };
                    const res = await fetch(resolveApiUrl(`/plans`), {
                      method: "POST",
                      headers: { ...defaultApiHeaders(), "Content-Type": "application/json" },
                      body: JSON.stringify(payload),
                    });
                    if (!res.ok) {
                      let msg = res.statusText || `HTTP ${res.status}`;
                      try { const j = await res.json(); if (typeof j?.detail === "string") msg = j.detail; } catch {}
                      throw new Error(msg);
                    }
                    const body = await res.json() as { plan_id: string };
                    // Auto-assign sur le nouveau plan
                    const rec = await fetch(resolveApiUrl(`/plans/${body.plan_id}/auto_assign`), { method: "POST", headers: { ...defaultApiHeaders(), "X-Request-ID": crypto.randomUUID() } });
                    if (!rec.ok) throw new Error(rec.statusText || `HTTP ${rec.status}`);
                    setCreatedPlanId(body.plan_id);
                    toast("Plan mis à jour et agents assignés", "default");
                  } catch (e) {
                    toast((e as Error)?.message || "Échec de l'application des modifications", "error");
                  } finally {
                    setSubmitting(false);
                  }
                }}
                disabled={submitting}
                aria-busy={submitting}
              >
                Appliquer les modifications
              </ClayButton>
            </div>
            <div className="pt-3">
              <h4 className="text-sm font-semibold">Affectations</h4>
              <p className="text-xs text-secondary">Chaque étape peut être gérée par un manager/executant avec son prompt dédié.</p>
              <div className="mt-2 max-h-[280px] overflow-auto rounded-xl border border-white/10">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 z-10 bg-white/5 text-left text-xs text-white/60 backdrop-blur">
                    <tr>
                      <th className="px-3 py-2">Nœud</th>
                      <th className="px-3 py-2">Rôle</th>
                      <th className="px-3 py-2">Agent</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignments.map((a, idx) => (
                      <React.Fragment key={`${a.node_id}-${idx}`}>
                        <tr className={idx % 2 ? "bg-white/[0.02]" : ""}>
                          <td className="px-3 py-2 font-medium text-white/90">{a.title}</td>
                          <td className="px-3 py-2">
                            <select
                              value={a.role}
                              onChange={(e) => setAssignments((arr) => arr.map((it) => it.node_id === a.node_id ? { ...it, role: e.target.value } : it))}
                              className="rounded-md border border-white/10 bg-white/[0.02] px-2 py-1 text-xs"
                            >
                              <option value="manager">manager</option>
                              <option value="executor">executor</option>
                            </select>
                          </td>
                        <td className="px-3 py-2 text-white/80">
                          <div className="flex items-center gap-2">
                            <span>{a.agent_id || "(auto)"}</span>
                            {a.agent_id ? (
                              <button
                                type="button"
                                className="rounded border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]"
                                onClick={async () => {
                                  try {
                                    setEditAgentId(a.agent_id!);
                                    setEditAgent(null);
                                    const res = await fetch(resolveApiUrl(`/agents/${a.agent_id}`), { headers: { ...defaultApiHeaders(), Accept: 'application/json' } });
                                    if (res.ok) {
                                      const body = await res.json();
                                      setEditAgent({
                                        id: body.id,
                                        name: body.name,
                                        role: body.role,
                                        domain: body.domain,
                                        default_model: body.default_model ?? null,
                                        prompt_system: body.prompt_system ?? null,
                                        prompt_user: body.prompt_user ?? null,
                                        is_active: !!body.is_active,
                                      });
                                    }
                                  } catch {}
                                }}
                              >
                                Modifier
                              </button>
                            ) : null}
                          </div>
                        </td>
                        </tr>
                        <tr className={idx % 2 ? "bg-white/[0.02]" : ""}>
                          <td className="px-3 pb-3 pt-0" colSpan={3}>
                            <label className="mb-1 block text-xs text-white/60" htmlFor={`prompt-${a.node_id}`}>Prompt (optionnel)</label>
                            <textarea
                              id={`prompt-${a.node_id}`}
                              value={a.prompt || ''}
                              onChange={(e) => setAssignments((arr) => arr.map((it) => it.node_id === a.node_id ? { ...it, prompt: e.target.value } : it))}
                              onKeyDownCapture={(e) => e.stopPropagation()}
                              rows={2}
                              className="w-full resize-y rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 text-xs outline-none focus:border-white/20"
                              placeholder="Décrivez le comportement attendu de l'agent pour cette étape"
                            />
                          </td>
                        </tr>
                      </React.Fragment>
                    ))}
                    {assignments.length === 0 && (
                      <tr>
                        <td className="px-3 py-2 text-secondary" colSpan={3}>Aucune affectation pour le moment</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
              {assignments.length > 0 && (
                <div className="mt-2 flex items-center justify-end">
                  <ClayButton
                    type="button"
                    variant="outline"
                    onClick={async () => {
                      try {
                        setSubmitting(true);
                        const payload = { items: assignments.map(({ node_id, role, agent_id, llm_backend, llm_model, prompt }) => ({ node_id, role, agent_id, llm_backend, llm_model, params: prompt ? { prompt } : undefined })) };
                        const res = await fetch(resolveApiUrl(`/plans/${createdPlanId}/assignments`), {
                          method: "POST",
                          headers: { ...defaultApiHeaders(), "Content-Type": "application/json" },
                          body: JSON.stringify(payload),
                        });
                        if (!res.ok) throw new Error(res.statusText || `HTTP ${res.status}`);
                        toast("Affectations mises à jour", "default");
                      } catch (e) {
                        toast((e as Error)?.message || "Échec de la mise à jour des affectations", "error");
                      } finally {
                        setSubmitting(false);
                      }
                    }}
                  >
                    Appliquer les affectations
                  </ClayButton>
                </div>
              )}
            </div>
          </Panel>
        </div>
      )}
      {editAgentId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal>
          <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-[#141821] p-4 shadow-2xl">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Modifier l'agent</h3>
              <button className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-sm hover:bg-white/[0.07]" onClick={() => { setEditAgentId(null); setEditAgent(null); }}>Fermer</button>
            </div>
            {!editAgent ? (
              <p className="text-sm text-secondary">Chargement…</p>
            ) : (
              <form className="space-y-3" onSubmit={async (e) => {
                e.preventDefault();
                try {
                  setSavingAgent(true);
                  const payload = {
                    name: editAgent.name,
                    role: editAgent.role,
                    domain: editAgent.domain,
                    default_model: editAgent.default_model ?? null,
                    prompt_system: editAgent.prompt_system ?? null,
                    prompt_user: editAgent.prompt_user ?? null,
                    is_active: editAgent.is_active,
                  };
                  const res = await fetch(resolveApiUrl(`/agents/${editAgent.id}`), { method: 'PATCH', headers: { ...defaultApiHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                  if (!res.ok) throw new Error(res.statusText || `HTTP ${res.status}`);
                } catch (e) {
                  toast((e as Error)?.message || 'Échec de la mise à jour de l\'agent', 'error');
                } finally {
                  setSavingAgent(false);
                  setEditAgentId(null);
                }
              }}>
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm">Nom</label>
                    <input className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 outline-none focus:border-white/20" value={editAgent.name} onChange={(e) => setEditAgent({ ...editAgent, name: e.target.value })} />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm">Rôle</label>
                    <input className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 outline-none focus:border-white/20" value={editAgent.role} onChange={(e) => setEditAgent({ ...editAgent, role: e.target.value })} />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm">Domaine</label>
                    <input className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 outline-none focus:border-white/20" value={editAgent.domain} onChange={(e) => setEditAgent({ ...editAgent, domain: e.target.value })} />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm">Modèle par défaut</label>
                    <input className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 outline-none focus:border-white/20" value={editAgent.default_model || ''} onChange={(e) => setEditAgent({ ...editAgent, default_model: e.target.value })} />
                  </div>
                </div>
                <div>
                  <label className="mb-1 block text-sm">Prompt système</label>
                  <textarea rows={3} className="w-full resize-y rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 outline-none focus:border-white/20" value={editAgent.prompt_system || ''} onChange={(e) => setEditAgent({ ...editAgent, prompt_system: e.target.value })} />
                </div>
                <div>
                  <label className="mb-1 block text-sm">Prompt utilisateur</label>
                  <textarea rows={3} className="w-full resize-y rounded-xl border border-white/10 bg-white/[0.02] px-3 py-2 outline-none focus:border-white/20" value={editAgent.prompt_user || ''} onChange={(e) => setEditAgent({ ...editAgent, prompt_user: e.target.value })} />
                </div>
                <div className="flex items-center justify-between">
                  <label className="inline-flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={editAgent.is_active} onChange={(e) => setEditAgent({ ...editAgent, is_active: e.target.checked })} />
                    Actif
                  </label>
                  <ClayButton type="submit" disabled={savingAgent} aria-busy={savingAgent}>Enregistrer</ClayButton>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

// UI utils
const ACCENT = "#4FD1C5";

function uid(prefix = "n") {
  return `${prefix}${Math.random().toString(36).slice(2, 8)}`;
}

function sortNodes(nodes: Array<{ parentId?: string | null; order: number }>) {
  return [...nodes].sort((a, b) => (a.parentId === b.parentId ? a.order - b.order : (a.parentId || "").localeCompare(b.parentId || "")));
}

function PlanEditorInline({ value, onChange, defaultAgent }: { value: Array<{ id: string; parentId?: string | null; title: string; order: number; agentId?: string | null }>; onChange: (nodes: any[]) => void; defaultAgent?: string }) {
  const [local, setLocal] = React.useState(() => sortNodes(value));
  React.useEffect(() => setLocal(sortNodes(value)), [value]);
  const agentOptions = React.useMemo(() => Array.from(new Set([defaultAgent || "writer-pro", "qa-bot", "indexer-1", ...((local.map((n) => n.agentId).filter(Boolean) as string[]))])), [defaultAgent, local]);
  const update = (next: any[]) => { const sorted = sortNodes(next); setLocal(sorted); onChange(sorted); };
  const addRoot = () => { const siblings = local.filter((n) => !n.parentId); update([...local, { id: uid(), parentId: null, title: "Nouvelle étape", order: siblings.length }]); };
  const addChild = (parentId: string) => { const siblings = local.filter((n) => n.parentId === parentId); update([...local, { id: uid(), parentId, title: "Sous-tâche", order: siblings.length }]); };
  const rename = (id: string, title: string) => update(local.map((n) => (n.id === id ? { ...n, title } : n)));
  const remove = (id: string) => { const toRemove = new Set<string>([id]); let changed = true; while (changed) { changed = false; for (const n of local) { if (n.parentId && toRemove.has(n.parentId) && !toRemove.has(n.id)) { toRemove.add(n.id); changed = true; } } } update(local.filter((n) => !toRemove.has(n.id))); };
  const move = (id: string, dir: -1 | 1) => { const node = local.find((n: any) => n.id === id); if (!node) return; const siblings = local.filter((n: any) => (node.parentId ? n.parentId === node.parentId : !n.parentId)).sort((a: any, b: any) => a.order - b.order); const idx = siblings.findIndex((s: any) => s.id === id); const swap = siblings[idx + dir]; if (!swap) return; const next = local.map((n: any) => (n.id === node.id ? { ...n, order: swap.order } : n.id === swap.id ? { ...n, order: node.order } : n)); update(next); };
  const Row = ({ n, depth }: { n: any; depth: number }) => (
    <div className="group mb-1 flex items-center gap-2 rounded-lg px-2 py-1 hover:bg-white/5" style={{ marginLeft: depth * 16 }}>
      <div className="text-white/40">{depth > 0 ? "↳" : "•"}</div>
      <input value={n.title} onChange={(e) => rename(n.id, e.target.value)} onKeyDownCapture={(e) => e.stopPropagation()} className="w-full rounded-md border border-white/10 bg-transparent px-2 py-1 text-sm outline-none focus:border-white/20" />
      <select value={n.agentId ?? ""} onChange={(e) => update(local.map((m: any) => (m.id === n.id ? { ...m, agentId: e.target.value || undefined } : m)))} className="rounded-md border border-white/10 bg-transparent px-2 py-1 text-xs text-white/80">
        <option value="">— agent —</option>
        {agentOptions.map((a) => (
          <option key={a} value={a}>{a}</option>
        ))}
      </select>
      <button className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]" onClick={() => { const name = window.prompt("Nom du nouvel agent"); if (name) { update(local.map((m: any) => (m.id === n.id ? { ...m, agentId: name } : m))); } }}>+ agent</button>
      <div className="invisible ml-2 flex items-center gap-1 group-hover:visible">
        <button className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]" onClick={() => addChild(n.id)}>+ sous-tâche</button>
        <button className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]" onClick={() => move(n.id, -1)}>↑</button>
        <button className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]" onClick={() => move(n.id, +1)}>↓</button>
        <button className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs text-red-300 hover:bg-white/[0.07]" onClick={() => remove(n.id)}>Supprimer</button>
      </div>
    </div>
  );
  const render = (parentId: string | null, depth: number) => {
    const items = local.filter((n: any) => (parentId ? n.parentId === parentId : !n.parentId)).sort((a: any, b: any) => a.order - b.order);
    return (
      <div>
        {items.map((n: any) => (
          <div key={n.id}>
            <Row n={n} depth={depth} />
            {render(n.id, depth + 1)}
          </div>
        ))}
        {depth === 0 && (
          <button className="mt-1 rounded-md border border-white/10 bg-white/[0.04] px-2 py-1 text-xs hover:bg-white/[0.07]" onClick={addRoot}>+ étape racine</button>
        )}
      </div>
    );
  };
  return <div>{render(null, 0)}</div>;
}
