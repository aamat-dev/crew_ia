import '@testing-library/jest-dom';
import 'whatwg-fetch';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect } from 'vitest';
import RunsTable, { RunsTableProps } from '../components/RunsTable';
import * as client from '../api/client';
import { ApiError } from '../api/http';
import { Status } from '../api/types';

const setup = (props: Partial<RunsTableProps> = {}) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const defaultProps: RunsTableProps = {
    page: 1,
    pageSize: 20,
    onPageChange: vi.fn(),
    onPageSizeChange: vi.fn(),
    onOpenRun: vi.fn(),
  };
  const view = render(
    <QueryClientProvider client={queryClient}>
      <RunsTable {...defaultProps} {...props} />
    </QueryClientProvider>,
  );
  return { ...view, queryClient };
};

describe('RunsTable', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });
  it('rendu loading', () => {
    vi.spyOn(client, 'listRuns').mockImplementation(
      () => new Promise(() => {}),
    );
    setup();
    expect(screen.getAllByText('Chargement...')).toHaveLength(3);
  });

  it('rendu empty', async () => {
    vi.spyOn(client, 'listRuns').mockResolvedValueOnce({
      items: [],
      meta: { page: 1, page_size: 20, total: 0 },
    });
    setup();
    await waitFor(() =>
      expect(screen.getByText('Aucune donnée.')).toBeInTheDocument(),
    );
  });

  it('rendu error + retry', async () => {
    const spy = vi.spyOn(client, 'listRuns');
    spy.mockRejectedValueOnce(new ApiError('boom', 500, 'req-1'));
    setup();
    await waitFor(() => expect(spy).toHaveBeenCalled());
    await waitFor(() =>
      expect(screen.getByText('Une erreur est survenue.')).toBeInTheDocument(),
    );
    expect(screen.getByText('Request ID: req-1')).toBeInTheDocument();
    spy.mockResolvedValueOnce({
      items: [],
      meta: { page: 1, page_size: 20, total: 0 },
    });
    fireEvent.click(screen.getByText('Réessayer'));
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(2));
  });

  it('refetch quand les props changent', async () => {
    const spy = vi.spyOn(client, 'listRuns').mockResolvedValue({
      items: [],
      meta: { page: 1, page_size: 20, total: 0 },
    });
    const { rerender, queryClient } = setup();
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(1));
    rerender(
      <QueryClientProvider client={queryClient}>
        <RunsTable
          page={1}
          pageSize={20}
          status={['running' as Status]}
          onPageChange={vi.fn()}
          onPageSizeChange={vi.fn()}
          onOpenRun={vi.fn()}
        />
      </QueryClientProvider>,
    );
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(2));
  });

  it('mappe le filtre queued vers pending', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ items: [], total: 0, limit: 20, offset: 0 }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    );
    global.fetch = fetchMock as unknown as typeof fetch;
    setup({ status: ['queued'] });
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const url = new URL(fetchMock.mock.calls[0][0] as string);
    expect(url.searchParams.get('status')).toBe('pending');
  });
});
