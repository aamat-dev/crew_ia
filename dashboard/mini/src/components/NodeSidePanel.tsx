import type { JSX } from 'react';
import { useEffect, useState } from 'react';
import { useNodeArtifacts } from '../api/hooks';
import { patchNode } from '../api/client';

interface NodeSidePanelProps {
  node: { id: string; status: string; role?: string };
  onClose: () => void;
  onUpdated: () => void;
}

const NodeSidePanel = ({ node, onClose, onUpdated }: NodeSidePanelProps): JSX.Element => {
  const [requestId, setRequestId] = useState<string | undefined>();
  const [overridePrompt, setOverridePrompt] = useState('');
  const [overrideParams, setOverrideParams] = useState('');
  const [logText, setLogText] = useState('');
  const [sidecar, setSidecar] = useState('');

  const artifactsQuery = useNodeArtifacts(
    node.id,
    { page: 1, pageSize: 50 },
    { enabled: Boolean(node.id) },
  );

  useEffect(() => {
    setRequestId(undefined);
    setOverridePrompt('');
    setOverrideParams('');
    setLogText('');
    setSidecar('');
  }, [node.id]);

  useEffect(() => {
    const fetchArtifacts = async () => {
      if (!artifactsQuery.data) return;
      const log = artifactsQuery.data.items.find((a) => a.kind === 'log');
      if (log) {
        try {
          const res = await fetch(log.url);
          setLogText(await res.text());
        } catch {
          setLogText('');
        }
      }
      const sc = artifactsQuery.data.items.find((a) => a.kind === 'llm_sidecar');
      if (sc) {
        try {
          const res = await fetch(sc.url);
          setSidecar(await res.text());
        } catch {
          setSidecar('');
        }
      }
    };
    fetchArtifacts();
  }, [artifactsQuery.data]);

  const doAction = async (body: Record<string, unknown>) => {
    if (!window.confirm('Confirmer ?')) return;
    const { requestId } = await patchNode(node.id, body);
    setRequestId(requestId);
    await artifactsQuery.refetch();
    onUpdated();
  };

  const onOverride = () => {
    let params: unknown;
    if (overrideParams) {
      try {
        params = JSON.parse(overrideParams);
      } catch {
        alert('Paramètres JSON invalides');
        return;
      }
    }
    void doAction({ action: 'override', prompt: overridePrompt || undefined, params });
  };

  return (
    <aside style={{ borderLeft: '1px solid #ccc', padding: 16, width: 320 }} data-testid="node-sidepanel">
      <button onClick={onClose}>Fermer</button>
      <h3>{node.role ?? node.id}</h3>
      <p>Statut: {node.status}</p>
      <div>
        <button onClick={() => void doAction({ action: 'pause' })}>Pause</button>
        <button onClick={() => void doAction({ action: 'resume' })}>Resume</button>
        <button onClick={() => void doAction({ action: 'skip' })}>Skip</button>
      </div>
      <div>
        <h4>Override</h4>
        <input
          placeholder="prompt"
          value={overridePrompt}
          onChange={(e) => setOverridePrompt(e.target.value)}
        />
        <textarea
          placeholder="params JSON"
          value={overrideParams}
          onChange={(e) => setOverrideParams(e.target.value)}
        />
        <button onClick={onOverride}>Envoyer</button>
      </div>
      {requestId && <p>Request ID: {requestId}</p>}
      <div>
        <h4>Logs</h4>
        <pre style={{ whiteSpace: 'pre-wrap' }}>{logText}</pre>
      </div>
      <div>
        <h4>Artifacts</h4>
        <ul>
          {artifactsQuery.data?.items.map((a) => (
            <li key={a.id}>
              <a href={a.url} target="_blank" rel="noreferrer">
                {a.name}
              </a>
            </li>
          ))}
        </ul>
      </div>
      {sidecar && (
        <div>
          <h4>Sidecar</h4>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{sidecar}</pre>
        </div>
      )}
    </aside>
  );
};

export default NodeSidePanel;
