import type { JSX } from 'react';
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useRun, useRunSummary } from '../api/hooks';
import { ApiError } from '../api/http';
import { useApiKey } from '../state/ApiKeyContext';
import RunSummary from '../components/RunSummary';
import DagView from '../components/DagView';
import NodesTable from '../components/NodesTable';
import EventsTable from '../components/EventsTable';
import ArtifactsList from '../components/ArtifactsList';

const RunDetailPage = (): JSX.Element => {
  const { apiKey, useEnvKey } = useApiKey();
  const hasKey = Boolean(apiKey) || useEnvKey;
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const runQuery = useRun(id ?? '', { enabled: hasKey && Boolean(id) });
  const summaryQuery = useRunSummary(id ?? '', {
    enabled: hasKey && Boolean(id),
  });

  const [nodesPage, setNodesPage] = useState(1);
  const [nodesPageSize, setNodesPageSize] = useState(20);
  const [eventsPage, setEventsPage] = useState(1);
  const [eventsPageSize, setEventsPageSize] = useState(20);
  const [selectedNodeId, setSelectedNodeId] = useState<string | undefined>(
    undefined,
  );
  const [eventsLevel, setEventsLevel] = useState<
    'debug' | 'info' | 'warn' | 'error' | undefined
  >(undefined);
  const [eventsText, setEventsText] = useState('');

  const retry = (): void => {
    queryClient.invalidateQueries({ queryKey: ['run', id] });
    queryClient.invalidateQueries({ queryKey: ['run', id, 'summary'] });
  };

  if (!hasKey) {
    return <div>Veuillez saisir une clé API pour continuer.</div>;
  }

  if (runQuery.isLoading) {
    return <div className="skeleton">Chargement...</div>;
  }

  if (runQuery.isError) {
    const err = runQuery.error as unknown;
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

  let summary = summaryQuery.data;
  if (summaryQuery.isError) {
    console.warn('run summary unavailable', summaryQuery.error);
    summary = undefined;
  }

  return (
    <div>
      <h2>{run.title ?? run.id}</h2>
      {summary && <RunSummary run={run} summary={summary} />}
      {run.dag && (
        <section>
          <DagView dag={run.dag} />
        </section>
      )}
      <section>
        <h3>Nodes</h3>
        <NodesTable
          runId={run.id}
          page={nodesPage}
          pageSize={nodesPageSize}
          selectedNodeId={selectedNodeId}
          onSelectNode={setSelectedNodeId}
          onPageChange={setNodesPage}
          onPageSizeChange={(s) => {
            setNodesPageSize(s);
            setNodesPage(1);
          }}
        />
      </section>
      <section>
        <h3>Events</h3>
        <EventsTable
          runId={run.id}
          page={eventsPage}
          pageSize={eventsPageSize}
          level={eventsLevel}
          text={eventsText}
          onLevelChange={(lvl) => {
            setEventsLevel(lvl);
            setEventsPage(1);
          }}
          onTextChange={(t) => {
            setEventsText(t);
            setEventsPage(1);
          }}
          onPageChange={setEventsPage}
          onPageSizeChange={(s) => {
            setEventsPageSize(s);
            setEventsPage(1);
          }}
        />
      </section>
      <section>
        <h3>Artifacts</h3>
        <ArtifactsList runId={run.id} nodeId={selectedNodeId} />
      </section>
    </div>
  );
};

export default RunDetailPage;
