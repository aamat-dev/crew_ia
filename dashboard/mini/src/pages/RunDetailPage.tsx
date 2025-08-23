import type { JSX } from 'react';
import { useParams } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useRun, useRunSummary } from '../api/hooks';
import { ApiError } from '../api/http';
import { useApiKey } from '../state/ApiKeyContext';

const RunDetailPage = (): JSX.Element => {
  const { apiKey, useEnvKey } = useApiKey();
  const hasKey = Boolean(apiKey) || useEnvKey;
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const runQuery = useRun(id ?? '', { enabled: hasKey && Boolean(id) });
  const summaryQuery = useRunSummary(id ?? '', {
    enabled: hasKey && Boolean(id),
  });

  const retry = (): void => {
    queryClient.invalidateQueries({ queryKey: ['run', id] });
    queryClient.invalidateQueries({ queryKey: ['run', id, 'summary'] });
  };

  if (!hasKey) {
    return <div>Veuillez saisir une clé API pour continuer.</div>;
  }

  if (runQuery.isLoading || summaryQuery.isLoading) {
    return <div className="skeleton">Chargement...</div>;
  }

  if (runQuery.isError || summaryQuery.isError) {
    const err = (runQuery.error ?? summaryQuery.error) as unknown;
    return (
      <div>
        <p>Une erreur est survenue.</p>
        {err instanceof ApiError && <p>Request ID: {err.requestId}</p>}
        <button onClick={retry}>Réessayer</button>
      </div>
    );
  }

  const run = runQuery.data;
  if (!run) {
    return <p>Aucune donnée.</p>;
  }

  return (
    <div>
      <h2>{run.title ?? run.id}</h2>
      <p>{summaryQuery.data?.summary ?? ''}</p>
      <section>DagView (placeholder)</section>
      <section>Nodes (placeholder)</section>
      <section>Events (placeholder)</section>
      <section>Artifacts (placeholder)</section>
    </div>
  );
};

export default RunDetailPage;
