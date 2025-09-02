import type { JSX } from 'react';
import { useRuns, useFeedbacks, useRunAction } from '../lib/hooks';

const RunsTimeline = (): JSX.Element => {
  const runs = useRuns();
  const feedbacks = useFeedbacks();
  const runAction = useRunAction();

  if (runs.isLoading) return <p>Chargement...</p>;
  if (runs.isError) return <p>Erreur de chargement.</p>;

  return (
    <div>
      <h2>Runs</h2>
      <ul>
        {runs.data?.map((r) => (
          <li key={r.id}>
            {r.title ?? r.id} - {r.status}
            <button
              onClick={() => runAction.mutate({ id: r.id, action: 'pause' })}
            >
              Pause
            </button>
          </li>
        ))}
      </ul>
      <p>Feedbacks: {feedbacks.data?.length ?? 0}</p>
    </div>
  );
};

export default RunsTimeline;
