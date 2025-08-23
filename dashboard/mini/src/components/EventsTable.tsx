import type { JSX } from 'react';
import { useRunEvents } from '../api/hooks';
import { useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../api/http';

export type EventsTableProps = {
  runId: string;
  page: number;
  pageSize: number;
  level?: 'info' | 'warn' | 'error' | 'debug';
  text?: string;
  onPageChange: (nextPage: number) => void;
  onPageSizeChange: (size: number) => void;
};

const formatDate = (d?: string): string =>
  d ? new Date(d).toLocaleString() : '-';

const EventsTable = ({
  runId,
  page,
  pageSize,
  level,
  text,
  onPageChange,
  onPageSizeChange,
}: EventsTableProps): JSX.Element => {
  const params = { page, pageSize, level, text };
  const queryClient = useQueryClient();
  const eventsQuery = useRunEvents(runId, params, {
    enabled: Boolean(runId),
  });

  const retry = (): void => {
    queryClient.invalidateQueries({
      queryKey: ['run', runId, 'events', params],
    });
  };

  if (eventsQuery.isLoading) {
    return (
      <table>
        <caption>Events</caption>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Niveau</th>
            <th>Message</th>
            <th>Request ID</th>
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

  if (eventsQuery.isError) {
    const err = eventsQuery.error as unknown;
    return (
      <div>
        <p>Une erreur est survenue.</p>
        {err instanceof ApiError && <p>Request ID: {err.requestId}</p>}
        <button onClick={retry}>Réessayer</button>
      </div>
    );
  }

  const items = eventsQuery.data?.items ?? [];
  const meta = eventsQuery.data?.meta;

  if (items.length === 0) {
    return <p>Aucune donnée.</p>;
  }

  const total = meta?.total ?? 0;
  const currentPage = meta?.page ?? page;
  const size = meta?.page_size ?? pageSize;
  const maxPage = size > 0 ? Math.ceil(total / size) : 1;
  const hasPrev = currentPage > 1;
  const hasNext = currentPage < maxPage;

  return (
    <div>
      <table>
        <caption>Events</caption>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Niveau</th>
            <th>Message</th>
            <th>Request ID</th>
          </tr>
        </thead>
        <tbody>
          {items.map((ev) => (
            <tr key={ev.id}>
              <td>{formatDate(ev.timestamp)}</td>
              <td>
                <span className={`badge level-${ev.level}`}>{ev.level}</span>
              </td>
              <td>{ev.message}</td>
              <td>{ev.request_id ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ marginTop: '8px' }}>
        <button onClick={() => onPageChange(page - 1)} disabled={!hasPrev}>
          Précédent
        </button>
        <span style={{ margin: '0 8px' }}>
          Page {currentPage} / {maxPage || 1}
        </span>
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
      </div>
    </div>
  );
};

export default EventsTable;
