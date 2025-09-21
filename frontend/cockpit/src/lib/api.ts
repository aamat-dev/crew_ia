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
}

export interface RunDetail {
  id: string;
  title: string;
  status: string;
  started_at?: string | null;
  ended_at?: string | null;
  meta?: Record<string, unknown> | null;
  summary?: RunSummary | null;
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
  return getJson<RunDetail>(`/runs/${runId}`, undefined, options);
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

