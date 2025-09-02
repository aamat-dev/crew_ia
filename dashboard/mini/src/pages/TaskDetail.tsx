import type { JSX } from 'react';
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useTask, useGenerateTaskPlan } from '../api/hooks';
import { useApiKey } from '../state/ApiKeyContext';
import { ApiError } from '../api/http';
import { useToast } from '../components/ToastProvider';
import type { Plan } from '../api/types';

const TaskDetailPage = (): JSX.Element => {
  const { apiKey, useEnvKey } = useApiKey();
  const hasKey = Boolean(apiKey) || useEnvKey;
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const taskQuery = useTask(id ?? '', { enabled: hasKey && Boolean(id) });
  const genMutation = useGenerateTaskPlan(id ?? '');
  const toast = useToast();
  const [plan, setPlan] = useState<Plan | undefined>(undefined);

  useEffect(() => {
    setPlan(taskQuery.data?.plan);
  }, [taskQuery.data?.plan]);

  const retry = (): void => {
    queryClient.invalidateQueries({ queryKey: ['task', id] });
  };

  const generate = async (): Promise<void> => {
    try {
      const res = await genMutation.mutateAsync();
      setPlan(res);
      if (res.status === 'ready') {
        toast('Plan généré', 'success');
      } else if (res.status === 'invalid') {
        toast('Plan invalide', 'error');
      }
    } catch {
      toast('Erreur de génération', 'error');
    }
  };

  if (!hasKey) {
    return <div>Veuillez saisir une clé API pour continuer.</div>;
  }

  if (taskQuery.isLoading) {
    return <div className="skeleton">Chargement...</div>;
  }

  if (taskQuery.isError) {
    const err = taskQuery.error as unknown;
    return (
      <div>
        <p>Une erreur est survenue.</p>
        {err instanceof ApiError && <p>Request ID: {err.requestId}</p>}
        <button onClick={retry}>Réessayer</button>
      </div>
    );
  }

  const task = taskQuery.data;
  if (!task) {
    return <p>Aucune donnée.</p>;
  }

  return (
    <div>
      <h2>{task.title}</h2>
      <p>Statut: {task.status}</p>
      {plan && (
        <div>
          <p>Plan: {plan.status}</p>
          {plan.errors && (
            <ul>
              {plan.errors.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          )}
        </div>
      )}
      <button onClick={generate} disabled={genMutation.isPending}>
        Générer le plan
      </button>
    </div>
  );
};

export default TaskDetailPage;
