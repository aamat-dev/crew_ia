import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getRun,
  getRunSummary,
  listNodeArtifacts,
  listRunEvents,
  listRunNodes,
  listRuns,
  listTasks,
  getTask,
  createTask,
  generateTaskPlan,
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
  Task,
  TaskDetail,
} from './types';

export const useRuns = (
  params: {
    page: number;
    pageSize: number;
    status?: Status[];
    dateFrom?: string;
    dateTo?: string;
    title?: string;
    orderBy?: 'started_at' | 'ended_at' | 'title' | 'status';
    orderDir?: 'asc' | 'desc';
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
  params: {
    page: number;
    pageSize: number;
    orderBy?: string;
    orderDir?: 'asc' | 'desc';
  },
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
    orderBy?: string;
    orderDir?: 'asc' | 'desc';
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

export const useTasks = (
  params: {
    page: number;
    pageSize: number;
    orderBy?: 'created_at' | 'title' | 'status';
    orderDir?: 'asc' | 'desc';
  },
  opts?: { enabled?: boolean },
) =>
  useQuery<Page<Task>>({
    queryKey: ['tasks', params],
    queryFn: ({ signal }) => listTasks(params, { signal }),
    staleTime: 5_000,
    enabled: opts?.enabled,
  });

export const useTask = (id: string, opts?: { enabled?: boolean }) =>
  useQuery<TaskDetail>({
    queryKey: ['task', id],
    queryFn: ({ signal }) => getTask(id, { signal }),
    enabled: opts?.enabled,
  });

export const useCreateTask = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { title: string; description?: string }) =>
      createTask(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useGenerateTaskPlan = (id: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => generateTaskPlan(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task', id] });
    },
  });
};
