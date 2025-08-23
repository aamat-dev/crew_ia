import { fetchJson, FetchOpts } from './http';
import {
  ArtifactItem,
  EventItem,
  NodeItem,
  Page,
  Run,
  RunDetail,
  Status,
} from './types';

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
  const query: Record<string, string | number | boolean | undefined> = {
    page: params.page,
    page_size: params.pageSize,
    status: params.status?.join(','),
    date_from: params.dateFrom,
    date_to: params.dateTo,
    title: params.title,
  };
  const { data } = await fetchJson<Page<Run>>('/runs', { ...opts, query });
  return data;
};

export const getRun = async (
  id: string,
  opts: FetchOpts = {},
): Promise<RunDetail> => {
  const { data } = await fetchJson<RunDetail>(`/runs/${id}`, opts);
  return data;
};

export const getRunSummary = async (
  id: string,
  opts: FetchOpts = {},
): Promise<{ summary: string }> => {
  const { data } = await fetchJson<{ summary: string }>(
    `/runs/${id}/summary`,
    opts,
  );
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
  return data;
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
