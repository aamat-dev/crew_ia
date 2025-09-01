import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import PlanGraph from '../components/PlanGraph';
import AssignPanel from '../components/AssignPanel';
import { getPlan, saveAssignments, setPlanStatus } from '../api/client';
import type { Assignment, Plan } from '../api/types';
import { ApiError } from '../api/http';

const PlanEditor = () => {
  const { id } = useParams<{ id: string }>();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [assignments, setAssignments] = useState<Record<string, Assignment>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      getPlan(id)
        .then((p) => {
          setPlan(p);
          const map: Record<string, Assignment> = {};
          p.assignments?.forEach((a) => {
            map[a.node_id] = a;
          });
          setAssignments(map);
        })
        .catch(() => {
          /* ignore */
        });
    }
  }, [id]);

  const handleSave = async (a: Assignment) => {
    if (!id) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await saveAssignments(id, [a]);
      const newMap = { ...assignments, [a.node_id]: a };
      setAssignments(newMap);
      setSuccess('Assignation sauvegardée');
      if (plan && plan.graph.nodes.every((n) => newMap[n.id])) {
        await setPlanStatus(id, 'ready');
        setPlan({ ...plan, status: 'ready' });
      }
    } catch (err) {
      if (err instanceof ApiError) {
        const body = err.body as { detail?: string; error?: string } | undefined;
        setError(body?.detail || body?.error || err.message);
      } else {
        setError((err as Error).message);
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <PlanGraph graph={plan?.graph} selected={selected} onSelect={setSelected} />
      <AssignPanel
        nodeId={selected}
        assignment={selected ? assignments[selected] : undefined}
        onSave={handleSave}
        saving={saving}
        error={error}
        success={success}
      />
    </div>
  );
};

export default PlanEditor;
