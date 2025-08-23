import type { JSX } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppLayout from './layouts/AppLayout';
import RunsPage from './pages/RunsPage';
import RunDetailPage from './pages/RunDetailPage';
import { ApiKeyProvider } from './state/ApiKeyContext';

const queryClient = new QueryClient();

export const App = (): JSX.Element => (
  <ApiKeyProvider>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppLayout>
          <Routes>
            <Route path="/runs" element={<RunsPage />} />
            <Route path="/runs/:id" element={<RunDetailPage />} />
            <Route path="*" element={<Navigate to="/runs" replace />} />
          </Routes>
        </AppLayout>
      </BrowserRouter>
    </QueryClientProvider>
  </ApiKeyProvider>
);

export default App;
