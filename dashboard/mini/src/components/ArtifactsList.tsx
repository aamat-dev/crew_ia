import type { JSX } from 'react';
import { useNodeArtifacts } from '../api/hooks';
import { useQueryClient } from '@tanstack/react-query';
import { ApiError } from '../api/http';
import { getApiBaseUrl } from '../config/env';

export type ArtifactsListProps = {
  runId: string;
  nodeId?: string;
};

const formatSize = (bytes?: number): string => {
  if (bytes === undefined) return '-';
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB'];
  let i = -1;
  let value = bytes;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i++;
  }
  return `${value.toFixed(1)} ${units[i]}`;
};

const ArtifactsList = ({
  runId: _runId,
  nodeId,
}: ArtifactsListProps): JSX.Element => {
  void _runId;
  const params = { page: 1, pageSize: 50 };
  const queryClient = useQueryClient();
  const artifactsQuery = useNodeArtifacts(nodeId ?? '', params, {
    enabled: Boolean(nodeId),
  });

  const retry = (): void => {
    if (nodeId) {
      queryClient.invalidateQueries({
        queryKey: ['node', nodeId, 'artifacts', params],
      });
    }
  };

  if (!nodeId) {
    return <p>Aucun nœud sélectionné.</p>;
  }

  if (artifactsQuery.isLoading) {
    return (
      <table>
        <caption>Artifacts</caption>
        <thead>
          <tr>
            <th>Nom</th>
            <th>Type</th>
            <th>Taille</th>
            <th>Télécharger</th>
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

  if (artifactsQuery.isError) {
    const err = artifactsQuery.error as unknown;
    return (
      <div>
        <p>Une erreur est survenue.</p>
        {err instanceof ApiError && <p>Request ID: {err.requestId}</p>}
        <button onClick={retry}>Réessayer</button>
      </div>
    );
  }

  const items = artifactsQuery.data?.items ?? [];
  const meta = artifactsQuery.data?.meta;
  const total = meta?.total;

  if (items.length === 0) {
    return <p>Aucun artefact.</p>;
  }

  return (
    <>
      {total !== undefined && <p>Total: {total}</p>}
      <table>
        <caption>Artifacts</caption>
      <thead>
        <tr>
          <th>Nom</th>
          <th>Type</th>
          <th>Taille</th>
          <th>Télécharger</th>
        </tr>
      </thead>
      <tbody>
        {items.map((a) => (
          <tr key={a.id}>
            <td>{a.name}</td>
            <td>{a.kind}</td>
            <td>{formatSize(a.size_bytes)}</td>
            <td>
              <a
                href={`${getApiBaseUrl()}/artifacts/${a.id}/download`}
                target="_blank"
                rel="noreferrer"
              >
                Télécharger
              </a>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
    </>
  );
};

export default ArtifactsList;
