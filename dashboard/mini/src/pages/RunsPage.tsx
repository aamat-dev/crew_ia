import type { JSX } from 'react';
import { Link } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useRuns } from '../api/hooks';
import { ApiError } from '../api/http';
import { useApiKey } from '../state/ApiKeyContext';

const RunsPage = (): JSX.Element => {
  const { apiKey, useEnvKey } = useApiKey();
  const hasKey = Boolean(apiKey) || useEnvKey;

  const queryClient = useQueryClient();
  const runsQuery = useRuns({ page: 1, pageSize: 20 }, { enabled: hasKey });

  const retry = (): void => {
    queryClient.invalidateQueries({ queryKey: ['runs'] });
  };

  if (!hasKey) {
    return <div>Veuillez saisir une clé API pour continuer.</div>;
  }

  let content: JSX.Element;
  if (runsQuery.isLoading) {
    content = (
      <ul>
        {Array.from({ length: 3 }).map((_, i) => (
          <li key={i} className="skeleton">
            Chargement...
          </li>
        ))}
      </ul>
    );
  } else if (runsQuery.isError) {
    const err = runsQuery.error;
    content = (
      <div>
        <p>Une erreur est survenue.</p>
        {err instanceof ApiError && <p>Request ID: {err.requestId}</p>}
        <button onClick={retry}>Réessayer</button>
      </div>
    );
  } else {
    const items = runsQuery.data?.items ?? [];
    if (items.length === 0) {
      content = <p>Aucune donnée.</p>;
    } else {
      content = (
        <ul>
          {items.map((run) => (
            <li key={run.id}>
              <Link to={`/runs/${run.id}`}>{run.title ?? run.id}</Link>
            </li>
          ))}
        </ul>
      );
    }
  }

  return (
    <div>
      <div
        style={{
          border: '1px solid #ccc',
          padding: '8px',
          marginBottom: '16px',
        }}
      >
        Filtres (placeholder)
      </div>
      {content}
    </div>
  );
};

export default RunsPage;
