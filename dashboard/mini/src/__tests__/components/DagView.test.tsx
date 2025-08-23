import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import DagView from '../../components/DagView';
import type { RunDetail } from '../../api/types';

describe('DagView', () => {
  it('rend les nodes et les edges à partir du dag', () => {
    const dag: NonNullable<RunDetail['dag']> = {
      nodes: [
        { id: 'n1', role: 'start', status: 'succeeded' },
        { id: 'n2', role: 'end', status: 'failed' },
      ],
      edges: [{ from: 'n1', to: 'n2' }],
    };
    render(<DagView dag={dag} />);
    expect(screen.getByTestId('dag-node-n1')).toBeInTheDocument();
    expect(screen.getByTestId('dag-node-n2')).toBeInTheDocument();
    expect(screen.getByTestId('dag-edge-n1-n2')).toBeInTheDocument();
  });
});
