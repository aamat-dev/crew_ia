import type { JSX } from 'react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import DagView from '../components/DagView';
import NodeSidePanel from '../components/NodeSidePanel';
import type { RunDetail as RunType, Status } from '../api/types';
import { fetchJson, ApiError } from '../api/http';
import { useApiKey } from '../state/ApiKeyContext';

const apiToUiStatus = (status: string): Status => {
  switch (status) {
    case 'pending':
      return 'queued';
    case 'completed':
      return 'succeeded';
    default:
      return status as Status;
  }
};

const fetchRun = async (id: string, signal: AbortSignal) => {
  const { data, requestId } = await fetchJson<any>(`/runs/${id}`, { signal });
  const run: RunType = { ...data, status: apiToUiStatus(data.status) };
  if (run.dag) {
    run.dag = {
      nodes: (run.dag.nodes as any).map((n: any) => ({
        ...n,
        status: apiToUiStatus(n.status),
      })),
      edges: run.dag.edges,
    };
  }
  return { run, requestId };
};

const RunDetail = (): JSX.Element => {
  const { id } = useParams<{ id: string }>();
  const { apiKey, useEnvKey } = useApiKey();
  const hasKey = Boolean(apiKey) || useEnvKey;
  const [selectedNodeId, setSelectedNodeId] = useState<string | undefined>();
  type DagNode = RunType['dag'] extends { nodes: (infer N)[] } ? N : never;
  const [selectedNode, setSelectedNode] = useState<DagNode | undefined>();
  const [lastRequestId, setLastRequestId] = useState<string | undefined>();
  const runQuery = useQuery({
    queryKey: ['run', id],
    queryFn: ({ signal }) => fetchRun(id!, signal),
    enabled: hasKey && Boolean(id),
    refetchInterval: (query) => {
      const status = query.state.data?.run.status;
      return status === 'running' || status === 'queued' ? 2000 : false;
    },
  });

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
      </div>
    );
  }
  const run = runQuery.data?.run;
  useEffect(() => {
    if (selectedNodeId && run?.dag) {
      const n = run.dag.nodes.find((nd) => nd.id === selectedNodeId);
      if (n) setSelectedNode(n);
    }
  }, [run, selectedNodeId]);
  if (!run) return <p>Aucune donnée.</p>;
  return (
    <div>
      <h2>{run.title ?? run.id}</h2>
      <p>Request ID: {lastRequestId ?? runQuery.data?.requestId}</p>
      {run.dag && (
        <DagView
          dag={run.dag}
          onSelectNode={(nid) => setSelectedNodeId(nid)}
          selectedNodeId={selectedNodeId}
        />
      )}
      {selectedNode && (
        <NodeSidePanel
          node={selectedNode}
          onClose={() => setSelectedNodeId(undefined)}
          onUpdated={() => runQuery.refetch()}
          onAction={(rid) => setLastRequestId(rid)}
        />
      )}
    </div>
  );
};

export default RunDetail;
