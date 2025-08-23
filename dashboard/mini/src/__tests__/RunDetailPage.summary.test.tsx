import '@testing-library/jest-dom';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect } from 'vitest';

vi.mock('../state/ApiKeyContext', () => ({
  useApiKey: () => ({ apiKey: 'k', useEnvKey: false }),
}));

const run = { id: '1', title: 'r1', status: 'queued' as const };

type UseRunReturn = {
  data: typeof run;
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
};

type UseRunSummaryReturn = {
  data: undefined;
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
};

vi.mock('../api/hooks', () => ({
  useRun: (): UseRunReturn => ({ data: run, isLoading: false, isError: false }),
  useRunSummary: (): UseRunSummaryReturn => ({
    data: undefined,
    isLoading: false,
    isError: true,
    error: new Error('nope'),
  }),
}));

import RunDetailPage from '../pages/RunDetailPage';

describe('RunDetailPage', () => {
  it('affiche le run même si le résumé échoue', async () => {
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
    await waitFor(() => expect(screen.getByText('r1')).toBeInTheDocument());
    expect(
      screen.queryByText('Une erreur est survenue.'),
    ).not.toBeInTheDocument();
  });
});
