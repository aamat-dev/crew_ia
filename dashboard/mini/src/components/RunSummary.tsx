import type { JSX } from 'react';
import type { Run, RunSummary as RunSummaryType } from '../api/types';

interface RunSummaryProps {
  run: Run;
  summary?: RunSummaryType;
}

const formatDate = (value?: string): string =>
  value ? new Date(value).toLocaleString() : '—';

const RunSummary = ({ run, summary }: RunSummaryProps): JSX.Element => {
  return (
    <div className="run-summary" data-testid="run-summary">
      <p>
        Statut:{' '}
        <span className={`badge status-${run.status}`}>{run.status}</span>
      </p>
      <p>Début: {formatDate(run.started_at)}</p>
      <p>Fin: {formatDate(run.ended_at)}</p>
      {summary && (
        <ul>
          {summary.duration_ms !== undefined && (
            <li>Durée: {Math.round(summary.duration_ms / 1000)}s</li>
          )}
          <li>
            Nœuds: {summary.nodes_completed}/{summary.nodes_total} (échecs:{' '}
            {summary.nodes_failed})
          </li>
          <li>Artifacts: {summary.artifacts_total}</li>
          <li>Événements: {summary.events_total}</li>
        </ul>
      )}
    </div>
  );
};

export default RunSummary;
