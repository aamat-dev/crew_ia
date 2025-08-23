import { fetchJson, FetchOpts } from './http';
import {
  ApiStatus,
  ArtifactItem,
  BackendRunsList,
  EventItem,
  NodeItem,
  Page,
  Run,
  RunDetail,
  RunSummary,
  Status,
} from './types';

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
  const query: Record<string, string | number | boolean | undefined> = {
    page: params.page,
    page_size: params.pageSize,
    status: status || undefined,
    date_from: params.dateFrom,
    date_to: params.dateTo,
    title: params.title,
  };
  const { data } = await fetchJson<BackendRunsList>('/runs', {
    ...opts,
    query,
  });
  return {
    items: data.items.map((r) => ({ ...r, status: apiToUiStatus(r.status) })),
    meta: {
      page: Math.floor(data.offset / data.limit) + 1,
      page_size: data.limit,
      total: data.total,
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
  params: { page: number; pageSize: number },
  opts: FetchOpts = {},
): Promise<Page<NodeItem>> => {
  const query = { page: params.page, page_size: params.pageSize };
  const { data } = await fetchJson<Page<NodeItem>>(`/runs/${id}/nodes`, {
    ...opts,
    query,
  });
  return {
    items: data.items.map((n) => ({ ...n, status: apiToUiStatus(n.status) })),
    meta: data.meta,
  };
};

export const listRunEvents = async (
  id: string,
  params: {
    page: number;
    pageSize: number;
    level?: 'info' | 'warn' | 'error' | 'debug';
    text?: string;
  },
  opts: FetchOpts = {},
): Promise<Page<EventItem>> => {
  const query: Record<string, string | number | boolean | undefined> = {
    page: params.page,
    page_size: params.pageSize,
    level: params.level,
    text: params.text,
  };
  const { data } = await fetchJson<Page<EventItem>>(`/runs/${id}/events`, {
    ...opts,
    query,
  });
  return data;
};

export const listNodeArtifacts = async (
  nodeId: string,
  params: { page: number; pageSize: number; kind?: string },
  opts: FetchOpts = {},
): Promise<Page<ArtifactItem>> => {
  const query: Record<string, string | number | boolean | undefined> = {
    page: params.page,
    page_size: params.pageSize,
    kind: params.kind,
  };
  const { data } = await fetchJson<Page<ArtifactItem>>(
    `/nodes/${nodeId}/artifacts`,
    {
      ...opts,
      query,
    },
  );
  return data;
};
