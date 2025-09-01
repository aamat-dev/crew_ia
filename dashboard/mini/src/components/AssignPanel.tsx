import { useEffect, useState } from 'react';
import type { Assignment } from '../api/types';

interface AssignPanelProps {
  nodeId?: string | null;
  assignment?: Assignment;
  onSave: (a: Assignment) => void | Promise<void>;
  saving?: boolean;
  error?: string | null;
  success?: string | null;
}

const AssignPanel = ({
  nodeId,
  assignment,
  onSave,
  saving,
  error,
  success,
}: AssignPanelProps) => {
  const [role, setRole] = useState('');
  const [agent, setAgent] = useState('');
  const [backend, setBackend] = useState('');
  const [model, setModel] = useState('');
  const [paramsText, setParamsText] = useState('');

  useEffect(() => {
    if (assignment) {
      setRole(assignment.role);
      setAgent(assignment.agent_id);
      setBackend(assignment.llm_backend);
      setModel(assignment.llm_model);
      setParamsText(
        assignment.params ? JSON.stringify(assignment.params, null, 2) : '',
      );
    } else {
      setRole('');
      setAgent('');
      setBackend('');
      setModel('');
      setParamsText('');
    }
  }, [assignment, nodeId]);

  if (!nodeId) {
    return <div data-testid="assign-empty">Sélectionnez un nœud</div>;
  }

  const handleSave = () => {
    let parsed: Record<string, unknown> | undefined;
    try {
      parsed = paramsText ? JSON.parse(paramsText) : undefined;
    } catch {
      parsed = undefined;
    }
    onSave({
      node_id: nodeId,
      role,
      agent_id: agent,
      llm_backend: backend,
      llm_model: model,
      params: parsed,
    });
  };

  return (
    <div>
      <h3>Assignation {nodeId}</h3>
      <label>
        Rôle
        <input
          aria-label="role"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        />
      </label>
      <label>
        Agent
        <input
          aria-label="agent"
          value={agent}
          onChange={(e) => setAgent(e.target.value)}
        />
      </label>
      <label>
        Backend
        <input
          aria-label="backend"
          value={backend}
          onChange={(e) => setBackend(e.target.value)}
        />
      </label>
      <label>
        Modèle
        <input
          aria-label="model"
          value={model}
          onChange={(e) => setModel(e.target.value)}
        />
      </label>
      <label>
        Params JSON
        <textarea
          aria-label="params"
          value={paramsText}
          onChange={(e) => setParamsText(e.target.value)}
        />
      </label>
      <button onClick={handleSave} disabled={saving}>
        Save Assignments
      </button>
      {success && <div role="status">{success}</div>}
      {error && <div role="alert">{error}</div>}
    </div>
  );
};

export default AssignPanel;
