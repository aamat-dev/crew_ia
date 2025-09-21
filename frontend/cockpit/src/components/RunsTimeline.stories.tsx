import { RunsTimeline } from './RunsTimeline';

const meta = {
  title: 'Components/RunsTimeline',
  component: RunsTimeline,
  tags: ['autodocs'],
  argTypes: {
    events: { control: 'object' },
  },
  parameters: {
    docs: {
      description: {
        component: "Timeline des exécutions utilisant les rôles 'list' et 'listitem'.",
      },
    },
  },
};

export default meta;

export const Exemple = {
  args: {
    events: [
      { id: '1', status: 'Démarré', timestamp: '2024-01-01T10:00:00Z' },
      { id: '2', status: 'En cours', timestamp: '2024-01-01T10:05:00Z' },
      { id: '3', status: 'Terminé', timestamp: '2024-01-01T10:10:00Z' },
    ],
  },
};
