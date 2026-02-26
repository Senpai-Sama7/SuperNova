/**
 * MemorySpace3D Demo - Interactive Showcase
 * 
 * Demonstrates the 3D memory visualization with sample data
 * and interactive controls.
 * 
 * @phase Phase 4 - 3D Memory Space
 */

import React, { useState, useMemo, useCallback } from 'react';
import { MemorySpace3D, MemoryNode } from './MemorySpace3D';

/** Generate sample memory constellation */
const generateSampleMemories = (): MemoryNode[] => {
  const memories: MemoryNode[] = [];
  const types: Array<'episodic' | 'semantic' | 'procedural'> = ['episodic', 'semantic', 'procedural'];
  
  // Create 50 sample memories in a spherical distribution
  for (let i = 0; i < 50; i++) {
    const type = types[i % 3] as 'episodic' | 'semantic' | 'procedural';
    const angle = (i / 50) * Math.PI * 2;
    const height = (Math.random() - 0.5) * 8;
    const radius = 3 + Math.random() * 4;
    
    memories.push({
      id: `memory-${i}`,
      position: [
        Math.cos(angle) * radius + (Math.random() - 0.5),
        height + (Math.random() - 0.5) * 2,
        Math.sin(angle) * radius + (Math.random() - 0.5)
      ],
      type,
      strength: 0.3 + Math.random() * 0.7,
      label: `${type.charAt(0).toUpperCase() + type.slice(1)} Memory ${i + 1}`,
      content: `Sample ${type} memory content for demonstration`,
      timestamp: Date.now() - Math.random() * 86400000 * 30,
      relatedIds: []
    });
  }
  
  // Create connections between nearby memories
  memories.forEach((memory, i) => {
    const related: string[] = [];
    memories.forEach((other, j) => {
      if (i !== j && other.type === memory.type) {
        const dist = Math.sqrt(
          Math.pow(memory.position[0] - other.position[0], 2) +
          Math.pow(memory.position[1] - other.position[1], 2) +
          Math.pow(memory.position[2] - other.position[2], 2)
        );
        if (dist < 3 && related.length < 3) {
          related.push(other.id);
        }
      }
    });
    memory.relatedIds = related;
  });
  
  return memories;
};

/** Demo component with controls */
export const MemorySpace3DDemo: React.FC = () => {
  const [memories, setMemories] = useState<MemoryNode[]>(generateSampleMemories());
  const [selectedNode, setSelectedNode] = useState<MemoryNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<MemoryNode | null>(null);
  const [nodeCount, setNodeCount] = useState(50);
  
  // Regenerate memories with different count
  const regenerateMemories = useCallback((count: number) => {
    const newMemories: MemoryNode[] = [];
    const types: Array<'episodic' | 'semantic' | 'procedural'> = ['episodic', 'semantic', 'procedural'];
    
    for (let i = 0; i < count; i++) {
      const type = types[i % 3] as 'episodic' | 'semantic' | 'procedural';
      const angle = (i / count) * Math.PI * 2;
      const height = (Math.random() - 0.5) * 8;
      const radius = 3 + Math.random() * 4;
      
      newMemories.push({
        id: `memory-${i}`,
        position: [
          Math.cos(angle) * radius + (Math.random() - 0.5),
          height + (Math.random() - 0.5) * 2,
          Math.sin(angle) * radius + (Math.random() - 0.5)
        ],
        type,
        strength: 0.3 + Math.random() * 0.7,
        label: `${type.charAt(0).toUpperCase() + type.slice(1)} Memory ${i + 1}`,
        content: `Sample ${type} memory content`,
        timestamp: Date.now() - Math.random() * 86400000 * 30,
        relatedIds: []
      });
    }
    
    // Create connections
    newMemories.forEach((memory, i) => {
      const related: string[] = [];
      newMemories.forEach((other, j) => {
        if (i !== j && other.type === memory.type) {
          const dist = Math.sqrt(
            Math.pow(memory.position[0] - other.position[0], 2) +
            Math.pow(memory.position[1] - other.position[1], 2) +
            Math.pow(memory.position[2] - other.position[2], 2)
          );
          if (dist < 3 && related.length < 3) {
            related.push(other.id);
          }
        }
      });
      memory.relatedIds = related;
    });
    
    setMemories(newMemories);
    setSelectedNode(null);
  }, []);
  
  // Stats
  const stats = useMemo(() => {
    const episodic = memories.filter(m => m.type === 'episodic').length;
    const semantic = memories.filter(m => m.type === 'semantic').length;
    const procedural = memories.filter(m => m.type === 'procedural').length;
    const connections = memories.reduce((acc, m) => acc + (m.relatedIds?.length || 0), 0);
    
    return { episodic, semantic, procedural, connections };
  }, [memories]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      background: '#0a0a0f'
    }}>
      {/* Header */}
      <div style={{
        padding: '1rem 2rem',
        borderBottom: '1px solid rgba(0, 255, 213, 0.2)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'rgba(26, 26, 46, 0.5)'
      }}>
        <div>
          <h1 style={{
            margin: 0,
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '1.25rem',
            color: '#00ffd5',
            textTransform: 'uppercase',
            letterSpacing: '0.1em'
          }}>
            Neural Constellation
          </h1>
          <p style={{
            margin: '0.25rem 0 0',
            fontSize: '0.75rem',
            color: 'rgba(255, 255, 255, 0.5)'
          }}>
            3D Memory Space Visualization
          </p>
        </div>
        
        {/* Controls */}
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <label style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.875rem' }}>
            Nodes: {nodeCount}
          </label>
          <input
            type="range"
            min="10"
            max="100"
            value={nodeCount}
            onChange={(e) => {
              const count = parseInt(e.target.value);
              setNodeCount(count);
              regenerateMemories(count);
            }}
            style={{ width: '150px' }}
          />
          <button
            onClick={() => regenerateMemories(nodeCount)}
            style={{
              padding: '0.5rem 1rem',
              background: 'rgba(0, 255, 213, 0.2)',
              border: '1px solid #00ffd5',
              borderRadius: '6px',
              color: '#00ffd5',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '0.75rem',
              cursor: 'pointer',
              textTransform: 'uppercase'
            }}
          >
            Regenerate
          </button>
        </div>
      </div>
      
      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* 3D Viewport */}
        <div style={{ flex: 1, position: 'relative' }}>
          <MemorySpace3D
            memories={memories}
            onNodeClick={setSelectedNode}
            onNodeHover={setHoveredNode}
            selectedNodeId={selectedNode?.id}
          />
          
          {/* Legend */}
          <div style={{
            position: 'absolute',
            bottom: '1rem',
            left: '1rem',
            padding: '1rem',
            background: 'rgba(26, 26, 46, 0.9)',
            border: '1px solid rgba(0, 255, 213, 0.2)',
            borderRadius: '8px',
            backdropFilter: 'blur(10px)'
          }}>
            <div style={{ 
              fontSize: '0.75rem', 
              color: '#00ffd5',
              marginBottom: '0.5rem',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              Memory Types
            </div>
            {[
              { type: 'episodic', color: '#f472b6', shape: '◆', label: 'Episodic' },
              { type: 'semantic', color: '#fbbf24', shape: '⬡', label: 'Semantic' },
              { type: 'procedural', color: '#f59e0b', shape: '■', label: 'Procedural' }
            ].map(item => (
              <div key={item.type} style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                marginBottom: '0.25rem',
                fontSize: '0.75rem',
                color: 'rgba(255, 255, 255, 0.8)'
              }}>
                <span style={{ color: item.color, fontSize: '0.875rem' }}>{item.shape}</span>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
          
          {/* Instructions */}
          <div style={{
            position: 'absolute',
            bottom: '1rem',
            right: '1rem',
            padding: '0.75rem 1rem',
            background: 'rgba(26, 26, 46, 0.9)',
            border: '1px solid rgba(0, 255, 213, 0.2)',
            borderRadius: '8px',
            backdropFilter: 'blur(10px)',
            fontSize: '0.75rem',
            color: 'rgba(255, 255, 255, 0.6)'
          }}>
            <div>🖱️ Drag to rotate</div>
            <div>📜 Scroll to zoom</div>
            <div>👆 Click nodes</div>
          </div>
        </div>
        
        {/* Sidebar */}
        <div style={{
          width: '300px',
          borderLeft: '1px solid rgba(0, 255, 213, 0.2)',
          background: 'rgba(26, 26, 46, 0.3)',
          padding: '1.5rem',
          overflow: 'auto'
        }}>
          {/* Stats */}
          <div style={{ marginBottom: '2rem' }}>
            <h3 style={{
              fontSize: '0.75rem',
              color: '#00ffd5',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: '1rem'
            }}>
              Constellation Stats
            </h3>
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              {[
                { label: 'Total Memories', value: memories.length, color: '#fff' },
                { label: 'Episodic', value: stats.episodic, color: '#f472b6' },
                { label: 'Semantic', value: stats.semantic, color: '#fbbf24' },
                { label: 'Procedural', value: stats.procedural, color: '#f59e0b' },
                { label: 'Connections', value: stats.connections, color: '#00ffd5' }
              ].map(stat => (
                <div key={stat.label} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.5rem 0.75rem',
                  background: 'rgba(0, 0, 0, 0.2)',
                  borderRadius: '6px'
                }}>
                  <span style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.6)' }}>
                    {stat.label}
                  </span>
                  <span style={{ 
                    fontSize: '0.875rem', 
                    fontWeight: 600,
                    color: stat.color,
                    fontFamily: 'JetBrains Mono, monospace'
                  }}>
                    {stat.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Selected Node Info */}
          {selectedNode && (
            <div style={{
              padding: '1rem',
              background: 'rgba(0, 255, 213, 0.05)',
              border: '1px solid rgba(0, 255, 213, 0.2)',
              borderRadius: '8px'
            }}>
              <h3 style={{
                fontSize: '0.75rem',
                color: '#00ffd5',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                marginBottom: '0.75rem'
              }}>
                Selected Memory
              </h3>
              <div style={{ marginBottom: '0.5rem' }}>
                <span style={{ 
                  fontSize: '0.625rem', 
                  textTransform: 'uppercase',
                  color: MEMORY_VISUALS[selectedNode.type].color
                }}>
                  {selectedNode.type}
                </span>
              </div>
              <h4 style={{
                fontSize: '0.875rem',
                color: '#fff',
                marginBottom: '0.5rem'
              }}>
                {selectedNode.label}
              </h4>
              <p style={{
                fontSize: '0.75rem',
                color: 'rgba(255, 255, 255, 0.6)',
                lineHeight: 1.5
              }}>
                {selectedNode.content}
              </p>
              <div style={{
                marginTop: '0.75rem',
                fontSize: '0.625rem',
                color: 'rgba(255, 255, 255, 0.4)'
              }}>
                Strength: {Math.round(selectedNode.strength * 100)}%
              </div>
            </div>
          )}
          
          {/* Hovered Node */}
          {hoveredNode && !selectedNode && (
            <div style={{
              padding: '0.75rem 1rem',
              background: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '8px',
              fontSize: '0.75rem',
              color: 'rgba(255, 255, 255, 0.7)'
            }}>
              Hovering: <span style={{ color: '#fff' }}>{hoveredNode.label}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Memory type visuals for sidebar
const MEMORY_VISUALS = {
  episodic: { color: '#f472b6' },
  semantic: { color: '#fbbf24' },
  procedural: { color: '#f59e0b' }
} as const;

export default MemorySpace3DDemo;
