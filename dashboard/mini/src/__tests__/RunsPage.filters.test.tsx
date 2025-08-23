import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { Status } from '../api/types';

vi.mock('../state/ApiKeyContext', () => ({
  useApiKey: () => ({
    apiKey: 'k',
    useEnvKey: false,
    setApiKey: vi.fn(),
    setUseEnvKey: vi.fn(),
    reset: vi.fn(),
  }),
}));

const useRunsMock = vi.fn(
  (params: {
    page: number;
    pageSize: number;
    status?: Status[];
    dateFrom?: string;
    dateTo?: string;
    title?: string;
  }) => ({
    data: {
      items: [
        {
          id: '1',
          title: 'r1',
          status: 'queued',
          started_at: undefined,
          ended_at: undefined,
        },
      ],
      meta: { page: params.page, page_size: params.pageSize, total: 40 },
    },
    isLoading: false,
    isError: false,
  }),
);

vi.mock('../api/hooks', () => ({
  useRuns: (params: Parameters<typeof useRunsMock>[0]) => useRunsMock(params),
}));

import RunsPage from '../pages/RunsPage';

const setup = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<RunsPage />} />
          <Route path="/runs/:id" element={<div>detail</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe.skip('RunsPage filters', () => {
  beforeEach(() => {
    useRunsMock.mockClear();
  });

  it('debounce title', async () => {
    vi.useFakeTimers();
    setup();
    expect(useRunsMock).toHaveBeenCalledTimes(1);
    const input = screen.getByPlaceholderText('Titre');
    fireEvent.change(input, { target: { value: 'a' } });
    fireEvent.change(input, { target: { value: 'ab' } });
    await vi.advanceTimersByTimeAsync(300);
    await waitFor(() => expect(useRunsMock).toHaveBeenCalledTimes(2));
    vi.useRealTimers();
  });

  it('changer un filtre remet la page à 1', async () => {
    setup();
    expect(useRunsMock).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('Suivant'));
    await waitFor(() => expect(useRunsMock).toHaveBeenCalledTimes(2));
    expect(useRunsMock.mock.calls[1][0].page).toBe(2);
    fireEvent.click(screen.getByLabelText('running'));
    await waitFor(() => expect(useRunsMock).toHaveBeenCalledTimes(3));
    expect(useRunsMock.mock.calls[2][0].page).toBe(1);
  });

  it('clic sur une ligne redirige vers le détail', async () => {
    setup();
    expect(screen.getByText('r1')).toBeInTheDocument();
    fireEvent.click(screen.getByText('r1'));
    await waitFor(() => expect(screen.getByText('detail')).toBeInTheDocument());
  });
});
