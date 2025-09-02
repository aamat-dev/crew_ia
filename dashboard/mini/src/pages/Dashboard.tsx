import type { JSX } from 'react';
import { useAgents, useRuns } from '../lib/hooks';

const Dashboard = (): JSX.Element => {
  const agents = useAgents();
  const runs = useRuns();

  if (agents.isLoading || runs.isLoading) {
    return <p>Chargement...</p>;
  }

  if (agents.isError || runs.isError) {
    return <p>Erreur de chargement.</p>;
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Agents: {agents.data?.length ?? 0}</p>
      <p>Runs: {runs.data?.length ?? 0}</p>
    </div>
  );
};

export default Dashboard;
