import type { JSX } from 'react';
import { useRunNodes } from '../api/hooks';
import { useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../api/http';

export type NodesTableProps = {
  runId: string;
  page: number;
  pageSize: number;
  onPageChange: (nextPage: number) => void;
  onPageSizeChange: (size: number) => void;
};

const formatDate = (d?: string): string =>
  d ? new Date(d).toLocaleString() : '-';

const formatDuration = (ms?: number): string =>
  ms !== undefined ? `${Math.round(ms / 1000)}s` : '-';

const NodesTable = ({
  runId,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: NodesTableProps): JSX.Element => {
  const params = { page, pageSize };
  const queryClient = useQueryClient();
  const nodesQuery = useRunNodes(runId, params, {
    enabled: Boolean(runId),
  });

  const retry = (): void => {
    queryClient.invalidateQueries({
      queryKey: ['run', runId, 'nodes', params],
    });
  };

  if (nodesQuery.isLoading) {
    return (
      <table>
        <caption>Nodes</caption>
        <thead>
          <tr>
            <th>ID</th>
            <th>Rôle</th>
            <th>Statut</th>
            <th>Début</th>
            <th>Fin</th>
            <th>Durée</th>
            <th>Checksum</th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 3 }).map((_, i) => (
            <tr key={i} className="skeleton">
              <td colSpan={7}>Chargement...</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  if (nodesQuery.isError) {
    const err = nodesQuery.error as unknown;
    return (
      <div>
        <p>Une erreur est survenue.</p>
        {err instanceof ApiError && <p>Request ID: {err.requestId}</p>}
        <button onClick={retry}>Réessayer</button>
      </div>
    );
  }

  const items = nodesQuery.data?.items ?? [];
  const meta = nodesQuery.data?.meta;

  if (items.length === 0) {
    return <p>Aucune donnée.</p>;
  }

  const total = meta?.total ?? 0;
  const currentPage = meta?.page ?? page;
  const size = meta?.page_size ?? pageSize;
  const maxPage = size > 0 ? Math.ceil(total / size) : 1;

  const hasPrev = currentPage > 1;
  const hasNext = currentPage < maxPage;

  const calcDuration = (
    started?: string,
    ended?: string,
    dms?: number,
  ): string => {
    let ms = dms;
    if (ms === undefined && started && ended) {
      ms = new Date(ended).getTime() - new Date(started).getTime();
    }
    return formatDuration(ms);
  };

  return (
    <div>
      <table>
        <caption>Nodes</caption>
        <thead>
          <tr>
            <th>ID</th>
            <th>Rôle</th>
            <th>Statut</th>
            <th>Début</th>
            <th>Fin</th>
            <th>Durée</th>
            <th>Checksum</th>
          </tr>
        </thead>
        <tbody>
          {items.map((node) => (
            <tr key={node.id}>
              <td>{node.id}</td>
              <td>{node.role ?? '-'}</td>
              <td>
                <span className={`badge status-${node.status}`}>
                  {node.status}
                </span>
              </td>
              <td>{formatDate(node.started_at)}</td>
              <td>{formatDate(node.ended_at)}</td>
              <td>
                {calcDuration(node.started_at, node.ended_at, node.duration_ms)}
              </td>
              <td>{node.checksum ?? '-'}</td>
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

export default NodesTable;
