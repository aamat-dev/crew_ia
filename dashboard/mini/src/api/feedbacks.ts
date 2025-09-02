import { fetchJson, postJson, FetchOpts } from './http';
import { Feedback, Page } from './types';

export const listFeedbacks = async (
  params: { run_id?: string; node_id?: string },
  opts: FetchOpts = {},
): Promise<Page<Feedback>> => {
  const query: Record<string, string | undefined> = {
    run_id: params.run_id,
    node_id: params.node_id,
  };
  const { data, headers } = await fetchJson<{ items: Feedback[] }>('/feedbacks', {
    ...opts,
    query,
  });
  const totalHeader = headers.get('X-Total-Count');
  const total = totalHeader ? Number(totalHeader) : undefined;
  return {
    items: data.items,
    meta: { total },
  };
};

export const createFeedback = async (
  payload: Omit<Feedback, 'id' | 'created_at' | 'updated_at'>,
  opts: FetchOpts = {},
): Promise<Feedback> => {
  const { data } = await postJson<Feedback, typeof payload>(
    '/feedbacks',
    payload,
    { ...opts, role: 'editor' },
  );
  return data;
};
