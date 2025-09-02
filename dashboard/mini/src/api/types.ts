export type UiStatus =
  | 'queued'
  | 'running'
  | 'succeeded'
  | 'failed'
  | 'canceled'
  | 'partial';

export type ApiStatus = 'pending' | 'running' | 'completed' | 'failed';

export type Status = UiStatus | ApiStatus;

export interface PageMeta {
  page?: number;
  page_size?: number;
  total?: number;
  next?: string;
  prev?: string;
}
export interface Page<T> {
  items: T[];
  meta?: PageMeta;
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
    nodes: Array<{ id: string; label?: string; role?: string; status: Status; feedbacks?: Feedback[] }>;
    edges: Array<{ from: string; to: string }>;
  };
}

export interface Feedback {
  id: string;
  run_id: string;
  node_id: string;
  source: 'auto' | 'human';
  reviewer?: string;
  score: number;
  comment: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
}

export interface NodeItem {
  id: string;
  role?: string;
  status: Status;
  started_at?: string;
  ended_at?: string;
  duration_ms?: number;
  checksum?: string;
  feedbacks?: Feedback[];
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

export type TaskStatus =
  | 'draft'
  | 'ready'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed';

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  created_at?: string;
  plan?: Plan;
}

export type TaskDetail = Task;

// Run type as returned by the backend with API status values
export type BackendRun = Omit<Run, 'status'> & { status: ApiStatus };

export interface BackendRunsList {
  items: BackendRun[];
  total: number;
  limit: number;
  offset: number;
}
export interface Assignment {
  node_id: string;
  role: string;
  agent_id: string;
  llm_backend: string;
  llm_model: string;
  params?: Record<string, any>;
}

export interface Plan {
  id?: string;
  status: 'draft' | 'ready' | 'invalid';
  errors?: string[];
  graph?: {
    nodes: Array<{ id: string; role?: string }>;
    edges: Array<{ from: string; to: string }>;
  };
  assignments?: Assignment[];
}
