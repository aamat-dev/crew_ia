import { useQuery } from '@tanstack/react-query';
import {
  getRun,
  getRunSummary,
  listNodeArtifacts,
  listRunEvents,
  listRunNodes,
  listRuns,
} from './client';
import {
  ArtifactItem,
  EventItem,
  NodeItem,
  Page,
  Run,
  RunDetail,
  RunSummary,
  Status,
} from './types';

export const useRuns = (
  params: {
    page: number;
    pageSize: number;
    status?: Status[];
    dateFrom?: string;
    dateTo?: string;
    title?: string;
  },
  opts?: { enabled?: boolean },
) =>
  useQuery<Page<Run>>({
    queryKey: ['runs', params],
    queryFn: ({ signal }) => listRuns(params, { signal }),
    staleTime: 5_000,
    enabled: opts?.enabled,
  });

export const useRun = (id: string, opts?: { enabled?: boolean }) =>
  useQuery<RunDetail>({
    queryKey: ['run', id],
    queryFn: ({ signal }) => getRun(id, { signal }),
    enabled: opts?.enabled,
  });

export const useRunSummary = (id: string, opts?: { enabled?: boolean }) =>
  useQuery<RunSummary>({
    queryKey: ['run', id, 'summary'],
    queryFn: ({ signal }) => getRunSummary(id, { signal }),
    enabled: opts?.enabled,
  });

export const useRunNodes = (
  id: string,
  params: { page: number; pageSize: number },
  opts?: { enabled?: boolean },
) =>
  useQuery<Page<NodeItem>>({
    queryKey: ['run', id, 'nodes', params],
    queryFn: ({ signal }) => listRunNodes(id, params, { signal }),
    enabled: opts?.enabled,
  });

export const useRunEvents = (
  id: string,
  params: {
    page: number;
    pageSize: number;
    level?: 'info' | 'warn' | 'error' | 'debug';
    text?: string;
  },
  opts?: { enabled?: boolean },
) =>
  useQuery<Page<EventItem>>({
    queryKey: ['run', id, 'events', params],
    queryFn: ({ signal }) => listRunEvents(id, params, { signal }),
    enabled: opts?.enabled,
  });

export const useNodeArtifacts = (
  nodeId: string,
  params: { page: number; pageSize: number; kind?: string },
  opts?: { enabled?: boolean },
) =>
  useQuery<Page<ArtifactItem>>({
    queryKey: ['node', nodeId, 'artifacts', params],
    queryFn: ({ signal }) => listNodeArtifacts(nodeId, params, { signal }),
    enabled: opts?.enabled,
  });
