import type { JSX } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppLayout from './layouts/AppLayout';
import RunsPage from './pages/RunsPage';
import RunDetailPage from './pages/RunDetailPage';
import TasksPage from './pages/Tasks';
import TaskDetailPage from './pages/TaskDetail';
import PlanEditor from './pages/PlanEditor';
import { ApiKeyProvider } from './state/ApiKeyContext';
import { ToastProvider } from './components/ToastProvider'; // présent depuis S11

const queryClient = new QueryClient();

export const App = (): JSX.Element => (
  <ApiKeyProvider>
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <AppLayout>
            <Routes>
              <Route path="/runs" element={<RunsPage />} />
              <Route path="/runs/:id" element={<RunDetailPage />} />
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
