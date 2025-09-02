import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import PlanEditor from '../pages/PlanEditor';

const renderEditor = () => {
  render(
    <MemoryRouter initialEntries={['/plans/p1']}>
      <Routes>
        <Route path="/plans/:id" element={<PlanEditor />} />
      </Routes>
    </MemoryRouter>,
  );
};

describe('PlanEditor assignments', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('upsert assign', async () => {
    const plan = {
      id: 'p1',
      status: 'draft',
      graph: { nodes: [{ id: 'n1' }], edges: [] },
      assignments: [],
    };
    const fetchMock = vi.fn<
      (url: RequestInfo, _opts?: RequestInit) => Promise<Response>
    >((url) => {
        if (url.toString().endsWith('/plans/p1')) {
          return Promise.resolve(
            new Response(JSON.stringify(plan), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            }),
          );
        }
        if (url.toString().endsWith('/plans/p1/assignments')) {
          return Promise.resolve(
            new Response('{}', {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            }),
          );
        }
        if (url.toString().endsWith('/plans/p1/status')) {
          return Promise.resolve(
            new Response('{}', {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            }),
          );
        }
        return Promise.reject(new Error('unknown url'));
      });
    (global as any).fetch = fetchMock;

    renderEditor();

    const nodeBtn = await screen.findByTestId('plan-node-n1');
    fireEvent.click(nodeBtn);
    fireEvent.change(screen.getByLabelText('role'), { target: { value: 'r1' } });
    fireEvent.change(screen.getByLabelText('agent'), { target: { value: 'a1' } });
    fireEvent.change(screen.getByLabelText('backend'), { target: { value: 'b1' } });
    fireEvent.change(screen.getByLabelText('model'), { target: { value: 'm1' } });
    fireEvent.change(screen.getByLabelText('params'), { target: { value: '{"x":1}' } });
    fireEvent.click(screen.getByText('Save Assignments'));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));

    fireEvent.change(screen.getByLabelText('backend'), {
      target: { value: 'b2' },
    });
    await waitFor(() =>
      expect(screen.getByLabelText('backend')).toHaveValue('b2'),
    );
    fireEvent.click(screen.getByText('Save Assignments'));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));

    const calls = (
      fetchMock.mock.calls as Array<[RequestInfo, RequestInit | undefined]>
    ).filter(([url]) => url.toString().endsWith('/plans/p1/assignments'));
    expect(JSON.parse(calls[0][1]?.body as string)).toEqual({
      items: [
        {
          node_id: 'n1',
          role: 'r1',
          agent_id: 'a1',
          llm_backend: 'b1',
          llm_model: 'm1',
          params: { x: 1 },
        },
      ],
    });
    expect(JSON.parse(calls[1][1]?.body as string)).toEqual({
      items: [
        {
          node_id: 'n1',
          role: 'r1',
          agent_id: 'a1',
          llm_backend: 'b2',
          llm_model: 'm1',
          params: { x: 1 },
        },
      ],
    });
  });

  it('node unknown -> erreur affichée', async () => {
    const plan = {
      id: 'p1',
      status: 'draft',
      graph: { nodes: [{ id: 'n1' }], edges: [] },
      assignments: [],
    };
    const fetchMock = vi.fn<
      (url: RequestInfo, _opts?: RequestInit) => Promise<Response>
    >((url) => {
        if (url.toString().endsWith('/plans/p1')) {
          return Promise.resolve(
            new Response(JSON.stringify(plan), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            }),
          );
        }
        if (url.toString().endsWith('/plans/p1/assignments')) {
          return Promise.resolve(
            new Response(JSON.stringify({ error: 'unknown node' }), {
              status: 400,
              headers: { 'Content-Type': 'application/json' },
            }),
          );
        }
        return Promise.reject(new Error('unknown url'));
      });
    (global as any).fetch = fetchMock;

    renderEditor();

    const nodeBtn = await screen.findByTestId('plan-node-n1');
    fireEvent.click(nodeBtn);
    fireEvent.change(screen.getByLabelText('role'), { target: { value: 'r1' } });
    fireEvent.change(screen.getByLabelText('agent'), { target: { value: 'a1' } });
    fireEvent.change(screen.getByLabelText('backend'), { target: { value: 'b1' } });
    fireEvent.change(screen.getByLabelText('model'), { target: { value: 'm1' } });
    fireEvent.click(screen.getByText('Save Assignments'));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('unknown node');
  });
});
