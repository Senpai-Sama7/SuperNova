/**
 * MemoryGraph Component
 * Network visualization of memory nodes and connections
 */
import { memo, useMemo, useCallback } from 'react';
import type { MemoryGraphProps } from '../../types';
import { Theme } from '../../theme';

const NODE_COLORS: Record<string, string> = {
  episodic: Theme.colors.accent,
  semantic: Theme.colors.secondary,
  procedural: Theme.colors.warning,
  working: Theme.colors.info,
};

export const MemoryGraph = memo<MemoryGraphProps>(function MemoryGraph({
  data,
  width = 300,
  height = 200,
  onNodeClick,
  selectedNodeId,
}) {
  const { nodes, edges } = data;

  // Calculate positions with simple force-directed layout
  const positions = useMemo(() => {
    const pos = new Map<string, { x: number; y: number }>();
    const padding = 30;
    const availableWidth = width - 2 * padding;
    const availableHeight = height - 2 * padding;

    // Simple circular layout for now
    nodes.forEach((node, index) => {
      if (node.x !== undefined && node.y !== undefined) {
        pos.set(node.id, { x: node.x, y: node.y });
      } else {
        const angle = (index / Math.max(nodes.length, 1)) * 2 * Math.PI;
        const r = Math.min(availableWidth, availableHeight) / 3;
        pos.set(node.id, {
          x: width / 2 + r * Math.cos(angle),
          y: height / 2 + r * Math.sin(angle),
        });
      }
    });

    return pos;
  }, [nodes, width, height]);

  const handleNodeClick = useCallback((nodeId: string) => {
    if (onNodeClick) {
      const node = nodes.find(n => n.id === nodeId);
      if (node) onNodeClick(node);
    }
  }, [nodes, onNodeClick]);

  if (!nodes.length) {
    return (
      <svg width={width} height={height} role="img" aria-label="No memory nodes">
        <text x={width / 2} y={height / 2} textAnchor="middle" fill={Theme.colors.textMuted} fontSize="12">
          No memory data
        </text>
      </svg>
    );
  }

  return (
    <svg width={width} height={height} role="img" aria-label={`Memory graph with ${nodes.length} nodes and ${edges.length} connections`}>
      {/* Edges */}
      <g aria-hidden="true">
        {edges.map((edge, index) => {
          const source = positions.get(edge.source);
          const target = positions.get(edge.target);
          if (!source || !target) return null;

          return (
            <line
              key={`${edge.source}-${edge.target}-${index}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke={Theme.colors.border}
              strokeWidth={1 + (edge.strength || 0.5) * 2}
              opacity={0.5}
            />
          );
        })}
      </g>

      {/* Nodes */}
      <g>
        {nodes.map((node) => {
          const pos = positions.get(node.id);
          if (!pos) return null;

          const isSelected = node.id === selectedNodeId;
          const radius = 6 + (node.strength || 0.5) * 6;
          const color = NODE_COLORS[node.type] || Theme.colors.textMuted;

          return (
            <g
              key={node.id}
              transform={`translate(${pos.x}, ${pos.y})`}
              role="button"
              tabIndex={0}
              aria-label={`${node.type} memory: ${node.label}`}
              onClick={() => handleNodeClick(node.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleNodeClick(node.id);
                }
              }}
              style={{ cursor: onNodeClick ? 'pointer' : 'default' }}
            >
              {/* Glow effect for selected */}
              {isSelected && (
                <circle
                  r={radius + 4}
                  fill={color}
                  opacity={0.3}
                />
              )}
              
              {/* Node circle */}
              <circle
                r={radius}
                fill={Theme.colors.surfaceLow}
                stroke={color}
                strokeWidth={isSelected ? 3 : 2}
              />

              {/* Label */}
              <text
                y={radius + 12}
                textAnchor="middle"
                fill={Theme.colors.textMuted}
                fontSize="8"
                style={{ pointerEvents: 'none' }}
              >
                {node.label.length > 12 ? `${node.label.slice(0, 12)}...` : node.label}
              </text>
            </g>
          );
        })}
      </g>

      {/* Legend */}
      <g transform={`translate(10, ${height - 50})`}>
        {Object.entries(NODE_COLORS).map(([type, color], index) => (
          <g key={type} transform={`translate(0, ${index * 12})`}>
            <circle r={3} fill={color} />
            <text x={8} y={3} fill={Theme.colors.textMuted} fontSize="8">
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </text>
          </g>
        ))}
      </g>
    </svg>
  );
});

export default MemoryGraph;
