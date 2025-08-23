import '@testing-library/jest-dom';
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import type { Mock } from 'vitest';

vi.mock('../../state/ApiKeyContext', () => ({
  useApiKey: () => ({ apiKey: 'k', useEnvKey: false }),
}));

vi.mock('../../api/hooks', () => ({
  useRun: vi.fn(),
  useRunSummary: vi.fn(),
  useRunNodes: vi.fn(),
  useRunEvents: vi.fn(),
  useNodeArtifacts: vi.fn(),
}));

import {
  useRun,
  useRunSummary,
  useRunNodes,
  useRunEvents,
  useNodeArtifacts,
} from '../../api/hooks';
import RunDetailPage from '../../pages/RunDetailPage';

describe('RunDetailPage events and artifacts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('gère la sélection et les filtres', async () => {
    const run = { id: '1', title: 'r1', status: 'queued' as const };
    (useRun as unknown as Mock).mockReturnValue({
      data: run,
      isLoading: false,
      isError: false,
    });
    (useRunSummary as unknown as Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });
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
    (useRunEvents as unknown as Mock).mockImplementation(
      (
        _id: string,
        params: {
          page: number;
          pageSize: number;
          level?: string;
          text?: string;
        },
      ) => ({
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
          meta: { page: params.page, page_size: params.pageSize, total: 40 },
        },
        isLoading: false,
        isError: false,
      }),
    );
    (useNodeArtifacts as unknown as Mock).mockReturnValue({
      data: { items: [], meta: { page: 1, page_size: 50, total: 0 } },
      isLoading: false,
      isError: false,
    });

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/runs/1']}>
          <Routes>
            <Route path="/runs/:id" element={<RunDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole('tab', { name: 'Nodes' }));
    fireEvent.click(await screen.findByTestId('node-row-n1'));
    fireEvent.click(screen.getByRole('tab', { name: 'Artifacts' }));
    await waitFor(() => {
      const calls = (useNodeArtifacts as unknown as Mock).mock.calls;
      const last = calls[calls.length - 1];
      expect(last?.[0]).toBe('n1');
    });

    fireEvent.click(screen.getByRole('tab', { name: 'Events' }));
    fireEvent.click(screen.getByText('Suivant'));
    await waitFor(() => {
      const calls = (useRunEvents as unknown as Mock).mock.calls;
      const last = calls[calls.length - 1];
      expect(last?.[1].page).toBe(2);
    });

    fireEvent.change(screen.getByLabelText('level-filter'), {
      target: { value: 'error' },
    });
    await waitFor(() => {
      const calls = (useRunEvents as unknown as Mock).mock.calls;
      const last = calls[calls.length - 1];
      expect(last?.[1].level).toBe('error');
      expect(last?.[1].page).toBe(1);
    });

    fireEvent.change(screen.getByLabelText('text-filter'), {
      target: { value: 'foo' },
    });
    await act(async () => {
      await new Promise((r) => setTimeout(r, 350));
    });
    await waitFor(() => {
      const calls = (useRunEvents as unknown as Mock).mock.calls;
      const last = calls[calls.length - 1];
      expect(last?.[1].text).toBe('foo');
      expect(last?.[1].page).toBe(1);
    });
  });
});
