import type { JSX } from 'react';
import { Task } from '../api/types';
import { useTasks } from '../api/hooks';
import { useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../api/http';

export type TasksTableProps = {
  page: number;
  pageSize: number;
  orderBy: 'created_at' | 'title' | 'status';
  orderDir: 'asc' | 'desc';
  onPageChange: (next: number) => void;
  onPageSizeChange: (s: number) => void;
  onOrderByChange: (f: 'created_at' | 'title' | 'status') => void;
  onOrderDirChange: (d: 'asc' | 'desc') => void;
  onOpenTask: (id: string) => void;
};

export const TasksTable = ({
  page,
  pageSize,
  orderBy,
  orderDir,
  onPageChange,
  onPageSizeChange,
  onOrderByChange,
  onOrderDirChange,
  onOpenTask,
}: TasksTableProps): JSX.Element => {
  const params = { page, pageSize, orderBy, orderDir };
  const queryClient = useQueryClient();
  const tasksQuery = useTasks(params);

  const retry = (): void => {
    queryClient.invalidateQueries({ queryKey: ['tasks', params] });
  };

  if (tasksQuery.isLoading) {
    return (
      <table>
        <caption>Tâches</caption>
        <thead>
          <tr>
            <th>ID</th>
            <th>Titre</th>
            <th>Statut</th>
            <th>Créée</th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 3 }).map((_, i) => (
            <tr key={i} className="skeleton">
              <td colSpan={4}>Chargement...</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  if (tasksQuery.isError) {
    const err = tasksQuery.error;
    return (
      <div>
        <p>Une erreur est survenue.</p>
        {err instanceof ApiError && <p>Request ID: {err.requestId}</p>}
        <button onClick={retry}>Réessayer</button>
      </div>
    );
  }

  const items = tasksQuery.data?.items ?? [];
  const meta = tasksQuery.data?.meta;

  if (items.length === 0) {
    return <p>Aucune donnée.</p>;
  }

  const total = meta?.total;
  const size = pageSize;
  const maxPage = total !== undefined ? Math.ceil(total / size) : undefined;
  const hasPrev = Boolean(meta?.prev);
  const hasNext = Boolean(meta?.next);

  const formatDate = (d?: string): string =>
    d ? new Date(d).toLocaleString() : '-';

  return (
    <div>
      <table>
        <caption>Tâches</caption>
        <thead>
          <tr>
            <th>ID</th>
            <th>Titre</th>
            <th>Statut</th>
            <th>Créée</th>
          </tr>
        </thead>
        <tbody>
          {items.map((t: Task) => (
            <tr
              key={t.id}
              onClick={() => onOpenTask(t.id)}
              style={{ cursor: 'pointer' }}
            >
              <td>{t.id}</td>
              <td>{t.title}</td>
              <td>{t.status}</td>
              <td>{formatDate(t.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ marginTop: '8px' }}>
        <button onClick={() => onPageChange(page - 1)} disabled={!hasPrev}>
          Précédent
        </button>
        <span style={{ margin: '0 8px' }}>
          Page {page}
          {maxPage ? ` / ${maxPage}` : ''}
        </span>
        {total !== undefined && (
          <span style={{ marginRight: '8px' }}>Total: {total}</span>
        )}
        <button onClick={() => onPageChange(page + 1)} disabled={!hasNext}>
          Suivant
        </button>
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          style={{ marginLeft: '8px' }}
        >
          {[10, 20, 50].map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <label style={{ marginLeft: '8px' }}>
          Trier par
          <select
            aria-label="order-by"
            value={orderBy}
            onChange={(e) => {
              onOrderByChange(
                e.target.value as 'created_at' | 'title' | 'status',
              );
              onPageChange(1);
            }}
            style={{ marginLeft: '4px' }}
          >
            {['created_at', 'title', 'status'].map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
        </label>
        <label style={{ marginLeft: '8px' }}>
          Direction
          <select
            aria-label="order-dir"
            value={orderDir}
            onChange={(e) => {
              onOrderDirChange(e.target.value as 'asc' | 'desc');
              onPageChange(1);
            }}
            style={{ marginLeft: '4px' }}
          >
            <option value="asc">asc</option>
            <option value="desc">desc</option>
          </select>
        </label>
      </div>
    </div>
  );
};

export default TasksTable;
