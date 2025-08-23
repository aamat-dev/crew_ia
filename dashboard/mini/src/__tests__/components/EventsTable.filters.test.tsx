import '@testing-library/jest-dom';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import type { Mock } from 'vitest';
import EventsTable, { EventsTableProps } from '../../components/EventsTable';

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
  };
  const view = render(
    <QueryClientProvider client={queryClient}>
      <EventsTable {...defaultProps} {...props} />
    </QueryClientProvider>,
  );
  return { ...view, queryClient };
};

describe('EventsTable filters', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  it('déclenche les callbacks de filtre', () => {
    (useRunEvents as unknown as Mock).mockReturnValue({
      data: {
        items: [
          {
            id: 'e1',
            timestamp: '2023-01-01T00:00:00Z',
            level: 'info',
            message: 'hello',
            request_id: 'r1',
          },
        ],
        meta: { page: 1, page_size: 20, total: 1 },
      },
      isLoading: false,
      isError: false,
    });
    const onLevelChange = vi.fn();
    const onTextChange = vi.fn();
    const onPageChange = vi.fn();
    setup({ onLevelChange, onTextChange, onPageChange });

    fireEvent.change(screen.getByTestId('events-level-filter'), {
      target: { value: 'error' },
    });
    expect(onLevelChange).toHaveBeenCalledWith('error');

    fireEvent.change(screen.getByTestId('events-text-filter'), {
      target: { value: 'abc' },
    });
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(onTextChange).toHaveBeenCalledWith('abc');

    expect(onPageChange).not.toHaveBeenCalled();
  });
});
