import type { Status } from "@/ui/theme";
import { resolveApiUrl, defaultApiHeaders } from "@/lib/config";
import { fetchJson, type FetchOptions } from "@/lib/http";

export interface ApiPageLinks {
  prev?: string | null;
  next?: string | null;
}

export interface ApiPage<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  _links?: ApiPageLinks | null;
  links?: ApiPageLinks | null;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  domain: string;
  prompt_system?: string | null;
  prompt_user?: string | null;
  default_model?: string | null;
  config: Record<string, unknown>;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RunListItem {
  id: string;
  title: string;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
}

export interface RunSummary {
  nodes_total: number;
  nodes_completed: number;
  nodes_failed: number;
  artifacts_total: number;
  events_total: number;
  duration_ms?: number | null;
  llm_prompt_tokens?: number | null;
  llm_completion_tokens?: number | null;
  llm_total_tokens?: number | null;
  llm_request_count?: number | null;
  llm_avg_latency_ms?: number | null;
  llm_p95_latency_ms?: number | null;
}

export interface RunDetail {
  id: string;
  title: string;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  meta?: Record<string, unknown> | null;
  summary?: RunSummary | null;
  dag?: {
    nodes: NodeListItem[];
    edges?: Array<{ source: string; target: string }>;
  } | null;
  events?: Array<{
    id: string;
    run_id: string;
    node_id?: string | null;
    level: string;
    message: string;
    timestamp: string;
    request_id?: string | null;
  }> | null;
  artifacts?: ArtifactSummary[] | null;
}

export interface ArtifactSummary {
  id: string;
  node_id: string;
  type: string;
  path?: string | null;
  content?: string | null;
  summary?: string | null;
  created_at: string;
  preview?: string | null;
}

export interface RunActionResponse {
  status: string;
  skipped_nodes?: string[];
}

export interface IncidentEvent {
  id: string;
  level: string;
  message: string;
  timestamp: string;
  node_id?: string | null;
}

export interface IncidentNode {
  id: string;
  key?: string | null;
  title: string;
  status: string;
  role?: string | null;
  updated_at?: string | null;
  events: IncidentEvent[];
  artifacts: ArtifactSummary[];
}

export interface IncidentRunInfo {
  id: string;
  title: string;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  duration_ms?: number | null;
  summary?: RunSummary | null;
}

export interface IncidentReport {
  run: IncidentRunInfo;
  failed_nodes: IncidentNode[];
  recent_events: IncidentEvent[];
  signals: Array<Record<string, unknown>>;
}

export interface PlanVersionDiff {
  plan_id: string;
  current_version: number;
  previous_version: number;
  added_nodes: Array<Record<string, unknown>>;
  removed_nodes: Array<Record<string, unknown>>;
  changed_nodes: Array<{
    id: string;
    changes: Record<string, { previous: unknown; current: unknown }>;
  }>;
  added_edges: Array<{ source: string; target: string }>;
  removed_edges: Array<{ source: string; target: string }>;
}

export interface FeedbackItem {
  id: string;
  run_id: string;
  node_id: string | null;
  source: string;
  reviewer?: string | null;
  score?: number | null;
  comment?: string | null;
  metadata?: Record<string, unknown> | null;
  evaluation?: unknown;
  created_at?: string | null;
  updated_at?: string | null;
}

function buildUrl(path: string, params?: Record<string, string | number | boolean | undefined | null>) {
  const base = resolveApiUrl(path);
  const url = new URL(base);
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    url.searchParams.set(key, String(value));
  });
  return url.toString();
}

async function getJson<T>(path: string, params?: Record<string, string | number | boolean | undefined | null>, options?: FetchOptions) {
  const url = buildUrl(path, params);
  return fetchJson<T>(url, {
    ...options,
    headers: { ...defaultApiHeaders(), ...(options?.headers || {}) },
  });
}

export interface FetchAgentsParams {
  limit?: number;
  offset?: number;
  role?: string;
  domain?: string;
  isActive?: boolean;
  orderBy?: string;
  orderDir?: "asc" | "desc";
}

export function fetchAgents(params: FetchAgentsParams = {}, options?: FetchOptions) {
  return getJson<ApiPage<Agent>>("/agents", {
    limit: params.limit,
    offset: params.offset,
    role: params.role,
    domain: params.domain,
    is_active: params.isActive,
    order_by: params.orderBy,
    order_dir: params.orderDir,
  }, options);
}

export interface FetchRunsParams {
  limit?: number;
  offset?: number;
  status?: string;
  titleContains?: string;
  startedFrom?: string;
  startedTo?: string;
  orderBy?: string;
  orderDir?: "asc" | "desc";
}

export function fetchRuns(params: FetchRunsParams = {}, options?: FetchOptions) {
  return getJson<ApiPage<RunListItem>>("/runs", {
    limit: params.limit,
    offset: params.offset,
    status: params.status,
    title_contains: params.titleContains,
    started_from: params.startedFrom,
    started_to: params.startedTo,
    order_by: params.orderBy,
    order_dir: params.orderDir,
  }, options);
}

export function fetchRun(runId: string, options?: FetchOptions) {
  return getJson<RunDetail>(
    `/runs/${runId}`,
    { include_events: 20, include_nodes: true, include_artifacts: 5 },
    options,
  );
}

// Tasks
export interface TaskListItem {
  id: string;
  title: string;
  status?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface FetchTasksParams {
  limit?: number;
  offset?: number;
  orderBy?: string;
  orderDir?: "asc" | "desc";
}

export function fetchTasks(params: FetchTasksParams = {}, options?: FetchOptions) {
  return getJson<ApiPage<TaskListItem>>("/tasks", {
    limit: params.limit,
    offset: params.offset,
    order_by: params.orderBy,
    order_dir: params.orderDir,
  }, options);
}

export async function cancelRun(runId: string, options?: FetchOptions): Promise<RunActionResponse> {
  return runAction(runId, "cancel", options);
}

export async function runAction(
  runId: string,
  action: "cancel" | "pause" | "resume" | "skip_failed_and_resume",
  options?: FetchOptions,
): Promise<RunActionResponse> {
  const response = await fetch(resolveApiUrl(`/runs/${runId}`), {
    method: "PATCH",
    headers: { ...defaultApiHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
    signal: options?.signal,
  });

  if (!response.ok) {
    let message = response.statusText || `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string") {
        message = payload.detail;
      }
    } catch {}
    throw new Error(message);
  }

  return (await response.json()) as RunActionResponse;
}

export function fetchPlanVersionDiff(
  planId: string,
  numero: number,
  previous?: number,
  options?: FetchOptions,
) {
  return getJson<PlanVersionDiff>(
    `/plans/${planId}/versions/${numero}/diff`,
    { previous },
    options,
  );
}

export interface NodeListItem {
  id: string;
  run_id: string;
  key?: string | null;
  title: string;
  status: string;
  role?: string | null;
  checksum?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export function fetchRunNodes(
  runId: string,
  params: { limit?: number; offset?: number; status?: string } = {},
  options?: FetchOptions
) {
  return getJson<ApiPage<NodeListItem>>(`/runs/${runId}/nodes`, {
    limit: params.limit ?? 100,
    offset: params.offset ?? 0,
    status: params.status,
    order_by: "-created_at",
  }, options);
}

export interface AuditLogItem {
  id: string;
  run_id?: string | null;
  node_id?: string | null;
  source: string;
  action: string;
  actor_role?: string | null;
  actor?: string | null;
  request_id?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

export function fetchAuditLogs(params: { runId?: string; nodeId?: string; limit?: number; offset?: number }, options?: FetchOptions) {
  return getJson<ApiPage<AuditLogItem>>("/audit", {
    run_id: params.runId,
    node_id: params.nodeId,
    limit: params.limit,
    offset: params.offset,
    order_by: "-created_at",
  }, options);
}

export function fetchRunIncident(runId: string, options?: FetchOptions) {
  return getJson<IncidentReport>(`/runs/${runId}/incident`, {}, options);
}

export async function exportRunIncident(runId: string): Promise<Blob> {
  const url = buildUrl(`/runs/${runId}/incident`, { export: true });
  const response = await fetch(url, {
    headers: { ...defaultApiHeaders(), Accept: "application/json" },
  });
  if (!response.ok) {
    let message = response.statusText || `HTTP ${response.status}`;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string") {
        message = payload.detail;
      }
    } catch {}
    throw new Error(message);
  }
  return await response.blob();
}

export function nodeAction(nodeId: string, payload: { action: "pause" | "resume" | "skip" | "override"; prompt?: string; params?: unknown }, options?: FetchOptions) {
  const url = resolveApiUrl(`/nodes/${nodeId}`);
  return fetch(url, {
    method: "PATCH",
    headers: { ...defaultApiHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: options?.signal,
  });
}

export interface FetchFeedbacksParams {
  limit?: number;
  offset?: number;
  runId?: string;
  nodeId?: string;
  source?: string;
  minScore?: number;
  maxScore?: number;
  orderBy?: string;
  orderDir?: "asc" | "desc";
}

export function fetchFeedbacks(params: FetchFeedbacksParams = {}, options?: FetchOptions) {
  return getJson<ApiPage<FeedbackItem>>("/feedbacks", {
    limit: params.limit,
    offset: params.offset,
    run_id: params.runId,
    node_id: params.nodeId,
    source: params.source,
    score_min: params.minScore,
    score_max: params.maxScore,
    order_by: params.orderBy,
    order_dir: params.orderDir,
  }, options);
}

export function normalizeRunStatus(status: string): Status {
  const value = status.toLowerCase();
  switch (value) {
    case "running":
      return "running";
    case "completed":
    case "succeeded":
      return "completed";
    case "failed":
    case "error":
      return "failed";
    case "canceled":
      return "canceled";
    case "paused":
      return "paused";
    case "queued":
    case "pending":
    case "draft":
    case "ready":
      return "queued";
    default:
      return "queued";
  }
}
