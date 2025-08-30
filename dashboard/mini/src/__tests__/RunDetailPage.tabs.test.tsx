import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect } from 'vitest';

vi.mock('../state/ApiKeyContext', () => ({
  useApiKey: () => ({ apiKey: 'k', useEnvKey: false, setApiKey: vi.fn() }),
}));

const run = { id: '1', title: 'r1', status: 'queued' as const };
const nodes = [{ id: 'n1', status: 'succeeded', role: 'r1' }];

type UseReturn = {
  data: unknown;
  isLoading: boolean;
  isError: boolean;
};

vi.mock('../api/hooks', () => ({
  useRun: (): UseReturn => ({ data: run, isLoading: false, isError: false }),
  useRunSummary: (): UseReturn => ({
    data: undefined,
    isLoading: false,
    isError: false,
  }),
  useRunNodes: (): UseReturn => ({
    data: { items: nodes, meta: { page: 1, page_size: 20, total: 1 } },
    isLoading: false,
    isError: false,
  }),
  useRunEvents: (): UseReturn => ({
    data: { items: [], meta: { page: 1, page_size: 20, total: 0 } },
    isLoading: false,
    isError: false,
  }),
  useNodeArtifacts: (): UseReturn => ({
    data: { items: [], meta: { page: 1, page_size: 50, total: 0 } },
    isLoading: false,
    isError: false,
  }),
}));

import RunDetailPage from '../pages/RunDetailPage';

describe('RunDetailPage tabs', () => {
  it('affiche et utilise les onglets', async () => {
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

    ['Résumé', 'DAG', 'Nodes', 'Events', 'Artifacts'].forEach((t) =>
      expect(screen.getByRole('tab', { name: t })).toBeInTheDocument(),
    );

    expect(screen.getByRole('tab', { name: 'Résumé' })).toHaveAttribute(
      'aria-selected',
      'true',
    );

    fireEvent.click(screen.getByRole('tab', { name: 'Nodes' }));
    expect(screen.getByRole('tab', { name: 'Nodes' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
    await screen.findByRole('table', { name: 'Nodes' });

    fireEvent.click(screen.getByRole('tab', { name: 'Artifacts' }));
    expect(screen.getByRole('tab', { name: 'Artifacts' })).toHaveAttribute(
      'aria-selected',
      'true',
    );
    await screen.findByText('Aucun nœud sélectionné.');
  });
});
