import { z } from 'zod';

export const AgentSchema = z.object({
  id: z.string(),
  name: z.string(),
});

export type Agent = z.infer<typeof AgentSchema>;

export const RunSchema = z.object({
  id: z.string(),
  title: z.string().optional(),
  status: z.enum([
    'queued',
    'running',
    'succeeded',
    'failed',
    'canceled',
    'partial',
    'paused',
  ]),
  started_at: z.string().optional(),
  ended_at: z.string().optional(),
  counters: z
    .object({
      tokens_total: z.number().optional(),
      nodes_total: z.number().optional(),
      errors: z.number().optional(),
    })
    .optional(),
});

export type Run = z.infer<typeof RunSchema>;

export const FeedbackSchema = z.object({
  id: z.string(),
  run_id: z.string(),
  node_id: z.string(),
  source: z.enum(['auto', 'human']),
  reviewer: z.string().optional(),
  score: z.number(),
  comment: z.string(),
  metadata: z.record(z.any()).optional(),
  created_at: z.string(),
  updated_at: z.string().optional(),
});

export type Feedback = z.infer<typeof FeedbackSchema>;
