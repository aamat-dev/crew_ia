import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchAgents,
  fetchRuns,
  fetchFeedbacks,
  runAction,
  RunAction,
} from './api';
import { Agent, Run, Feedback } from './models';

export const useAgents = () =>
  useQuery<Agent[]>({ queryKey: ['agents'], queryFn: fetchAgents });

export const useRuns = () =>
  useQuery<Run[]>({ queryKey: ['runs'], queryFn: fetchRuns });

export const useFeedbacks = () =>
  useQuery<Feedback[]>({ queryKey: ['feedbacks'], queryFn: fetchFeedbacks });

export const useRunAction = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, action }: { id: string; action: RunAction }) =>
      runAction(id, action),
    onMutate: async ({ id, action }) => {
      await queryClient.cancelQueries({ queryKey: ['runs'] });
      const prev = queryClient.getQueryData<Run[]>(['runs']);
      if (prev) {
        const nextStatus =
          action === 'pause'
            ? 'paused'
            : action === 'resume' || action === 'retry'
              ? 'running'
              : action === 'cancel'
                ? 'canceled'
                : undefined;
        if (nextStatus) {
          queryClient.setQueryData<Run[]>(
            ['runs'],
            prev.map((r) => (r.id === id ? { ...r, status: nextStatus } : r)),
          );
        }
      }
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(['runs'], ctx.prev);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] });
    },
  });
};
