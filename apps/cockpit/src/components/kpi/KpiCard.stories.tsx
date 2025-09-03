import type { Meta, StoryObj } from '@storybook/react';
import { KpiCard } from './KpiCard';

const meta: Meta<typeof KpiCard> = {
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

type Story = StoryObj<typeof KpiCard>;

export const Exemple: Story = {
  args: {
    title: 'Requêtes',
    value: '42',
  },
};
