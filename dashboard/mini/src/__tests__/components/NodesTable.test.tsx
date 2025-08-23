import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import type { Mock } from 'vitest';
import NodesTable, { NodesTableProps } from '../../components/NodesTable';
import { ApiError } from '../../api/http';

vi.mock('../../api/hooks', () => ({
  useRunNodes: vi.fn(),
}));
import { useRunNodes } from '../../api/hooks';

const setup = (props: Partial<NodesTableProps> = {}) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const defaultProps: NodesTableProps = {
    runId: 'r1',
    page: 1,
    pageSize: 20,
    onPageChange: vi.fn(),
    onPageSizeChange: vi.fn(),
  };
  const view = render(
    <QueryClientProvider client={queryClient}>
      <NodesTable {...defaultProps} {...props} />
    </QueryClientProvider>,
  );
  return { ...view, queryClient };
};

describe('NodesTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('affiche les items', () => {
    (useRunNodes as unknown as Mock).mockReturnValue({
      data: {
        items: [
          {
            id: 'n1',
            role: 'start',
            status: 'succeeded',
            started_at: '2023-01-01T00:00:00Z',
            ended_at: '2023-01-01T00:00:05Z',
            duration_ms: 5000,
            checksum: 'abc',
          },
        ],
        meta: { page: 1, page_size: 20, total: 1 },
      },
      isLoading: false,
      isError: false,
    });
    setup();
    expect(screen.getByText('n1')).toBeInTheDocument();
    expect(screen.getByText('start')).toBeInTheDocument();
    expect(screen.getByText('abc')).toBeInTheDocument();
  });

  it("affiche l'état loading", () => {
    (useRunNodes as unknown as Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });
    setup();
    expect(screen.getAllByText('Chargement...').length).toBeGreaterThan(0);
  });

  it("affiche l'état vide", () => {
    (useRunNodes as unknown as Mock).mockReturnValue({
      data: { items: [], meta: { page: 1, page_size: 20, total: 0 } },
      isLoading: false,
      isError: false,
    });
    setup();
    expect(screen.getByText('Aucune donnée.')).toBeInTheDocument();
  });

  it("affiche l'erreur et relance sur retry", () => {
    (useRunNodes as unknown as Mock).mockReturnValue({
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
