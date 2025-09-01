import type { JSX } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApiKey } from '../state/ApiKeyContext';
import TasksTable from '../components/TasksTable';
import TaskFormModal from '../components/TaskFormModal';

const TasksPage = (): JSX.Element => {
  const { apiKey, useEnvKey } = useApiKey();
  const hasKey = Boolean(apiKey) || useEnvKey;
  const navigate = useNavigate();

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [orderBy, setOrderBy] = useState<'created_at' | 'title' | 'status'>('created_at');
  const [orderDir, setOrderDir] = useState<'asc' | 'desc'>('desc');
  const [showModal, setShowModal] = useState(false);

  const onOpenTask = (id: string): void => {
    navigate(`/tasks/${id}`);
  };

  if (!hasKey) {
    return <div>Veuillez saisir une clé API pour continuer.</div>;
  }

  return (
    <div>
      <button onClick={() => setShowModal(true)}>Nouvelle tâche</button>
      <TasksTable
        page={page}
        pageSize={pageSize}
        orderBy={orderBy}
        orderDir={orderDir}
        onPageChange={setPage}
        onPageSizeChange={(s) => {
          setPageSize(s);
          setPage(1);
        }}
        onOrderByChange={(f) => {
          setOrderBy(f);
          setPage(1);
        }}
        onOrderDirChange={(d) => {
          setOrderDir(d);
          setPage(1);
        }}
        onOpenTask={onOpenTask}
      />
      {showModal && <TaskFormModal onClose={() => setShowModal(false)} />}
    </div>
  );
};

export default TasksPage;
