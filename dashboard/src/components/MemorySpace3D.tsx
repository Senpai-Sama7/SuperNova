/**
 * MemorySpace3D - 3D Neural Constellation Visualization
 * 
 * Three.js-powered immersive memory space with atmospheric lighting,
 * starfield background, and interactive navigation.
 * 
 * @author 3D Graphics Engineering Team
 * @phase Phase 4 - 3D Memory Space
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

/** Props for MemorySpace3D component */
interface MemorySpace3DProps {
  memories: MemoryNode[];
  onNodeClick?: (node: MemoryNode) => void;
  onNodeHover?: (node: MemoryNode | null) => void;
  selectedNodeId?: string | null;
  className?: string;
}

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

/** Atmospheric scene setup with lighting */
const AtmosphericScene: React.FC = () => {
  const { scene } = useThree();
  
  // Configure fog for depth perception
  useEffect(() => {
    scene.fog = new THREE.FogExp2(0x0a0a0f, 0.03);
    return () => {
      scene.fog = null;
    };
  }, [scene]);

  return (
    <>
      {/* Ambient lighting - neural purple tint */}
      <ambientLight intensity={0.3} color="#7c3aed" />
      
      {/* Main point light - supernova cyan */}
      <pointLight 
        position={[10, 10, 10]} 
        intensity={1.5} 
        color="#00ffd5"
        distance={50}
        decay={2}
      />
      
      {/* Secondary point light - warm accent */}
      <pointLight 
        position={[-10, -10, -5]} 
        intensity={0.8} 
        color="#f472b6"
        distance={40}
        decay={2}
      />
      
      {/* Rim light for edge definition */}
      <directionalLight
        position={[0, 10, 0]}
        intensity={0.5}
        color="#ffffff"
      />
      
      {/* Starfield background */}
      <Stars
        radius={100}
        depth={50}
        count={5000}
        factor={4}
        saturation={0.5}
        fade
        speed={0.5}
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
  className = ''
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
          <AtmosphericScene />
          
          {/* Memory nodes with floating animation */}
          {memories.map(memory => (
            <Float
              key={memory.id}
              speed={2}
              rotationIntensity={0.3}
              floatIntensity={0.5}
              floatingRange={[-0.2, 0.2]}
            >
              <MemoryNode3D
                position={memory.position}
                type={memory.type}
                strength={memory.strength}
                label={memory.label}
                isSelected={memory.id === selectedNodeId}
                onClick={() => onNodeClick?.(memory)}
                onHover={(hovered) => onNodeHover?.(hovered ? memory : null)}
              />
            </Float>
          ))}
          
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
