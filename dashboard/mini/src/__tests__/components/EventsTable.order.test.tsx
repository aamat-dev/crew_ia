import '@testing-library/jest-dom';
import 'whatwg-fetch';
import { render, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect } from 'vitest';
import EventsTable, { EventsTableProps } from '../../components/EventsTable';

const setup = (props: Partial<EventsTableProps> = {}) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const defaultProps: EventsTableProps = {
    runId: 'r1',
    page: 1,
    pageSize: 20,
    orderBy: 'timestamp',
    orderDir: 'desc',
    onPageChange: vi.fn(),
    onPageSizeChange: vi.fn(),
    onOrderByChange: vi.fn(),
    onOrderDirChange: vi.fn(),
  };
  return render(
    <QueryClientProvider client={queryClient}>
      <EventsTable {...defaultProps} {...props} />
    </QueryClientProvider>,
  );
};

describe('EventsTable order params', () => {
  it('envoie order_by et order_dir', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ items: [], meta: { page: 1, page_size: 20, total: 0 } }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );
    global.fetch = fetchMock as unknown as typeof fetch;
    setup({ orderBy: 'level', orderDir: 'asc' });
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const url = new URL(fetchMock.mock.calls[0][0] as string);
    expect(url.searchParams.get('order_by')).toBe('level');
    expect(url.searchParams.get('order_dir')).toBe('asc');
  });
});
