/**
 * OrchestrationGraph Component
 * Multi-agent workflow visualization
 */
import { memo, useMemo, useCallback } from 'react';
import type { OrchestrationGraphProps } from '../../types';
import { Theme } from '../../theme';

const NODE_SHAPES: Record<string, string> = {
  agent: 'circle',
  gateway: 'diamond',
  aggregator: 'square',
  router: 'hexagon',
};

const STATUS_COLORS: Record<string, string> = {
  active: Theme.colors.accent,
  pending: Theme.colors.warning,
  completed: Theme.colors.success,
  failed: Theme.colors.error,
};

export const OrchestrationGraph = memo<OrchestrationGraphProps>(function OrchestrationGraph({
  data,
  width = 400,
  height = 250,
  onNodeClick,
}) {
  const { nodes, edges, strategy } = data;

  const positions = useMemo(() => {
    const pos = new Map<string, { x: number; y: number }>();
    
    nodes.forEach((node) => {
      // Use provided positions or fallback to simple grid
      const x = node.x ?? Math.random() * (width - 60) + 30;
      const y = node.y ?? Math.random() * (height - 60) + 30;
      pos.set(node.id, { x, y });
    });

    return pos;
  }, [nodes, width, height]);

  const handleNodeClick = useCallback((nodeId: string) => {
    if (onNodeClick) {
      const node = nodes.find(n => n.id === nodeId);
      if (node) onNodeClick(node);
    }
  }, [nodes, onNodeClick]);

  const renderNodeShape = (node: typeof nodes[0], pos: { x: number; y: number }) => {
    const color = STATUS_COLORS[node.status] || Theme.colors.textMuted;
    const size = 16;

    switch (NODE_SHAPES[node.type]) {
      case 'circle':
        return (
          <circle
            cx={pos.x}
            cy={pos.y}
            r={size}
            fill={Theme.colors.surfaceLow}
            stroke={color}
            strokeWidth={2}
          />
        );
      case 'diamond':
        return (
          <polygon
            points={`${pos.x},${pos.y - size} ${pos.x + size},${pos.y} ${pos.x},${pos.y + size} ${pos.x - size},${pos.y}`}
            fill={Theme.colors.surfaceLow}
            stroke={color}
            strokeWidth={2}
          />
        );
      case 'square':
        return (
          <rect
            x={pos.x - size}
            y={pos.y - size}
            width={size * 2}
            height={size * 2}
            fill={Theme.colors.surfaceLow}
            stroke={color}
            strokeWidth={2}
          />
        );
      case 'hexagon':
        const hexPoints = [];
        for (let i = 0; i < 6; i++) {
          const angle = (i * 60 - 30) * (Math.PI / 180);
          hexPoints.push(`${pos.x + size * Math.cos(angle)},${pos.y + size * Math.sin(angle)}`);
        }
        return (
          <polygon
            points={hexPoints.join(' ')}
            fill={Theme.colors.surfaceLow}
            stroke={color}
            strokeWidth={2}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div role="region" aria-label={`Orchestration graph: ${strategy} strategy with ${nodes.length} nodes`}>
      <svg width={width} height={height}>
        {/* Strategy label */}
        <text
          x={width - 10}
          y={20}
          textAnchor="end"
          fill={Theme.colors.textMuted}
          fontSize="10"
          fontWeight={600}
          style={{ textTransform: 'uppercase' }}
        >
          {strategy}
        </text>

        {/* Edges */}
        <g aria-hidden="true">
          {edges.map((edge, index) => {
            const source = positions.get(edge.source);
            const target = positions.get(edge.target);
            if (!source || !target) return null;

            const isActive = edge.status === 'active';

            return (
              <g key={`${edge.source}-${edge.target}-${index}`}>
                <line
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={isActive ? Theme.colors.accent : Theme.colors.border}
                  strokeWidth={isActive ? 2 : 1}
                  strokeDasharray={edge.status === 'pending' ? '4 2' : undefined}
                  opacity={isActive ? 1 : 0.5}
                />
                {edge.label && (
                  <text
                    x={(source.x + target.x) / 2}
                    y={(source.y + target.y) / 2 - 5}
                    textAnchor="middle"
                    fill={Theme.colors.textMuted}
                    fontSize="8"
                    style={{ pointerEvents: 'none' }}
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}
        </g>

        {/* Nodes */}
        <g>
          {nodes.map((node) => {
            const pos = positions.get(node.id);
            if (!pos) return null;

            return (
              <g
                key={node.id}
                role="button"
                tabIndex={0}
                aria-label={`${node.type}: ${node.label}, status ${node.status}`}
                onClick={() => handleNodeClick(node.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleNodeClick(node.id);
                  }
                }}
                style={{ cursor: onNodeClick ? 'pointer' : 'default' }}
              >
                {renderNodeShape(node, pos)}
                <text
                  x={pos.x}
                  y={pos.y + 28}
                  textAnchor="middle"
                  fill={Theme.colors.text}
                  fontSize="9"
                  style={{ pointerEvents: 'none' }}
                >
                  {node.label.length > 10 ? `${node.label.slice(0, 10)}...` : node.label}
                </text>
              </g>
            );
          })}
        </g>

        {/* Legend */}
        <g transform={`translate(10, ${height - 40})`}>
          {Object.entries(STATUS_COLORS).map(([status, color], index) => (
            <g key={status} transform={`translate(${index * 50}, 0)`}>
              <circle r={3} fill={color} />
              <text x={8} y={3} fill={Theme.colors.textMuted} fontSize="8">
                {status}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
});

export default OrchestrationGraph;
