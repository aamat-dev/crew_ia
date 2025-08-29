import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import type { Mock } from 'vitest';
import NodesTable, { NodesTableProps } from '../../components/NodesTable';

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
    orderBy: 'created_at',
    orderDir: 'desc',
    onOrderByChange: vi.fn(),
    onOrderDirChange: vi.fn(),
  };
  const view = render(
    <QueryClientProvider client={queryClient}>
      <NodesTable {...defaultProps} {...props} />
    </QueryClientProvider>,
  );
  return { ...view, queryClient };
};

describe('NodesTable selection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('appelle onSelectNode lors du clic', () => {
    (useRunNodes as unknown as Mock).mockReturnValue({
      data: {
        items: [
          { id: 'n1', status: 'succeeded', role: 'r1' },
          { id: 'n2', status: 'succeeded', role: 'r2' },
        ],
        meta: { page: 1, page_size: 20, total: 2 },
      },
      isLoading: false,
      isError: false,
    });
    const onSelect = vi.fn();
    setup({ onSelectNode: onSelect });
    fireEvent.click(screen.getByTestId('node-row-n1'));
    expect(onSelect).toHaveBeenCalledWith('n1');
  });

  it('applique le style sélectionné', () => {
    (useRunNodes as unknown as Mock).mockReturnValue({
      data: {
        items: [
          { id: 'n1', status: 'succeeded', role: 'r1' },
          { id: 'n2', status: 'succeeded', role: 'r2' },
        ],
        meta: { page: 1, page_size: 20, total: 2 },
      },
      isLoading: false,
      isError: false,
    });
    setup({ selectedNodeId: 'n1' });
    const row = screen.getByTestId('node-row-n1');
    expect(row).toHaveStyle({ background: '#eef' });
    expect(row).toHaveAttribute('aria-selected', 'true');
  });
});
