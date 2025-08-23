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
  Status,
} from './types';

export const useRuns = (params: {
  page: number;
  pageSize: number;
  status?: Status[];
  dateFrom?: string;
  dateTo?: string;
  title?: string;
}) =>
  useQuery<Page<Run>>({
    queryKey: ['runs', params],
    queryFn: ({ signal }) => listRuns(params, { signal }),
    staleTime: 5_000,
  });

export const useRun = (id: string) =>
  useQuery<RunDetail>({
    queryKey: ['run', id],
    queryFn: ({ signal }) => getRun(id, { signal }),
  });

export const useRunSummary = (id: string) =>
  useQuery<{ summary: string }>({
    queryKey: ['run', id, 'summary'],
    queryFn: ({ signal }) => getRunSummary(id, { signal }),
  });

export const useRunNodes = (
  id: string,
  params: { page: number; pageSize: number },
) =>
  useQuery<Page<NodeItem>>({
    queryKey: ['run', id, 'nodes', params],
    queryFn: ({ signal }) => listRunNodes(id, params, { signal }),
  });

export const useRunEvents = (
  id: string,
  params: {
    page: number;
    pageSize: number;
    level?: 'info' | 'warn' | 'error' | 'debug';
    text?: string;
  },
) =>
  useQuery<Page<EventItem>>({
    queryKey: ['run', id, 'events', params],
    queryFn: ({ signal }) => listRunEvents(id, params, { signal }),
  });

export const useNodeArtifacts = (
  nodeId: string,
  params: { page: number; pageSize: number; kind?: string },
) =>
  useQuery<Page<ArtifactItem>>({
    queryKey: ['node', nodeId, 'artifacts', params],
    queryFn: ({ signal }) => listNodeArtifacts(nodeId, params, { signal }),
  });
