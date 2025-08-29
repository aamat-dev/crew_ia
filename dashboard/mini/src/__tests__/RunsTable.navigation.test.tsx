import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, beforeEach, expect } from 'vitest';
import type { Mock } from 'vitest';
import RunsTable, { RunsTableProps } from '../components/RunsTable';

vi.mock('../api/hooks', () => ({
  useRuns: vi.fn(),
}));
import { useRuns } from '../api/hooks';

const setup = (props: Partial<RunsTableProps> = {}) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const defaultProps: RunsTableProps = {
    page: 1,
    pageSize: 20,
    orderBy: 'started_at',
    orderDir: 'desc',
    onPageChange: vi.fn(),
    onPageSizeChange: vi.fn(),
    onOrderByChange: vi.fn(),
    onOrderDirChange: vi.fn(),
    onOpenRun: vi.fn(),
  };
  render(
    <QueryClientProvider client={queryClient}>
      <RunsTable {...defaultProps} {...props} />
    </QueryClientProvider>,
  );
};

describe('RunsTable navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('début: prev disabled, next enabled', () => {
    (useRuns as unknown as Mock).mockReturnValue({
      data: {
        items: [{ id: 'r1', status: 'running' }],
        meta: { page: 1, page_size: 20, total: 40, next: '/runs?page=2' },
      },
      isLoading: false,
      isError: false,
    });
    setup();
    expect(screen.getByText('Précédent')).toBeDisabled();
    expect(screen.getByText('Suivant')).not.toBeDisabled();
  });

  it('milieu: prev and next enabled', () => {
    (useRuns as unknown as Mock).mockReturnValue({
      data: {
        items: [{ id: 'r1', status: 'running' }],
        meta: {
          page: 2,
          page_size: 20,
          total: 40,
          next: '/runs?page=3',
          prev: '/runs?page=1',
        },
      },
      isLoading: false,
      isError: false,
    });
    setup({ page: 2 });
    expect(screen.getByText('Précédent')).not.toBeDisabled();
    expect(screen.getByText('Suivant')).not.toBeDisabled();
  });

  it('fin: next disabled, prev enabled', () => {
    (useRuns as unknown as Mock).mockReturnValue({
      data: {
        items: [{ id: 'r1', status: 'running' }],
        meta: { page: 3, page_size: 20, total: 40, prev: '/runs?page=2' },
      },
      isLoading: false,
      isError: false,
    });
    setup({ page: 3 });
    expect(screen.getByText('Précédent')).not.toBeDisabled();
    expect(screen.getByText('Suivant')).toBeDisabled();
  });

  it('change de tri met à jour prev/next', () => {
    (useRuns as unknown as Mock).mockImplementation((params) => {
      if (params.orderBy === 'started_at') {
        return {
          data: {
            items: [{ id: 'r1', status: 'running' }],
            meta: { page: 1, page_size: 20, total: 20, next: '/runs?page=2' },
          },
          isLoading: false,
          isError: false,
        };
      }
      return {
        data: {
          items: [{ id: 'r1', status: 'running' }],
          meta: { page: 1, page_size: 20, total: 20 },
        },
        isLoading: false,
        isError: false,
      };
    });
    const Wrapper = () => {
      const [orderBy, setOrderBy] = React.useState('started_at');
      return (
        <RunsTable
          page={1}
          pageSize={20}
          orderBy={orderBy}
          orderDir="desc"
          onOrderByChange={setOrderBy}
          onOrderDirChange={() => {}}
          onPageChange={() => {}}
          onPageSizeChange={() => {}}
          onOpenRun={() => {}}
        />
      );
    };
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <Wrapper />
      </QueryClientProvider>,
    );
    expect(screen.getByText('Suivant')).not.toBeDisabled();
    const select = screen.getByLabelText('order-by');
    fireEvent.change(select, { target: { value: 'ended_at' } });
    expect(screen.getByText('Suivant')).toBeDisabled();
    expect(screen.getByText('Précédent')).toBeDisabled();
  });
});
