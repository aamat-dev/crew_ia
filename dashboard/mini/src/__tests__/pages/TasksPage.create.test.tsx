import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';

vi.mock('../../state/ApiKeyContext', () => ({
  useApiKey: () => ({ apiKey: 'k', useEnvKey: false, setApiKey: vi.fn() }),
}));

const useTasksMock = vi.fn(() => ({
  data: { items: [], meta: { page: 1, page_size: 20, total: 0 } },
  isLoading: false,
  isError: false,
}));

const mutateAsync = vi.fn().mockResolvedValue({});
const useCreateTaskMock = vi.fn(() => ({ mutateAsync }));

vi.mock('../../api/hooks', () => ({
  useTasks: () => useTasksMock(),
  useCreateTask: () => useCreateTaskMock(),
}));

import TasksPage from '../../pages/Tasks';
import { ToastProvider } from '../../components/ToastProvider';

const setup = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <MemoryRouter initialEntries={['/tasks']}>
          <Routes>
            <Route path="/tasks" element={<TasksPage />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
};

describe('TasksPage create task', () => {
  beforeEach(() => {
    useTasksMock.mockClear();
    useCreateTaskMock.mockClear();
  });

  it('open modal and create task', async () => {
    setup();
    fireEvent.click(screen.getByText('Nouvelle tâche'));
    const input = screen.getByPlaceholderText('Titre');
    fireEvent.change(input, { target: { value: 't1' } });
    fireEvent.click(screen.getByText('Créer'));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());
    expect(screen.getByText('Tâche créée')).toBeInTheDocument();
  });
});
