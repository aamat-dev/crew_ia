import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('../../state/ApiKeyContext', () => ({
  useApiKey: () => ({ apiKey: 'k', useEnvKey: false, setApiKey: vi.fn() }),
}));

const useTaskMock = vi.fn(() => ({
  data: { id: '1', title: 't1', status: 'draft', plan: { status: 'draft' } },
  isLoading: false,
  isError: false,
}));

const mutateAsync = vi.fn();
const useGenerateTaskPlanMock = vi.fn(() => ({ mutateAsync }));

vi.mock('../../api/hooks', () => ({
  useTask: () => useTaskMock(),
  useGenerateTaskPlan: () => useGenerateTaskPlanMock(),
}));

import TaskDetailPage from '../../pages/TaskDetail';
import { ToastProvider } from '../../components/ToastProvider';

const setup = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <MemoryRouter initialEntries={['/tasks/1']}>
          <Routes>
            <Route path="/tasks/:id" element={<TaskDetailPage />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
};

describe('TaskDetailPage plan generation', () => {
  beforeEach(() => {
    mutateAsync.mockReset();
  });

  it('success', async () => {
    mutateAsync.mockResolvedValueOnce({ status: 'ready' });
    setup();
    fireEvent.click(screen.getByText('Générer le plan'));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());
    expect(screen.getByText('Plan généré')).toBeInTheDocument();
  });

  it('invalid', async () => {
    mutateAsync.mockResolvedValueOnce({ status: 'invalid', errors: ['oops'] });
    setup();
    fireEvent.click(screen.getByText('Générer le plan'));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());
    expect(screen.getByText('Plan invalide')).toBeInTheDocument();
    expect(screen.getByText('oops')).toBeInTheDocument();
  });
});
