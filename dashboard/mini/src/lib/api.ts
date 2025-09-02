import { getJSON, postJSON } from './http';
import {
  AgentSchema,
  Agent,
  RunSchema,
  Run,
  FeedbackSchema,
  Feedback,
} from './models';

export type RunAction = 'pause' | 'resume' | 'cancel' | 'retry';

export async function fetchAgents(): Promise<Agent[]> {
  const res = await getJSON<unknown>('/api/agents');
  if (res.error || !res.data) throw res.error ?? new Error('No data');
  return AgentSchema.array().parse(res.data);
}

export async function fetchRuns(): Promise<Run[]> {
  const res = await getJSON<unknown>('/api/runs');
  if (res.error || !res.data) throw res.error ?? new Error('No data');
  return RunSchema.array().parse(res.data);
}

export async function fetchFeedbacks(): Promise<Feedback[]> {
  const res = await getJSON<unknown>('/api/feedbacks');
  if (res.error || !res.data) throw res.error ?? new Error('No data');
  return FeedbackSchema.array().parse(res.data);
}

export async function runAction(id: string, action: RunAction): Promise<Run> {
  const res = await postJSON<unknown>(`/api/runs/${id}/actions`, { action });
  if (res.error || !res.data) throw res.error ?? new Error('No data');
  return RunSchema.parse(res.data);
}
