import type { ComponentType } from 'react';
import { useEffect, useState } from 'react';

interface PlanGraphProps {
  graph?: {
    nodes: Array<{ id: string; role?: string }>;
    edges: Array<{ from: string; to: string }>;
  };
  selected?: string | null;
  onSelect?: (id: string) => void;
}

interface ReactFlowModule {
  default: ComponentType<unknown>;
}

const PlanGraph = ({ graph, selected, onSelect }: PlanGraphProps) => {
  const [rf, setRf] = useState<ReactFlowModule | null>(null);

  useEffect(() => {
    const pkg = 'reactflow';
    import(/* @vite-ignore */ pkg)
      .then((mod: ReactFlowModule) => setRf(mod))
      .catch(() => {
        /* ignore, fallback */
      });
  }, []);

  if (!graph) return null;

  if (rf) {
    const ReactFlow = rf.default as ComponentType<Record<string, unknown>>;
    const nodes = graph.nodes.map((n, idx) => ({
      id: n.id,
      position: { x: idx * 200, y: 0 },
      data: { label: n.role ?? n.id },
      style: selected === n.id ? { border: '2px solid blue' } : undefined,
    }));
    const edges = graph.edges.map((e) => ({
      id: `${e.from}-${e.to}`,
      source: e.from,
      target: e.to,
    }));
    return (
      <div style={{ width: '100%', height: 200 }} data-testid="plan-reactflow">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={(_: unknown, node: { id: string }) => onSelect?.(node.id)}
        />
      </div>
    );
  }

  return (
    <ul data-testid="plan-fallback">
      {graph.nodes.map((n) => (
        <li key={n.id}>
          <button data-testid={`plan-node-${n.id}`} onClick={() => onSelect?.(n.id)}>
            {n.role ?? n.id}
          </button>
        </li>
      ))}
    </ul>
  );
};

export default PlanGraph;
