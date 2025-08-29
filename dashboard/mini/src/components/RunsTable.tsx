import type { JSX } from 'react';
import { Status, Run } from '../api/types';
import { useRuns } from '../api/hooks';
import { useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../api/http';

export type RunsTableProps = {
  page: number;
  pageSize: number;
  status?: Status[];
  dateFrom?: string;
  dateTo?: string;
  title?: string;
  orderBy: string;
  orderDir: 'asc' | 'desc';
  onPageChange: (nextPage: number) => void;
  onPageSizeChange: (size: number) => void;
  onOrderByChange: (field: string) => void;
  onOrderDirChange: (dir: 'asc' | 'desc') => void;
  onOpenRun: (id: string) => void;
};

export const RunsTable = ({
  page,
  pageSize,
  status,
  dateFrom,
  dateTo,
  title,
  orderBy,
  orderDir,
  onPageChange,
  onPageSizeChange,
  onOrderByChange,
  onOrderDirChange,
  onOpenRun,
}: RunsTableProps): JSX.Element => {
  const params = {
    page,
    pageSize,
    status,
    dateFrom,
    dateTo,
    title,
    orderBy,
    orderDir,
  };
  const queryClient = useQueryClient();
  const runsQuery = useRuns(params);

  const retry = (): void => {
    queryClient.invalidateQueries({ queryKey: ['runs', params] });
  };

  if (runsQuery.isLoading) {
    return (
      <table>
        <caption>Runs</caption>
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Status</th>
            <th>Started</th>
            <th>Ended</th>
            <th>Counters</th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 3 }).map((_, i) => (
            <tr key={i} className="skeleton">
              <td colSpan={6}>Chargement...</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  if (runsQuery.isError) {
    const err = runsQuery.error;
    return (
      <div>
        <p>Une erreur est survenue.</p>
        {err instanceof ApiError && <p>Request ID: {err.requestId}</p>}
        <button onClick={retry}>Réessayer</button>
      </div>
    );
  }

  const items = runsQuery.data?.items ?? [];
  const meta = runsQuery.data?.meta;

  if (items.length === 0) {
    return <p>Aucune donnée.</p>;
  }

  const total = meta?.total;
  const currentPage = page;
  const size = pageSize;
  const maxPage = total !== undefined ? Math.ceil(total / size) : undefined;

  const hasPrev = Boolean(meta?.prev);
  const hasNext = Boolean(meta?.next);

  const formatDate = (d?: string): string =>
    d ? new Date(d).toLocaleString() : '-';

  const renderCounters = (run: Run): string => {
    if (!run.counters) return '-';
    const { tokens_total, nodes_total, errors } = run.counters;
    const parts: string[] = [];
    if (tokens_total !== undefined) parts.push(`T${tokens_total}`);
    if (nodes_total !== undefined) parts.push(`N${nodes_total}`);
    if (errors !== undefined) parts.push(`E${errors}`);
    return parts.join(' ');
  };

  return (
    <div>
      <table>
        <caption>Runs</caption>
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Status</th>
            <th>Started</th>
            <th>Ended</th>
            <th>Counters</th>
          </tr>
        </thead>
        <tbody>
          {items.map((run) => (
            <tr
              key={run.id}
              onClick={() => onOpenRun(run.id)}
              style={{ cursor: 'pointer' }}
            >
              <td>{run.id}</td>
              <td>{run.title ?? '-'}</td>
              <td>{run.status}</td>
              <td>{formatDate(run.started_at)}</td>
              <td>{formatDate(run.ended_at)}</td>
              <td>{renderCounters(run)}</td>
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
            {['started_at', 'ended_at', 'title', 'status'].map((f) => (
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

export default RunsTable;
