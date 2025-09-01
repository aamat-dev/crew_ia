import type { JSX } from 'react';
import { useState } from 'react';
import { useCreateTask } from '../api/hooks';
import { useToast } from './ToastProvider';

export const TaskFormModal = ({ onClose }: { onClose: () => void }): JSX.Element => {
  const [title, setTitle] = useState('');
  const createTask = useCreateTask();
  const toast = useToast();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTask.mutateAsync({ title });
      toast('Tâche créée', 'success');
      onClose();
    } catch {
      toast("Erreur lors de la création", 'error');
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0,0,0,0.3)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <form onSubmit={submit} style={{ background: '#fff', padding: '16px' }}>
        <h3>Nouvelle tâche</h3>
        <label>
          Titre
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Titre"
          />
        </label>
        <div style={{ marginTop: '8px' }}>
          <button type="submit">Créer</button>
          <button type="button" onClick={onClose} style={{ marginLeft: '8px' }}>
            Annuler
          </button>
        </div>
      </form>
    </div>
  );
};

export default TaskFormModal;
