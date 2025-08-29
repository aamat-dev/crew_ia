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
  onPageChange: (nextPage: number) => void;
  onPageSizeChange: (size: number) => void;
  onOpenRun: (id: string) => void;
};

export const RunsTable = ({
  page,
  pageSize,
  status,
  dateFrom,
  dateTo,
  title,
  onPageChange,
  onPageSizeChange,
  onOpenRun,
}: RunsTableProps): JSX.Element => {
  const params = { page, pageSize, status, dateFrom, dateTo, title };
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
      </div>
    </div>
  );
};

export default RunsTable;
