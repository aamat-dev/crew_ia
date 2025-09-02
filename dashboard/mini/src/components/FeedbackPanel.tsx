import type { JSX } from 'react';
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listFeedbacks, createFeedback } from '../api/feedbacks';
import { patchNode } from '../api/client';
import type { Feedback } from '../api/types';
import { ApiError } from '../api/http';

interface Props {
  runId: string;
  nodeId: string;
}

const FeedbackPanel = ({ runId, nodeId }: Props): JSX.Element => {
  const [filter, setFilter] = useState<'all' | 'auto' | 'human'>('all');
  const [score, setScore] = useState('');
  const [comment, setComment] = useState('');
  const [reviewer, setReviewer] = useState('');
  const [requestId, setRequestId] = useState<string | undefined>();
  const qc = useQueryClient();

  const query = useQuery({
    queryKey: ['feedbacks', runId, nodeId],
    queryFn: ({ signal }) => listFeedbacks({ run_id: runId, node_id: nodeId }, { signal }),
  });

  const mutation = useMutation({
    mutationFn: (payload: Omit<Feedback, 'id' | 'created_at' | 'updated_at'>) =>
      createFeedback(payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['feedbacks', runId, nodeId] });
      setScore('');
      setComment('');
      setReviewer('');
    },
  });

  const doAction = async (body: Record<string, unknown>) => {
    if (!window.confirm('Confirmer ?')) return;
    try {
      const { requestId } = await patchNode(nodeId, body);
      setRequestId(requestId);
    } catch (err) {
      if (err instanceof ApiError) {
        alert(`Erreur ${err.status}`);
        setRequestId(err.requestId);
      } else if (err instanceof Error) {
        alert(err.message);
      }
    }
  };

  const items =
    query.data?.items.filter(
      (f) => filter === 'all' || f.source === filter,
    ) ?? [];

  const onSubmit = () => {
    mutation.mutate({
      run_id: runId,
      node_id: nodeId,
      source: 'human',
      reviewer: reviewer || undefined,
      score: Number(score),
      comment,
    });
  };

  return (
    <aside style={{ borderLeft: '1px solid #ccc', padding: 16, width: 320 }} data-testid="feedback-panel">
      <h4>Feedbacks</h4>
      <div>
        <button onClick={() => setFilter('all')} aria-pressed={filter === 'all'}>Tous</button>
        <button onClick={() => setFilter('auto')} aria-pressed={filter === 'auto'}>Auto</button>
        <button onClick={() => setFilter('human')} aria-pressed={filter === 'human'}>Humain</button>
      </div>
      <ul>
        {items.map((f) => (
          <li key={f.id}>
            <span>{new Date(f.created_at).toLocaleString()} — </span>
            <span>{f.source}</span> — <strong>{f.score}</strong> — {f.comment}
            {f.reviewer && <em> ({f.reviewer})</em>}
          </li>
        ))}
        {items.length === 0 && <li>Aucun feedback</li>}
      </ul>
      <div>
        <h5>Ajouter un feedback</h5>
        <input
          placeholder="reviewer"
          value={reviewer}
          onChange={(e) => setReviewer(e.target.value)}
        />
        <input
          placeholder="score"
          type="number"
          value={score}
          onChange={(e) => setScore(e.target.value)}
        />
        <textarea
          placeholder="commentaire"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
        <button onClick={onSubmit} disabled={mutation.isLoading}>Envoyer</button>
      </div>
      <div style={{ marginTop: 8 }}>
        <button onClick={() => void doAction({ action: 'resume' })}>Re-run guidé</button>
        <button onClick={() => void doAction({ action: 'override' })}>Override</button>
        <button onClick={() => void doAction({ action: 'pause' })}>Pause</button>
        <button onClick={() => void doAction({ action: 'resume' })}>Resume</button>
      </div>
      {requestId && <p>Request ID: {requestId}</p>}
    </aside>
  );
};

export default FeedbackPanel;
