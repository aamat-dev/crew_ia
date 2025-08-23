export type Status =
  | 'queued'
  | 'running'
  | 'succeeded'
  | 'failed'
  | 'canceled'
  | 'partial';

export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
}
export interface Page<T> {
  items: T[];
  meta: PageMeta;
}

export interface Run {
  id: string;
  title?: string;
  status: Status;
  started_at?: string;
  ended_at?: string;
  counters?: { tokens_total?: number; nodes_total?: number; errors?: number };
}

export interface RunSummary {
  nodes_total: number;
  nodes_completed: number;
  nodes_failed: number;
  artifacts_total: number;
  events_total: number;
  duration_ms?: number;
}

export interface RunDetail extends Run {
  summary?: RunSummary;
  dag?: {
    nodes: Array<{ id: string; label?: string; role?: string; status: Status }>;
    edges: Array<{ from: string; to: string }>;
  };
}

export interface NodeItem {
  id: string;
  role?: string;
  status: Status;
  started_at?: string;
  ended_at?: string;
  duration_ms?: number;
  checksum?: string;
}

export interface EventItem {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  request_id?: string;
}

export interface ArtifactItem {
  id: string;
  node_id: string;
  name: string;
  kind: 'file' | 'llm_sidecar' | 'log' | 'other';
  size_bytes?: number;
  url: string;
}
