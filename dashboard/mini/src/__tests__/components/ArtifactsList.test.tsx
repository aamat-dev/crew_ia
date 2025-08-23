import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import type { Mock } from 'vitest';
import ArtifactsList, {
  ArtifactsListProps,
} from '../../components/ArtifactsList';
import { ApiError } from '../../api/http';

vi.mock('../../api/hooks', () => ({
  useNodeArtifacts: vi.fn(),
}));
import { useNodeArtifacts } from '../../api/hooks';

const setup = (props: Partial<ArtifactsListProps> = {}) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const defaultProps: ArtifactsListProps = {
    runId: 'r1',
    nodeId: 'n1',
  };
  const view = render(
    <QueryClientProvider client={queryClient}>
      <ArtifactsList {...defaultProps} {...props} />
    </QueryClientProvider>,
  );
  return { ...view, queryClient };
};

describe('ArtifactsList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('affiche les artefacts', () => {
    (useNodeArtifacts as unknown as Mock).mockReturnValue({
      data: {
        items: [
          {
            id: 'a1',
            node_id: 'n1',
            name: 'f1',
            kind: 'file',
            size_bytes: 2048,
            url: 'http://example.com',
          },
        ],
        meta: { page: 1, page_size: 50, total: 1 },
      },
      isLoading: false,
      isError: false,
    });
    setup();
    expect(screen.getByText('f1')).toBeInTheDocument();
    expect(screen.getByText('file')).toBeInTheDocument();
  });

  it("affiche l'état loading", () => {
    (useNodeArtifacts as unknown as Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });
    setup();
    expect(screen.getAllByText('Chargement...').length).toBeGreaterThan(0);
  });

  it("affiche l'état vide", () => {
    (useNodeArtifacts as unknown as Mock).mockReturnValue({
      data: { items: [], meta: { page: 1, page_size: 50, total: 0 } },
      isLoading: false,
      isError: false,
    });
    setup();
    expect(screen.getByText('Aucun artefact.')).toBeInTheDocument();
  });

  it("affiche le message lorsqu'aucun nœud n'est sélectionné", () => {
    (useNodeArtifacts as unknown as Mock).mockReturnValue({
      data: { items: [], meta: { page: 1, page_size: 50, total: 0 } },
      isLoading: false,
      isError: false,
    });
    setup({ nodeId: undefined });
    expect(screen.getByText('Aucun nœud sélectionné.')).toBeInTheDocument();
  });

  it("affiche l'erreur et relance sur retry", () => {
    (useNodeArtifacts as unknown as Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new ApiError('boom', 500, 'req-1'),
    });
    const { queryClient } = setup();
    const spy = vi.spyOn(queryClient, 'invalidateQueries');
    fireEvent.click(screen.getByText('Réessayer'));
    expect(spy).toHaveBeenCalled();
    expect(screen.getByText('Request ID: req-1')).toBeInTheDocument();
  });
});
