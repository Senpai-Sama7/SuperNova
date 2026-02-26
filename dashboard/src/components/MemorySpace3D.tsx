/**
 * MemorySpace3D - 3D Neural Constellation Visualization
 * 
 * Three.js-powered immersive memory space with atmospheric lighting,
 * starfield background, and interactive navigation.
 * 
 * Phase 5 Enhancements:
 * - Adaptive lighting based on agent confidence state
 * - Entropy visualization with turbulence particle field
 * - Real-time memory update animations
 * - State-responsive glow intensity
 * 
 * @author 3D Graphics Engineering Team
 * @phase Phase 5 - Adaptive Atmosphere
 */

import React, { Suspense, useMemo, useState, useEffect } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { 
  OrbitControls, 
  Stars, 
  Float,
  PerspectiveCamera,
  useProgress
} from '@react-three/drei';
import * as THREE from 'three';
import { MemoryNode3D } from './MemoryNode3D';
import { ConnectionLines3D } from './ConnectionLines3D';
import { MemoryGraph2D } from './MemoryGraph2D';
import { AdaptiveLighting } from './AdaptiveLighting';
import { EntropyField, EntropyWave } from './EntropyField';
import { MemoryNodeAnimator, MemorySpawnEffect, useMemoryAnimations } from './MemoryNodeAnimator';

const styles = {
  container: 'memory-space-3d-container',
  canvas: 'memory-space-3d-canvas',
  loader: 'memory-space-3d-loader',
  loaderBar: 'memory-space-3d-loader-bar',
  loaderProgress: 'memory-space-3d-loader-progress',
  loaderText: 'memory-space-3d-loader-text',
  fallbackNotice: 'memory-space-3d-fallback-notice',
  fallbackIcon: 'memory-space-3d-fallback-icon'
};

/** Memory node data structure */
export interface MemoryNode {
  id: string;
  position: [number, number, number];
  type: 'episodic' | 'semantic' | 'procedural';
  strength: number;
  label: string;
  content: string;
  timestamp?: number;
  relatedIds?: string[];
}

/** Phase 5: Agent state for adaptive atmosphere */
export interface AgentState {
  /** Confidence level 0-1 (higher = brighter, more stable) */
  confidence: number;
  /** Entropy level 0-1 (higher = more chaos) */
  entropy: number;
  /** Current cognitive phase */
  cognitivePhase: 'PERCEIVE' | 'REMEMBER' | 'REASON' | 'ACT' | 'REFLECT' | 'CONSOLIDATE';
  /** Agent status */
  agentStatus: 'active' | 'reasoning' | 'waiting' | 'idle' | 'error';
  /** IDs of memories currently being processed */
  activeMemoryIds?: string[];
  /** Overall cognitive state */
  cognitiveState?: 'focused' | 'scattered' | 'stable';
}

/** Props for MemorySpace3D component */
interface MemorySpace3DProps {
  memories: MemoryNode[];
  onNodeClick?: (node: MemoryNode) => void;
  onNodeHover?: (node: MemoryNode | null) => void;
  selectedNodeId?: string | null;
  className?: string;
  /** Phase 5: Agent state for adaptive atmosphere */
  agentState?: AgentState;
  /** Phase 5: Show entropy field visualization */
  showEntropyField?: boolean;
  /** Phase 5: Enable real-time animations */
  enableAnimations?: boolean;
}

/** Default agent state */
const DEFAULT_AGENT_STATE: AgentState = {
  confidence: 0.7,
  entropy: 0.2,
  cognitivePhase: 'PERCEIVE',
  agentStatus: 'active',
  activeMemoryIds: [],
  cognitiveState: 'stable'
};

/** Loading indicator for 3D scene */
const Loader: React.FC = () => {
  const { progress } = useProgress();
  return (
    <div className={styles.loader}>
      <div className={styles.loaderBar}>
        <div 
          className={styles.loaderProgress} 
          style={{ width: `${progress}%` }}
        />
      </div>
      <span className={styles.loaderText}>
        Loading Neural Space... {Math.round(progress)}%
      </span>
    </div>
  );
};

/** Atmospheric scene setup with Phase 5 adaptive lighting */
const AtmosphericScene: React.FC<{ agentState: AgentState; showEntropyField: boolean }> = ({ 
  agentState, 
  showEntropyField 
}) => {
  const { scene } = useThree();
  
  // Configure fog for depth perception
  useEffect(() => {
    // Fog color and density are now managed by AdaptiveLighting
    scene.fog = new THREE.FogExp2(0x0a0a0f, 0.03);
    return () => {
      scene.fog = null;
    };
  }, [scene]);

  return (
    <>
      {/* Phase 5: Adaptive lighting based on agent state */}
      <AdaptiveLighting
        confidence={agentState.confidence}
        entropy={agentState.entropy}
        cognitivePhase={agentState.cognitivePhase}
        agentStatus={agentState.agentStatus}
      />
      
      {/* Phase 5: Entropy field visualization */}
      {showEntropyField && (
        <>
          <EntropyField 
            entropy={agentState.entropy} 
            particleCount={Math.floor(300 + agentState.entropy * 400)}
            bounds={15 + agentState.entropy * 5}
          />
          <EntropyWave entropy={agentState.entropy} ringCount={5} />
        </>
      )}
      
      {/* Starfield background - reacts to entropy */}
      <Stars
        radius={100}
        depth={50}
        count={Math.floor(5000 - agentState.entropy * 2000)} // Fewer stars when entropy is high
        factor={4}
        saturation={0.5}
        fade
        speed={0.5 + agentState.entropy * 1.5} // Stars move faster with high entropy
      />
    </>
  );
};

/** Camera controller with constraints */
const CameraController: React.FC = () => {
  return (
    <PerspectiveCamera
      makeDefault
      position={[0, 0, 15]}
      fov={60}
      near={0.1}
      far={1000}
    />
  );
};

/** Main 3D memory space component */
export const MemorySpace3D: React.FC<MemorySpace3DProps> = ({
  memories,
  onNodeClick,
  onNodeHover,
  selectedNodeId,
  className = '',
  agentState = DEFAULT_AGENT_STATE,
  showEntropyField = true,
  enableAnimations = true
}) => {
  const [webglSupported, setWebglSupported] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState(true);

  // Check WebGL support
  useEffect(() => {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      setWebglSupported(!!gl);
    } catch {
      setWebglSupported(false);
    }
  }, []);

  // Calculate connections between related memories
  const connections = useMemo(() => {
    const conn: Array<{ from: [number, number, number]; to: [number, number, number]; strength: number }> = [];
    
    memories.forEach(memory => {
      if (memory.relatedIds) {
        memory.relatedIds.forEach(relatedId => {
          const related = memories.find(m => m.id === relatedId);
          if (related && memory.id < related.id) { // Avoid duplicates
            conn.push({
              from: memory.position,
              to: related.position,
              strength: Math.min(memory.strength, related.strength)
            });
          }
        });
      }
    });
    
    return conn;
  }, [memories]);

  // Phase 5: Memory animation management
  const {
    enteringNodes,
    exitingNodes,
    spawnEffects,
    completeEnter,
    completeExit,
    completeSpawn
  } = useMemoryAnimations(memories, {
    onNodeEnter: (id) => console.log('Memory entered:', id),
    onNodeExit: (id) => console.log('Memory exited:', id)
  });

  // Fallback to 2D if WebGL not supported
  if (!webglSupported) {
    return (
      <div className={`${styles.container} ${className}`}>
        <div className={styles.fallbackNotice}>
          <span className={styles.fallbackIcon}>⚡</span>
          <span>WebGL not available - showing 2D view</span>
        </div>
        <MemoryGraph2D memories={memories} />
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${className}`}>
      <Suspense fallback={<Loader />}>
        <Canvas
          className={styles.canvas}
          gl={{
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance',
            stencil: false,
            depth: true
          }}
          camera={{ position: [0, 0, 15], fov: 60 }}
          dpr={[1, 2]}
          frameloop="always"
          onCreated={() => setIsLoading(false)}
        >
          <CameraController />
          <AtmosphericScene agentState={agentState} showEntropyField={showEntropyField} />
          
          {/* Phase 5: Spawn effects for new memories */}
          {enableAnimations && spawnEffects.map(id => {
            const memory = memories.find(m => m.id === id);
            if (!memory) return null;
            const color = memory.type === 'episodic' ? '#f472b6' : 
                         memory.type === 'semantic' ? '#fbbf24' : '#f59e0b';
            return (
              <MemorySpawnEffect
                key={`spawn-${id}`}
                position={memory.position}
                color={color}
                onComplete={() => completeSpawn(id)}
              />
            );
          })}
          
          {/* Memory nodes with floating animation and Phase 5 state responsiveness */}
          {memories.map(memory => {
            const isEntering = enteringNodes.has(memory.id);
            const isExiting = exitingNodes.has(memory.id);
            const isActive = agentState.activeMemoryIds?.includes(memory.id) ?? false;
            
            const nodeElement = (
              <MemoryNode3D
                position={memory.position}
                type={memory.type}
                strength={memory.strength}
                label={memory.label}
                isSelected={memory.id === selectedNodeId}
                confidence={agentState.confidence}
                entropy={agentState.entropy}
                cognitivePhase={agentState.cognitivePhase}
                agentStatus={agentState.agentStatus}
                isActive={isActive}
                onClick={() => onNodeClick?.(memory)}
                onHover={(hovered) => onNodeHover?.(hovered ? memory : null)}
              />
            );
            
            if (!enableAnimations) {
              return (
                <Float
                  key={memory.id}
                  speed={2}
                  rotationIntensity={0.3}
                  floatIntensity={0.5}
                  floatingRange={[-0.2, 0.2]}
                >
                  {nodeElement}
                </Float>
              );
            }
            
            return (
              <MemoryNodeAnimator
                key={memory.id}
                node={memory}
                isEntering={isEntering}
                isExiting={isExiting}
                cognitiveState={agentState.cognitiveState}
                onEntryComplete={() => completeEnter(memory.id)}
                onExitComplete={() => completeExit(memory.id)}
              >
                <Float
                  speed={2}
                  rotationIntensity={0.3}
                  floatIntensity={0.5}
                  floatingRange={[-0.2, 0.2]}
                >
                  {nodeElement}
                </Float>
              </MemoryNodeAnimator>
            );
          })}
          
          {/* Neural connections */}
          <ConnectionLines3D connections={connections} />
          
          {/* Navigation controls */}
          <OrbitControls
            enableZoom={true}
            enablePan={true}
            enableRotate={true}
            minDistance={5}
            maxDistance={30}
            zoomSpeed={0.8}
            rotateSpeed={0.6}
            panSpeed={0.8}
            enableDamping={true}
            dampingFactor={0.05}
            autoRotate={false}
            autoRotateSpeed={0.5}
          />
        </Canvas>
      </Suspense>
      
      {isLoading && <Loader />}
    </div>
  );
};

export default MemorySpace3D;
