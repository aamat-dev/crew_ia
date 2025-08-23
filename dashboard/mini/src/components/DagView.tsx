import type { ComponentType, JSX } from 'react';
import { useEffect, useState } from 'react';
import type { RunDetail } from '../api/types';

interface DagViewProps {
  dag?: RunDetail['dag'];
}

interface ReactFlowModule {
  default: ComponentType<unknown>;
}

const DagView = ({ dag }: DagViewProps): JSX.Element | null => {
  const [rf, setRf] = useState<ReactFlowModule | null>(null);

  useEffect(() => {
    const pkg = 'reactflow';
    import(/* @vite-ignore */ pkg)
      .then((mod: ReactFlowModule) => setRf(mod))
      .catch(() => {
        /* ignore, fallback */
      });
  }, []);

  if (!dag) return null;

  if (rf) {
    const ReactFlow = rf.default as ComponentType<Record<string, unknown>>;
    const nodes = dag.nodes.map((n, idx) => ({
      id: n.id,
      position: { x: idx * 200, y: 0 },
      data: { label: `${n.role ?? n.id} (${n.status})` },
    }));
    const edges = dag.edges.map((e) => ({
      id: `${e.from}-${e.to}`,
      source: e.from,
      target: e.to,
    }));
    return (
      <div style={{ width: '100%', height: 200 }} data-testid="dag-reactflow">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag
          zoomOnScroll
          fitView
        />
      </div>
    );
  }

  const width = dag.nodes.length * 120 + 40;
  const height = 120;
  return (
    <svg
      width={width}
      height={height}
      data-testid="dag-fallback"
      style={{ border: '1px solid #ccc' }}
    >
      {dag.edges.map((e, idx) => {
        const fromIndex = dag.nodes.findIndex((n) => n.id === e.from);
        const toIndex = dag.nodes.findIndex((n) => n.id === e.to);
        const x1 = 60 + fromIndex * 120;
        const x2 = 60 + toIndex * 120;
        return (
          <line
            key={idx}
            x1={x1}
            y1={60}
            x2={x2}
            y2={60}
            stroke="black"
            markerEnd="url(#arrow)"
            data-testid={`dag-edge-${e.from}-${e.to}`}
          />
        );
      })}
      <defs>
        <marker
          id="arrow"
          markerWidth="10"
          markerHeight="10"
          refX="10"
          refY="3"
          orient="auto"
        >
          <path d="M0,0 L0,6 L9,3 z" fill="black" />
        </marker>
      </defs>
      {dag.nodes.map((n, idx) => (
        <g
          key={n.id}
          transform={`translate(${40 + idx * 120},40)`}
          data-testid={`dag-node-${n.id}`}
        >
          <rect width="80" height="40" fill="#eee" stroke="#333" rx="4" />
          <text
            x="40"
            y="18"
            dominantBaseline="middle"
            textAnchor="middle"
            fontSize="10"
          >
            {n.role ?? n.id}
          </text>
          <text
            x="40"
            y="32"
            dominantBaseline="middle"
            textAnchor="middle"
            fontSize="8"
          >
            {n.status}
          </text>
        </g>
      ))}
    </svg>
  );
};

export default DagView;
