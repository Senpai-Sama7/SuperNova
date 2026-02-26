/**
 * MemoryNode3D - Interactive 3D Memory Crystal
 * 
 * Geometric representation of memories with:
 * - Episodic: Tetrahedron (temporal events)
 * - Semantic: Octahedron (factual knowledge)
 * - Procedural: Box (skills/how-to)
 * 
 * @author WebGL Performance Engineering Team
 * @phase Phase 4 - 3D Memory Space
 */

import React, { useRef, useMemo, useState } from 'react';
import { useFrame, ThreeEvent } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import type { MemoryNode } from './MemorySpace3D';

/** Props for MemoryNode3D */
interface MemoryNode3DProps {
  position: [number, number, number];
  type: MemoryNode['type'];
  strength: number;
  label: string;
  isSelected?: boolean;
  onClick?: () => void;
  onHover?: (hovered: boolean) => void;
}

/** Memory type configuration */
const MEMORY_CONFIG = {
  episodic: {
    geometry: 'tetrahedron',
    color: '#f472b6', // Pink - temporal events
    emissive: 0.3,
    size: 0.4,
    rotationSpeed: 0.5
  },
  semantic: {
    geometry: 'octahedron',
    color: '#fbbf24', // Gold - factual knowledge
    emissive: 0.4,
    size: 0.35,
    rotationSpeed: 0.3
  },
  procedural: {
    geometry: 'box',
    color: '#f59e0b', // Amber - skills
    emissive: 0.35,
    size: 0.45,
    rotationSpeed: 0.2
  }
} as const;

/** Reusable geometries for performance */
const GEOMETRIES = {
  tetrahedron: new THREE.TetrahedronGeometry(0.5, 0),
  octahedron: new THREE.OctahedronGeometry(0.5, 0),
  box: new THREE.BoxGeometry(0.5, 0.5, 0.5)
};

/** Reusable materials base */
const createMaterial = (color: string, emissiveIntensity: number) => {
  return new THREE.MeshStandardMaterial({
    color,
    emissive: color,
    emissiveIntensity,
    roughness: 0.3,
    metalness: 0.7,
    transparent: true,
    opacity: 0.9
  });
};

export const MemoryNode3D: React.FC<MemoryNode3DProps> = ({
  position,
  type,
  strength,
  label,
  isSelected = false,
  onClick,
  onHover
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.PointLight>(null);
  const [hovered, setHovered] = useState(false);
  
  const config = MEMORY_CONFIG[type];
  
  // Shared geometry (performance optimization)
  const geometry = useMemo(() => GEOMETRIES[config.geometry as keyof typeof GEOMETRIES], [config.geometry]);
  
  // Material with dynamic emissive intensity
  const material = useMemo(() => {
    const baseIntensity = config.emissive;
    const hoverMultiplier = hovered ? 2 : 1;
    const selectedMultiplier = isSelected ? 1.5 : 1;
    return createMaterial(config.color, baseIntensity * hoverMultiplier * selectedMultiplier);
  }, [config.color, config.emissive, hovered, isSelected]);

  // Animation loop
  useFrame((state) => {
    if (!meshRef.current) return;
    
    const time = state.clock.elapsedTime;
    
    // Gentle rotation
    meshRef.current.rotation.x = Math.sin(time * config.rotationSpeed) * 0.1;
    meshRef.current.rotation.y += 0.005 * config.rotationSpeed;
    meshRef.current.rotation.z = Math.cos(time * config.rotationSpeed * 0.7) * 0.05;
    
    // Pulse effect based on memory strength
    const pulse = Math.sin(time * 2) * 0.1 + 1;
    const baseScale = config.size * strength;
    const hoverScale = hovered ? 1.2 : 1;
    const selectedScale = isSelected ? 1.3 : 1;
    const finalScale = baseScale * pulse * hoverScale * selectedScale;
    
    meshRef.current.scale.setScalar(finalScale);
    
    // Update glow intensity
    if (glowRef.current) {
      const baseGlow = hovered ? 2 : 0.8;
      const selectedGlow = isSelected ? 1.5 : 1;
      glowRef.current.intensity = baseGlow * selectedGlow * (0.8 + Math.sin(time * 3) * 0.2);
    }
  });

  // Event handlers
  const handlePointerOver = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    setHovered(true);
    onHover?.(true);
    document.body.style.cursor = 'pointer';
  };

  const handlePointerOut = (e: ThreeEvent<PointerEvent>) => {
    e.stopPropagation();
    setHovered(false);
    onHover?.(false);
    document.body.style.cursor = 'auto';
  };

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    onClick?.();
  };

  // Selection ring
  const SelectionRing = isSelected ? (
    <mesh rotation={[Math.PI / 2, 0, 0]}>
      <ringGeometry args={[config.size * strength * 1.5, config.size * strength * 1.7, 32]} />
      <meshBasicMaterial color="#00ffd5" transparent opacity={0.6} side={THREE.DoubleSide} />
    </mesh>
  ) : null;

  return (
    <group position={position}>
      {/* Main memory crystal */}
      <mesh
        ref={meshRef}
        geometry={geometry}
        material={material}
        onClick={handleClick}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
        castShadow
        receiveShadow
      />
      
      {/* Selection indicator */}
      {SelectionRing}
      
      {/* Glow light */}
      <pointLight
        ref={glowRef}
        color={config.color}
        intensity={hovered ? 2 : 0.8}
        distance={5}
        decay={2}
      />
      
      {/* Tooltip on hover */}
      {hovered && (
        <Html distanceFactor={10} style={{ pointerEvents: 'none' }}>
          <div style={{
            background: 'rgba(26, 26, 46, 0.95)',
            border: `1px solid ${config.color}`,
            borderRadius: '8px',
            padding: '0.5rem 0.75rem',
            color: '#fff',
            fontFamily: 'Inter, sans-serif',
            fontSize: '0.75rem',
            whiteSpace: 'nowrap',
            boxShadow: `0 0 20px ${config.color}40`,
            backdropFilter: 'blur(10px)'
          }}>
            <div style={{ 
              color: config.color, 
              fontWeight: 600,
              marginBottom: '0.25rem'
            }}>
              {label}
            </div>
            <div style={{ 
              fontSize: '0.625rem',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              opacity: 0.7
            }}>
              {type} • Strength: {Math.round(strength * 100)}%
            </div>
          </div>
        </Html>
      )}
    </group>
  );
};

export default MemoryNode3D;
