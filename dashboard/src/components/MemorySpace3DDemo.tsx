/**
 * MemorySpace3D Demo - Interactive Showcase with Phase 5 Controls
 * 
 * Demonstrates the 3D memory visualization with:
 * - Sample data and interactive controls
 * - Real-time confidence/entropy adjustment
 * - Memory addition/removal animations
 * - State-responsive atmosphere controls
 * 
 * @phase Phase 5 - Adaptive Atmosphere
 */

import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { MemorySpace3D, MemoryNode, AgentState } from './MemorySpace3D';

/** Generate sample memory constellation */
const generateSampleMemories = (count: number): MemoryNode[] => {
  const memories: MemoryNode[] = [];
  const types: Array<'episodic' | 'semantic' | 'procedural'> = ['episodic', 'semantic', 'procedural'];
  
  // Create memories in a spherical distribution
  for (let i = 0; i < count; i++) {
    const type = types[i % 3] as 'episodic' | 'semantic' | 'procedural';
    const angle = (i / count) * Math.PI * 2;
    const height = (Math.random() - 0.5) * 8;
    const radius = 3 + Math.random() * 4;
    
    memories.push({
      id: `memory-${i}-${Date.now()}`,
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

/** Demo component with Phase 5 adaptive controls */
export const MemorySpace3DDemo: React.FC = () => {
  const [memories, setMemories] = useState<MemoryNode[]>(() => generateSampleMemories(50));
  const [selectedNode, setSelectedNode] = useState<MemoryNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<MemoryNode | null>(null);
  
  // Phase 5: Agent state for adaptive atmosphere
  const [agentState, setAgentState] = useState<AgentState>({
    confidence: 0.7,
    entropy: 0.2,
    cognitivePhase: 'PERCEIVE',
    agentStatus: 'active',
    activeMemoryIds: [],
    cognitiveState: 'stable'
  });
  
  // Phase 5: Visual settings
  const [showEntropyField, setShowEntropyField] = useState(true);
  const [enableAnimations, setEnableAnimations] = useState(true);
  
  // Node count control
  const [nodeCount, setNodeCount] = useState(50);
  
  // Auto-cycle through phases for demo
  const [autoCycle, setAutoCycle] = useState(false);
  const cycleIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const phases: AgentState['cognitivePhase'][] = ['PERCEIVE', 'REMEMBER', 'REASON', 'ACT', 'REFLECT', 'CONSOLIDATE'];
  
  useEffect(() => {
    if (autoCycle) {
      let phaseIndex = 0;
      cycleIntervalRef.current = setInterval(() => {
        phaseIndex = (phaseIndex + 1) % phases.length;
        setAgentState(prev => ({
          ...prev,
          cognitivePhase: phases[phaseIndex]
        }));
      }, 3000);
    } else {
      if (cycleIntervalRef.current) {
        clearInterval(cycleIntervalRef.current);
      }
    }
    
    return () => {
      if (cycleIntervalRef.current) {
        clearInterval(cycleIntervalRef.current);
      }
    };
  }, [autoCycle]);
  
  // Regenerate memories
  const regenerateMemories = useCallback((count: number) => {
    setMemories(generateSampleMemories(count));
    setSelectedNode(null);
  }, []);
  
  // Phase 5: Add a new memory with animation
  const addMemory = useCallback(() => {
    const types: Array<'episodic' | 'semantic' | 'procedural'> = ['episodic', 'semantic', 'procedural'];
    const type = types[Math.floor(Math.random() * 3)];
    const angle = Math.random() * Math.PI * 2;
    const height = (Math.random() - 0.5) * 8;
    const radius = 3 + Math.random() * 4;
    
    const newMemory: MemoryNode = {
      id: `memory-${Date.now()}`,
      position: [
        Math.cos(angle) * radius + (Math.random() - 0.5),
        height + (Math.random() - 0.5) * 2,
        Math.sin(angle) * radius + (Math.random() - 0.5)
      ],
      type,
      strength: 0.3 + Math.random() * 0.7,
      label: `New ${type} Memory`,
      content: `Dynamically added ${type} memory`,
      timestamp: Date.now(),
      relatedIds: []
    };
    
    setMemories(prev => [...prev, newMemory]);
    
    // Mark as active briefly
    setAgentState(prev => ({
      ...prev,
      activeMemoryIds: [...(prev.activeMemoryIds || []), newMemory.id]
    }));
    
    setTimeout(() => {
      setAgentState(prev => ({
        ...prev,
        activeMemoryIds: prev.activeMemoryIds?.filter(id => id !== newMemory.id) || []
      }));
    }, 2000);
  }, []);
  
  // Phase 5: Remove a memory with exit animation
  const removeMemory = useCallback(() => {
    if (memories.length === 0) return;
    const toRemove = memories[Math.floor(Math.random() * memories.length)];
    setMemories(prev => prev.filter(m => m.id !== toRemove.id));
  }, [memories]);
  
  // Phase 5: Simulate active processing on selected node
  useEffect(() => {
    if (selectedNode) {
      setAgentState(prev => ({
        ...prev,
        activeMemoryIds: [selectedNode.id]
      }));
    } else {
      setAgentState(prev => ({
        ...prev,
        activeMemoryIds: []
      }));
    }
  }, [selectedNode]);
  
  // Stats
  const stats = useMemo(() => {
    const episodic = memories.filter(m => m.type === 'episodic').length;
    const semantic = memories.filter(m => m.type === 'semantic').length;
    const procedural = memories.filter(m => m.type === 'procedural').length;
    const connections = memories.reduce((acc, m) => acc + (m.relatedIds?.length || 0), 0);
    
    return { episodic, semantic, procedural, connections };
  }, [memories]);
  
  // Get phase color for UI
  const getPhaseColor = (phase: string): string => {
    const colors: Record<string, string> = {
      PERCEIVE: '#60a5fa',
      REMEMBER: '#f472b6',
      REASON: '#fbbf24',
      ACT: '#4ade80',
      REFLECT: '#a78bfa',
      CONSOLIDATE: '#22d3ee'
    };
    return colors[phase] || '#60a5fa';
  };

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
            Phase 5: Adaptive Atmosphere
          </p>
        </div>
        
        {/* Phase 5: Agent State Controls */}
        <div style={{ 
          display: 'flex', 
          gap: '1rem', 
          alignItems: 'center',
          padding: '0.75rem 1.25rem',
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          {/* Cognitive Phase */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            <label style={{ fontSize: '0.625rem', color: 'rgba(255, 255, 255, 0.5)', textTransform: 'uppercase' }}>
              Phase
            </label>
            <select
              value={agentState.cognitivePhase}
              onChange={(e) => setAgentState(prev => ({ ...prev, cognitivePhase: e.target.value as AgentState['cognitivePhase'] }))}
              style={{
                background: 'rgba(0, 0, 0, 0.5)',
                border: `1px solid ${getPhaseColor(agentState.cognitivePhase)}`,
                borderRadius: '4px',
                color: getPhaseColor(agentState.cognitivePhase),
                fontSize: '0.75rem',
                padding: '0.25rem 0.5rem',
                fontFamily: 'JetBrains Mono, monospace',
                cursor: 'pointer'
              }}
            >
              {phases.map(phase => (
                <option key={phase} value={phase}>{phase}</option>
              ))}
            </select>
          </div>
          
          {/* Confidence Slider */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', minWidth: '120px' }}>
            <label style={{ fontSize: '0.625rem', color: 'rgba(255, 255, 255, 0.5)', textTransform: 'uppercase' }}>
              Confidence {Math.round(agentState.confidence * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={agentState.confidence * 100}
              onChange={(e) => setAgentState(prev => ({ 
                ...prev, 
                confidence: parseInt(e.target.value) / 100 
              }))}
              style={{ width: '100%' }}
            />
          </div>
          
          {/* Entropy Slider */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', minWidth: '120px' }}>
            <label style={{ 
              fontSize: '0.625rem', 
              color: agentState.entropy > 0.6 ? '#f87171' : 'rgba(255, 255, 255, 0.5)', 
              textTransform: 'uppercase' 
            }}>
              Entropy {Math.round(agentState.entropy * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={agentState.entropy * 100}
              onChange={(e) => setAgentState(prev => ({ 
                ...prev, 
                entropy: parseInt(e.target.value) / 100 
              }))}
              style={{ width: '100%' }}
            />
          </div>
          
          {/* Auto Cycle Toggle */}
          <button
            onClick={() => setAutoCycle(!autoCycle)}
            style={{
              padding: '0.4rem 0.75rem',
              background: autoCycle ? 'rgba(74, 222, 128, 0.2)' : 'rgba(255, 255, 255, 0.1)',
              border: `1px solid ${autoCycle ? '#4ade80' : 'rgba(255, 255, 255, 0.3)'}`,
              borderRadius: '4px',
              color: autoCycle ? '#4ade80' : 'rgba(255, 255, 255, 0.7)',
              fontSize: '0.625rem',
              cursor: 'pointer',
              textTransform: 'uppercase',
              fontFamily: 'JetBrains Mono, monospace'
            }}
          >
            {autoCycle ? '⏸ Cycle' : '▶ Cycle'}
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
            agentState={agentState}
            showEntropyField={showEntropyField}
            enableAnimations={enableAnimations}
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
            
            {/* Phase 5: Visual indicators */}
            <div style={{ marginTop: '0.75rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
              <div style={{ fontSize: '0.625rem', color: 'rgba(255, 255, 255, 0.4)', marginBottom: '0.25rem' }}>
                STATE INDICATORS
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', fontSize: '0.625rem' }}>
                <span style={{ color: '#00ff88' }}>● Active</span>
                <span style={{ color: '#ef4444' }}>⚠ High Entropy</span>
              </div>
            </div>
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
          width: '320px',
          borderLeft: '1px solid rgba(0, 255, 213, 0.2)',
          background: 'rgba(26, 26, 46, 0.3)',
          padding: '1.5rem',
          overflow: 'auto'
        }}>
          {/* Phase 5: Controls */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{
              fontSize: '0.75rem',
              color: '#00ffd5',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: '1rem'
            }}>
              Atmosphere Controls
            </h3>
            
            {/* Entropy Field Toggle */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '0.75rem',
              padding: '0.5rem',
              background: 'rgba(0, 0, 0, 0.2)',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.7)' }}>
                Entropy Field
              </span>
              <button
                onClick={() => setShowEntropyField(!showEntropyField)}
                style={{
                  padding: '0.25rem 0.75rem',
                  background: showEntropyField ? 'rgba(0, 255, 213, 0.2)' : 'rgba(255, 255, 255, 0.1)',
                  border: `1px solid ${showEntropyField ? '#00ffd5' : 'rgba(255, 255, 255, 0.3)'}`,
                  borderRadius: '4px',
                  color: showEntropyField ? '#00ffd5' : 'rgba(255, 255, 255, 0.5)',
                  fontSize: '0.625rem',
                  cursor: 'pointer'
                }}
              >
                {showEntropyField ? 'ON' : 'OFF'}
              </button>
            </div>
            
            {/* Animations Toggle */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '0.75rem',
              padding: '0.5rem',
              background: 'rgba(0, 0, 0, 0.2)',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.7)' }}>
                Animations
              </span>
              <button
                onClick={() => setEnableAnimations(!enableAnimations)}
                style={{
                  padding: '0.25rem 0.75rem',
                  background: enableAnimations ? 'rgba(0, 255, 213, 0.2)' : 'rgba(255, 255, 255, 0.1)',
                  border: `1px solid ${enableAnimations ? '#00ffd5' : 'rgba(255, 255, 255, 0.3)'}`,
                  borderRadius: '4px',
                  color: enableAnimations ? '#00ffd5' : 'rgba(255, 255, 255, 0.5)',
                  fontSize: '0.625rem',
                  cursor: 'pointer'
                }}
              >
                {enableAnimations ? 'ON' : 'OFF'}
              </button>
            </div>
            
            {/* Cognitive State */}
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column',
              gap: '0.25rem',
              marginBottom: '0.75rem',
              padding: '0.5rem',
              background: 'rgba(0, 0, 0, 0.2)',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.7)' }}>
                Cognitive State
              </span>
              <select
                value={agentState.cognitiveState}
                onChange={(e) => setAgentState(prev => ({ 
                  ...prev, 
                  cognitiveState: e.target.value as AgentState['cognitiveState']
                }))}
                style={{
                  background: 'rgba(0, 0, 0, 0.5)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '4px',
                  color: 'rgba(255, 255, 255, 0.9)',
                  fontSize: '0.75rem',
                  padding: '0.375rem',
                  fontFamily: 'JetBrains Mono, monospace'
                }}
              >
                <option value="stable">Stable</option>
                <option value="focused">Focused</option>
                <option value="scattered">Scattered</option>
              </select>
            </div>
          </div>
          
          {/* Memory Controls */}
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{
              fontSize: '0.75rem',
              color: '#00ffd5',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: '1rem'
            }}>
              Memory Controls
            </h3>
            
            {/* Node Count */}
            <div style={{ marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.7)' }}>Total Nodes</span>
                <span style={{ fontSize: '0.75rem', color: '#00ffd5' }}>{memories.length}</span>
              </div>
              <input
                type="range"
                min="10"
                max="100"
                value={nodeCount}
                onChange={(e) => {
                  const count = parseInt(e.target.value);
                  setNodeCount(count);
                }}
                style={{ width: '100%', marginBottom: '0.5rem' }}
              />
              <button
                onClick={() => regenerateMemories(nodeCount)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  background: 'rgba(0, 255, 213, 0.1)',
                  border: '1px solid rgba(0, 255, 213, 0.3)',
                  borderRadius: '4px',
                  color: '#00ffd5',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  fontFamily: 'JetBrains Mono, monospace'
                }}
              >
                Regenerate All
              </button>
            </div>
            
            {/* Add/Remove Buttons */}
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={addMemory}
                style={{
                  flex: 1,
                  padding: '0.5rem',
                  background: 'rgba(74, 222, 128, 0.1)',
                  border: '1px solid rgba(74, 222, 128, 0.3)',
                  borderRadius: '4px',
                  color: '#4ade80',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  fontFamily: 'JetBrains Mono, monospace'
                }}
              >
                + Add Memory
              </button>
              <button
                onClick={removeMemory}
                disabled={memories.length === 0}
                style={{
                  flex: 1,
                  padding: '0.5rem',
                  background: memories.length === 0 ? 'rgba(239, 68, 68, 0.05)' : 'rgba(239, 68, 68, 0.1)',
                  border: `1px solid ${memories.length === 0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(239, 68, 68, 0.3)'}`,
                  borderRadius: '4px',
                  color: memories.length === 0 ? 'rgba(239, 68, 68, 0.3)' : '#f87171',
                  fontSize: '0.75rem',
                  cursor: memories.length === 0 ? 'not-allowed' : 'pointer',
                  fontFamily: 'JetBrains Mono, monospace'
                }}
              >
                - Remove
              </button>
            </div>
          </div>
          
          {/* Stats */}
          <div style={{ marginBottom: '1.5rem' }}>
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
