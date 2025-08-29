import type { JSX } from 'react';
import { useState, useEffect } from 'react';
import { useRunEvents } from '../api/hooks';
import { useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../api/http';
import useDebouncedValue from '../hooks/useDebouncedValue';

export type EventsTableProps = {
  runId: string;
  page: number;
  pageSize: number;
  level?: 'info' | 'warn' | 'error' | 'debug';
  text?: string;
  onLevelChange?: (level?: 'info' | 'warn' | 'error' | 'debug') => void;
  onTextChange?: (text: string) => void;
  onPageChange: (nextPage: number) => void;
  onPageSizeChange: (size: number) => void;
  orderBy: string;
  orderDir: 'asc' | 'desc';
  onOrderByChange: (field: string) => void;
  onOrderDirChange: (dir: 'asc' | 'desc') => void;
};

const formatDate = (d?: string): string =>
  d ? new Date(d).toLocaleString() : '-';

const EventsTable = ({
  runId,
  page,
  pageSize,
  level,
  text,
  onLevelChange,
  onTextChange,
  onPageChange,
  onPageSizeChange,
  orderBy,
  orderDir,
  onOrderByChange,
  onOrderDirChange,
}: EventsTableProps): JSX.Element => {
  const params = { page, pageSize, level, text, orderBy, orderDir };
  const queryClient = useQueryClient();
  const eventsQuery = useRunEvents(runId, params, {
    enabled: Boolean(runId),
  });

  const [textInput, setTextInput] = useState(text ?? '');
  const debouncedText = useDebouncedValue(textInput, 300);
  useEffect(() => {
    setTextInput(text ?? '');
  }, [text]);
  useEffect(() => {
    if (onTextChange && debouncedText !== (text ?? '')) {
      onTextChange(debouncedText);
    }
  }, [debouncedText, onTextChange, text]);

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

  const total = meta?.total;
  const currentPage = page;
  const size = pageSize;
  const maxPage = total !== undefined ? Math.ceil(total / size) : undefined;
  const hasPrev = Boolean(meta?.prev);
  const hasNext = Boolean(meta?.next);

  return (
    <div>
      <div style={{ marginBottom: '8px' }}>
        <select
          aria-label="level-filter"
          data-testid="events-level-filter"
          value={level ?? ''}
          onChange={(e) =>
            onLevelChange?.(
              e.target.value
                ? (e.target.value as 'debug' | 'info' | 'warn' | 'error')
                : undefined,
            )
          }
        >
          <option value="">Tous</option>
          <option value="debug">debug</option>
          <option value="info">info</option>
          <option value="warn">warn</option>
          <option value="error">error</option>
        </select>
        <input
          aria-label="text-filter"
          data-testid="events-text-filter"
          placeholder="Filtrer le message"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          style={{ marginLeft: '8px' }}
        />
      </div>
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
          Page {currentPage}
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
              onOrderByChange(e.target.value);
              onPageChange(1);
            }}
            style={{ marginLeft: '4px' }}
          >
            {['timestamp', 'level'].map((f) => (
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

export default EventsTable;
