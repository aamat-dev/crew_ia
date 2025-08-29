import { fetchJson, FetchOpts } from './http';
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
} from './types';
import { parseLinkHeader } from './links';

const apiToUiStatus = (status: ApiStatus | Status): Status => {
  switch (status) {
    case 'pending':
      return 'queued';
    case 'completed':
      return 'succeeded';
    default:
      return status as Status;
  }
};

export const mapUiStatusesToApi = (status?: Status[]): ApiStatus[] => {
  if (!status) return [];
  return status
    .map((s) => {
      switch (s) {
        case 'queued':
          return 'pending';
        case 'succeeded':
          return 'completed';
        case 'running':
        case 'failed':
        case 'pending':
        case 'completed':
          return s;
        default:
          return undefined;
      }
    })
    .filter((s): s is ApiStatus => Boolean(s));
};

export const listRuns = async (
  params: {
    page: number;
    pageSize: number;
    status?: Status[];
    dateFrom?: string;
    dateTo?: string;
    title?: string;
  },
  opts: FetchOpts = {},
): Promise<Page<Run>> => {
  const status = mapUiStatusesToApi(params.status).join(',');
  const limit = Math.min(params.pageSize, 50);
  const offset = (params.page - 1) * limit;
  const query: Record<string, string | number | boolean | undefined> = {
    limit,
    offset,
    status: status || undefined,
    started_from: params.dateFrom,
    started_to: params.dateTo,
    title_contains: params.title,
    order_by: params.orderBy,
    order_dir: params.orderDir,
  };
  const { data, headers } = await fetchJson<{ items: BackendRun[] }>('/runs', {
    ...opts,
    query,
  });
  const links = parseLinkHeader(headers.get('Link') ?? '');
  const totalHeader = headers.get('X-Total-Count');
  const total = totalHeader
    ? Number(totalHeader)
    : (data as unknown as { total?: number }).total;
  return {
    items: data.items.map((r) => ({ ...r, status: apiToUiStatus(r.status) })),
    meta: {
      page: params.page,
      page_size: limit,
      total,
      next: links.next?.href,
      prev: links.prev?.href,
    },
  };
};

export const getRun = async (
  id: string,
  opts: FetchOpts = {},
): Promise<RunDetail> => {
  const { data } = await fetchJson<RunDetail>(`/runs/${id}`, opts);
  const run: RunDetail = { ...data, status: apiToUiStatus(data.status) };
  if (run.dag) {
    run.dag = {
      nodes: run.dag.nodes.map((n) => ({
        ...n,
        status: apiToUiStatus(n.status),
      })),
      edges: run.dag.edges,
    };
  }
  return run;
};

export const getRunSummary = async (
  id: string,
  opts: FetchOpts = {},
): Promise<RunSummary> => {
  const { data } = await fetchJson<RunSummary>(`/runs/${id}/summary`, opts);
  return data;
};

export const listRunNodes = async (
  id: string,
  params: {
    page: number;
    pageSize: number;
    orderBy?: string;
    orderDir?: 'asc' | 'desc';
  },
  opts: FetchOpts = {},
): Promise<Page<NodeItem>> => {
  const limit = Math.min(params.pageSize, 50);
  const offset = (params.page - 1) * limit;
  const query: Record<string, string | number | boolean | undefined> = {
    limit,
    offset,
    order_by: params.orderBy,
    order_dir: params.orderDir,
  };
  type BackendNode = Omit<NodeItem, 'status'> & { status: ApiStatus };
  const { data, headers } = await fetchJson<{ items: BackendNode[] }>(
    `/runs/${id}/nodes`,
    { ...opts, query },
  );
  const links = parseLinkHeader(headers.get('Link') ?? '');
  const totalHeader = headers.get('X-Total-Count');
  const total = totalHeader
    ? Number(totalHeader)
    : (data as unknown as { meta?: { total?: number } }).meta?.total;
  return {
    items: data.items.map((n) => ({ ...n, status: apiToUiStatus(n.status) })),
    meta: {
      page: params.page,
      page_size: limit,
      total,
      next: links.next?.href,
      prev: links.prev?.href,
    },
  };
};

export const listRunEvents = async (
  id: string,
  params: {
    page: number;
    pageSize: number;
    level?: 'info' | 'warn' | 'error' | 'debug';
    text?: string;
    orderBy?: string;
    orderDir?: 'asc' | 'desc';
  },
  opts: FetchOpts = {},
): Promise<Page<EventItem>> => {
  const limit = Math.min(params.pageSize, 50);
  const offset = (params.page - 1) * limit;
  const query: Record<string, string | number | boolean | undefined> = {
    limit,
    offset,
    level: params.level,
    q: params.text,
    order_by: params.orderBy,
    order_dir: params.orderDir,
  };
  const { data, headers } = await fetchJson<{ items: EventItem[] }>(
    `/runs/${id}/events`,
    { ...opts, query },
  );
  const links = parseLinkHeader(headers.get('Link') ?? '');
  const totalHeader = headers.get('X-Total-Count');
  const total = totalHeader
    ? Number(totalHeader)
    : (data as unknown as { meta?: { total?: number } }).meta?.total;
  return {
    items: data.items,
    meta: {
      page: params.page,
      page_size: limit,
      total,
      next: links.next?.href,
      prev: links.prev?.href,
    },
  };
};

export const listNodeArtifacts = async (
  nodeId: string,
  params: { page: number; pageSize: number; kind?: string },
  opts: FetchOpts = {},
): Promise<Page<ArtifactItem>> => {
  const limit = Math.min(params.pageSize, 50);
  const offset = (params.page - 1) * limit;
  const query: Record<string, string | number | boolean | undefined> = {
    limit,
    offset,
    type: params.kind,
  };
  const { data, headers } = await fetchJson<{ items: ArtifactItem[] }>(
    `/nodes/${nodeId}/artifacts`,
    {
      ...opts,
      query,
    },
  );
  const links = parseLinkHeader(headers.get('Link') ?? '');
  const totalHeader = headers.get('X-Total-Count');
  const total = totalHeader
    ? Number(totalHeader)
    : (data as unknown as { meta?: { total?: number } }).meta?.total;
  return {
    items: data.items,
    meta: {
      page: params.page,
      page_size: limit,
      total,
      next: links.next?.href,
      prev: links.prev?.href,
    },
  };
};
