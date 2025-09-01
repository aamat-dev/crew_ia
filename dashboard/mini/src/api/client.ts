import { fetchJson, FetchOpts, postJson } from './http';
import {
  ApiStatus,
  ArtifactItem,
  EventItem,
  NodeItem,
  Page,
  Run,
  RunDetail,
  RunSummary,
  Status,
  BackendRun,
  Task,
  TaskDetail,
  Plan,
  Assignment,
} from './types';
import { parseLinkHeader } from './links';

const apiToUiStatus = (status: ApiStatus | Status): Status => {
  switch (status) {
    case 'pending':   return 'queued';
    case 'completed': return 'succeeded';
    default:          return status as Status;
  }
};

export const mapUiStatusesToApi = (status?: Status[]): ApiStatus[] =>
  (status ?? [])
    .map(s => (s === 'queued' ? 'pending'
      : s === 'succeeded' ? 'completed'
      : ['running','failed','pending','completed'].includes(s as string) ? (s as ApiStatus)
      : undefined))
    .filter((s): s is ApiStatus => Boolean(s));

// -------- Runs
export const listRuns = async (
  params: {
    page: number; pageSize: number; status?: Status[];
    dateFrom?: string; dateTo?: string; title?: string;
    orderBy?: 'started_at'|'ended_at'|'title'|'status';
    orderDir?: 'asc'|'desc';
  },
  opts: FetchOpts = {},
): Promise<Page<Run>> => {
  const limit = Math.min(params.pageSize, 200);
  const offset = (params.page - 1) * limit;
  const query: Record<string,string|number|boolean|undefined> = {
    limit, offset,
    status: mapUiStatusesToApi(params.status).join('') || undefined,
    started_from: params.dateFrom,
    started_to: params.dateTo,
    title_contains: params.title,
    order_by: params.orderBy,
    order_dir: params.orderDir,
  };
  const { data, headers } = await fetchJson<{ items: BackendRun[] }>('/runs', { ...opts, query });
  const links = parseLinkHeader(headers.get('Link') ?? '');
  const totalHeader = headers.get('X-Total-Count');
  const total = totalHeader ? Number(totalHeader) : (data as any).total;
  return {
    items: data.items.map(r => ({ ...r, status: apiToUiStatus(r.status) })),
    meta: { page: params.page, page_size: limit, total, next: links.next?.href, prev: links.prev?.href },
  };
};

export const getRun = async (id: string, opts: FetchOpts = {}): Promise<RunDetail> => {
  const { data } = await fetchJson<RunDetail>(`/runs/${id}`, opts);
  const run: RunDetail = { ...data, status: apiToUiStatus(data.status) };
  if (run.dag) {
    run.dag = {
      nodes: run.dag.nodes.map(n => ({ ...n, status: apiToUiStatus(n.status) })),
      edges: run.dag.edges,
    };
  }
  return run;
};

export const getRunSummary = async (id: string, opts: FetchOpts = {}): Promise<RunSummary> => {
  const { data } = await fetchJson<RunSummary>(`/runs/${id}/summary`, opts);
  return data;
};

export const listRunNodes = async (
  id: string,
  params: { page: number; pageSize: number; orderBy?: string; orderDir?: 'asc'|'desc' },
  opts: FetchOpts = {},
): Promise<Page<NodeItem>> => {
  const limit = Math.min(params.pageSize, 200);
  const offset = (params.page - 1) * limit;
  const query: Record<string,string|number|boolean|undefined> = {
    limit, offset, order_by: params.orderBy, order_dir: params.orderDir,
  };
  type BackendNode = Omit<NodeItem,'status'> & { status: ApiStatus };
  const { data, headers } = await fetchJson<{ items: BackendNode[] }>(`/runs/${id}/nodes`, { ...opts, query });
  const links = parseLinkHeader(headers.get('Link') ?? '');
  const totalHeader = headers.get('X-Total-Count');
  const total = totalHeader ? Number(totalHeader)
    : (data as unknown as { meta?: { total?: number } }).meta?.total;
  return {
    items: data.items.map(n => ({ ...n, status: apiToUiStatus(n.status) })),
    meta: { page: params.page, page_size: limit, total, next: links.next?.href, prev: links.prev?.href },
  };
};

export const listRunEvents = async (
  id: string,
  params: { page: number; pageSize: number; level?: 'info'|'warn'|'error'|'debug'; text?: string; orderBy?: string; orderDir?: 'asc'|'desc' },
  opts: FetchOpts = {},
): Promise<Page<EventItem>> => {
  const limit = Math.min(params.pageSize, 200);
  const offset = (params.page - 1) * limit;
  const query: Record<string,string|number|boolean|undefined> = {
    limit, offset, level: params.level, q: params.text, order_by: params.orderBy, order_dir: params.orderDir,
  };
  const { data, headers } = await fetchJson<{ items: EventItem[] }>(`/runs/${id}/events`, { ...opts, query });
  const links = parseLinkHeader(headers.get('Link') ?? '');
  const totalHeader = headers.get('X-Total-Count');
  const total = totalHeader ? Number(totalHeader)
    : (data as unknown as { meta?: { total?: number } }).meta?.total;
  return { items: data.items, meta: { page: params.page, page_size: limit, total, next: links.next?.href, prev: links.prev?.href } };
};

export const listNodeArtifacts = async (
  nodeId: string,
  params: { page: number; pageSize: number; kind?: string },
  opts: FetchOpts = {},
): Promise<Page<ArtifactItem>> => {
  const limit = Math.min(params.pageSize, 200);
  const offset = (params.page - 1) * limit;
  const query: Record<string,string|number|boolean|undefined> = { limit, offset, type: params.kind };
  const { data, headers } = await fetchJson<{ items: ArtifactItem[] }>(`/nodes/${nodeId}/artifacts`, { ...opts, query });
  const links = parseLinkHeader(headers.get('Link') ?? '');
  const totalHeader = headers.get('X-Total-Count');
  const total = totalHeader ? Number(totalHeader)
    : (data as unknown as { meta?: { total?: number } }).meta?.total;
  return { items: data.items, meta: { page: params.page, page_size: limit, total, next: links.next?.href, prev: links.prev?.href } };
};

// PATCH node actions (pause/resume/skip/override)
export const patchNode = async (nodeId: string, body: Record<string, unknown>, opts: FetchOpts = {}) => {
  const { requestId } = await fetchJson<unknown>(`/nodes/${nodeId}`, { ...opts, method: 'PATCH', body });
  return { requestId };
};

// -------- Plans / Assignments
export const getPlan = async (id: string, opts: FetchOpts = {}): Promise<Plan> => {
  const { data } = await fetchJson<Plan>(`/plans/${id}`, opts);
  return data;
};

export const saveAssignments = async (planId: string, assignments: Assignment[], opts: FetchOpts = {}): Promise<void> => {
  await postJson<unknown, { assignments: Assignment[] }>(`/plans/${planId}/assignments`, { assignments }, opts);
};

export const setPlanStatus = async (planId: string, status: 'draft'|'ready'|'invalid', opts: FetchOpts = {}): Promise<void> => {
  await postJson<unknown, { status: 'draft'|'ready'|'invalid' }>(`/plans/${planId}/status`, { status }, opts);
};

// -------- Tasks
export const listTasks = async (
  params: { page: number; pageSize: number; orderBy?: 'created_at'|'title'|'status'; orderDir?: 'asc'|'desc' },
  opts: FetchOpts = {},
): Promise<Page<Task>> => {
  const limit = Math.min(params.pageSize, 200);
  const offset = (params.page - 1) * limit;
  const query: Record<string,string|number|boolean|undefined> = {
    limit, offset, order_by: params.orderBy, order_dir: params.orderDir,
  };
  const { data, headers } = await fetchJson<{ items: Task[] }>('/tasks', { ...opts, query });
  const links = parseLinkHeader(headers.get('Link') ?? '');
  const totalHeader = headers.get('X-Total-Count');
  const total = totalHeader ? Number(totalHeader)
    : (data as unknown as { meta?: { total?: number } }).meta?.total;
  return { items: data.items, meta: { page: params.page, page_size: limit, total, next: links.next?.href, prev: links.prev?.href } };
};

export const createTask = async (payload: { title: string; description?: string }, opts: FetchOpts = {}): Promise<Task> => {
  const { data } = await fetchJson<Task>('/tasks', { ...opts, method: 'POST', body: payload });
  return data;
};

export const getTask = async (id: string, opts: FetchOpts = {}): Promise<TaskDetail> => {
  const { data } = await fetchJson<TaskDetail>(`/tasks/${id}`, opts);
  return data;
};

export const generateTaskPlan = async (id: string, opts: FetchOpts = {}): Promise<Plan> => {
  const { data } = await fetchJson<Plan>(`/tasks/${id}/plan`, { ...opts, method: 'POST' });
  return data;
};
