import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import type { Mock } from 'vitest';
import EventsTable, { EventsTableProps } from '../../components/EventsTable';
import { ApiError } from '../../api/http';

vi.mock('../../api/hooks', () => ({
  useRunEvents: vi.fn(),
}));
import { useRunEvents } from '../../api/hooks';

const setup = (props: Partial<EventsTableProps> = {}) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const defaultProps: EventsTableProps = {
    runId: 'r1',
    page: 1,
    pageSize: 20,
    onPageChange: vi.fn(),
    onPageSizeChange: vi.fn(),
    orderBy: 'timestamp',
    orderDir: 'desc',
    onOrderByChange: vi.fn(),
    onOrderDirChange: vi.fn(),
  };
  const view = render(
    <QueryClientProvider client={queryClient}>
      <EventsTable {...defaultProps} {...props} />
    </QueryClientProvider>,
  );
  return { ...view, queryClient };
};

describe('EventsTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('affiche les événements', () => {
    (useRunEvents as unknown as Mock).mockReturnValue({
      data: {
        items: [
          {
            id: 'e1',
            timestamp: '2023-01-01T00:00:00Z',
            level: 'info',
            message: 'hello',
            request_id: 'r-1',
          },
        ],
        meta: { page: 1, page_size: 20, total: 1 },
      },
      isLoading: false,
      isError: false,
    });
    setup();
    expect(screen.getByText('hello')).toBeInTheDocument();
    expect(screen.getAllByText('info')[1]).toBeInTheDocument();
  });

  it("affiche l'état loading", () => {
    (useRunEvents as unknown as Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });
    setup();
    expect(screen.getAllByText('Chargement...').length).toBeGreaterThan(0);
  });

  it("affiche l'état vide", () => {
    (useRunEvents as unknown as Mock).mockReturnValue({
      data: { items: [], meta: { page: 1, page_size: 20, total: 0 } },
      isLoading: false,
      isError: false,
    });
    setup();
    expect(screen.getByText('Aucune donnée.')).toBeInTheDocument();
  });

  it("affiche l'erreur et relance sur retry", () => {
    (useRunEvents as unknown as Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new ApiError('boom', 500, 'req-1'),
    });
    const { queryClient } = setup();
    const spy = vi.spyOn(queryClient, 'invalidateQueries');
    fireEvent.click(screen.getByText('Réessayer'));
    expect(spy).toHaveBeenCalled();
    expect(screen.getByText('Request ID: req-1')).toBeInTheDocument();
  });
});
