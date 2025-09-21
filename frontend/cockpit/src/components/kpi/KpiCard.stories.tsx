import { KpiCard } from './KpiCard';

const meta = {
  title: 'Components/KpiCard',
  component: KpiCard,
  tags: ['autodocs'],
  argTypes: {
    title: { control: 'text' },
    value: { control: 'text' },
  },
  parameters: {
    docs: {
      description: {
        component: 'Carte KPI avec rôle "group" décrivant un indicateur et sa valeur.',
      },
    },
  },
};

export default meta;

export const Exemple = {
  args: {
    title: 'Requêtes',
    value: '42',
  },
};
