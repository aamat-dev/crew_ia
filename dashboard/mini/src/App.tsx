import type { JSX } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppLayout from './layouts/AppLayout';
import RunsPage from './pages/RunsPage';
import RunDetail from './pages/RunDetail'; // S13
import TasksPage from './pages/Tasks';     // S11
import TaskDetailPage from './pages/TaskDetail'; // S11
import PlanEditor from './pages/PlanEditor';     // S12
import { ApiKeyProvider } from './state/ApiKeyContext';
import { ToastProvider } from './components/ToastProvider'; // S11

const queryClient = new QueryClient();

export const App = (): JSX.Element => (
  <ApiKeyProvider>
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <AppLayout>
            <Routes>
              <Route path="/runs" element={<RunsPage />} />
              <Route path="/runs/:id" element={<RunDetail />} />
              <Route path="/tasks" element={<TasksPage />} />
              <Route path="/tasks/:id" element={<TaskDetailPage />} />
              <Route path="/plans/:id" element={<PlanEditor />} />
              <Route path="*" element={<Navigate to="/runs" replace />} />
            </Routes>
          </AppLayout>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  </ApiKeyProvider>
);

export default App;
