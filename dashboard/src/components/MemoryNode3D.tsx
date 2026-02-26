/**
 * MemoryNode3D - Interactive 3D Memory Crystal with State-Responsive Glow
 * 
 * Geometric representation of memories with:
 * - Episodic: Tetrahedron (temporal events)
 * - Semantic: Octahedron (factual knowledge)
 * - Procedural: Box (skills/how-to)
 * 
 * Features Phase 5 enhancements:
 * - State-responsive glow intensity (confidence, entropy, cognitive phase)
 * - Enhanced material properties reacting to agent state
 * - Pulsing animations synced with cognitive rhythm
 * 
 * @author WebGL Performance Engineering Team
 * @phase Phase 5 - Adaptive Atmosphere
 */

import React, { useRef, useMemo, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
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
  /** Phase 5: Agent confidence 0-1 affects glow intensity */
  confidence?: number;
  /** Phase 5: Entropy 0-1 affects color stability */
  entropy?: number;
  /** Phase 5: Cognitive phase affects animation style */
  cognitivePhase?: 'PERCEIVE' | 'REMEMBER' | 'REASON' | 'ACT' | 'REFLECT' | 'CONSOLIDATE';
  /** Phase 5: Agent status affects base glow */
  agentStatus?: 'active' | 'reasoning' | 'waiting' | 'idle' | 'error';
  /** Phase 5: Is this node being actively processed */
  isActive?: boolean;
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

/** Phase-specific glow modifiers */
const PHASE_GLOW_MODIFIERS: Record<string, number> = {
  PERCEIVE: 1.0,
  REMEMBER: 0.9,
  REASON: 1.3,    // Brighter when reasoning
  ACT: 1.4,       // Brightest when acting
  REFLECT: 0.7,   // Dim during reflection
  CONSOLIDATE: 0.8
};

/** Status-specific glow modifiers */
const STATUS_GLOW_MODIFIERS: Record<string, number> = {
  active: 1.2,
  reasoning: 1.4,
  waiting: 0.8,
  idle: 0.6,
  error: 0.9
};

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
  onHover,
  confidence = 0.7,
  entropy = 0.2,
  cognitivePhase = 'PERCEIVE',
  agentStatus = 'active',
  isActive = false
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.PointLight>(null);
  const [hovered, setHovered] = useState(false);
  
  const config = MEMORY_CONFIG[type];
  
  // Shared geometry (performance optimization)
  const geometry = useMemo(() => GEOMETRIES[config.geometry as keyof typeof GEOMETRIES], [config.geometry]);
  
  // Calculate state-responsive emissive intensity
  const calculateEmissiveIntensity = () => {
    const baseIntensity = config.emissive;
    const phaseMod = PHASE_GLOW_MODIFIERS[cognitivePhase] ?? 1;
    const statusMod = STATUS_GLOW_MODIFIERS[agentStatus] ?? 1;
    const confidenceMod = 0.5 + confidence; // 0.5 to 1.5 based on confidence
    const activeMod = isActive ? 1.5 : 1;
    
    // Entropy reduces stability (more flicker when high entropy)
    const entropyStability = 1 - entropy * 0.3;
    
    return baseIntensity * phaseMod * statusMod * confidenceMod * activeMod * entropyStability;
  };
  
  // Calculate state-responsive glow color
  const calculateGlowColor = () => {
    const baseColor = new THREE.Color(config.color);
    
    // High entropy shifts color toward red (warning)
    if (entropy > 0.6) {
      const shiftAmount = (entropy - 0.6) * 2; // 0 to 0.8
      const warningColor = new THREE.Color('#ff4444');
      baseColor.lerp(warningColor, shiftAmount * 0.3);
    }
    
    // Low confidence shifts toward gray/dull
    if (confidence < 0.4) {
      const grayAmount = (0.4 - confidence) * 1.5;
      const grayColor = new THREE.Color('#666666');
      baseColor.lerp(grayColor, grayAmount * 0.4);
    }
    
    return baseColor;
  };
  
  // Material with dynamic emissive intensity
  const material = useMemo(() => {
    const intensity = calculateEmissiveIntensity();
    const hoverMultiplier = hovered ? 2 : 1;
    const selectedMultiplier = isSelected ? 1.5 : 1;
    return createMaterial(config.color, intensity * hoverMultiplier * selectedMultiplier);
  }, [config.color, config.emissive, hovered, isSelected, confidence, entropy, cognitivePhase, agentStatus, isActive]);
  
  // Update material when state changes
  useEffect(() => {
    if (meshRef.current) {
      meshRef.current.material = material;
    }
  }, [material]);
  
  // Animation loop with state-responsive effects
  useFrame((state) => {
    if (!meshRef.current) return;
    
    const time = state.clock.elapsedTime;
    
    // Gentle rotation - speed varies by cognitive phase
    const phaseSpeedMod = PHASE_GLOW_MODIFIERS[cognitivePhase] ?? 1;
    meshRef.current.rotation.x = Math.sin(time * config.rotationSpeed * phaseSpeedMod) * 0.1;
    meshRef.current.rotation.y += 0.005 * config.rotationSpeed * phaseSpeedMod;
    meshRef.current.rotation.z = Math.cos(time * config.rotationSpeed * 0.7) * 0.05;
    
    // Pulse effect based on memory strength AND confidence
    const pulseBase = Math.sin(time * 2) * 0.1 + 1;
    const confidencePulse = isActive ? 1 + Math.sin(time * 4) * 0.1 : 1;
    const pulse = pulseBase * confidencePulse;
    
    const baseScale = config.size * strength;
    const hoverScale = hovered ? 1.2 : 1;
    const selectedScale = isSelected ? 1.3 : 1;
    const activeScale = isActive ? 1.15 : 1;
    const finalScale = baseScale * pulse * hoverScale * selectedScale * activeScale;
    
    meshRef.current.scale.setScalar(finalScale);
    
    // Update glow intensity with state responsiveness
    if (glowRef.current) {
      const baseGlow = hovered ? 2 : 0.8;
      const selectedGlow = isSelected ? 1.5 : 1;
      const activeGlow = isActive ? 1.8 : 1;
      const confidenceGlow = 0.5 + confidence;
      
      // Entropy causes flicker in glow
      const entropyFlicker = entropy > 0.5 
        ? Math.sin(time * (5 + entropy * 10)) * entropy * 0.3
        : 0;
      
      glowRef.current.intensity = baseGlow * selectedGlow * activeGlow * confidenceGlow * 
        (0.8 + Math.sin(time * 3) * 0.2) + entropyFlicker;
      
      // Update glow color based on state
      glowRef.current.color = calculateGlowColor();
    }
    
    // Entropy affects position jitter when very high
    if (entropy > 0.7 && meshRef.current.parent) {
      const jitterX = Math.sin(time * 10 + position[0]) * entropy * 0.02;
      const jitterY = Math.cos(time * 12 + position[1]) * entropy * 0.02;
      const jitterZ = Math.sin(time * 8 + position[2]) * entropy * 0.02;
      
      meshRef.current.position.set(jitterX, jitterY, jitterZ);
    } else if (meshRef.current.position.x !== 0) {
      meshRef.current.position.set(0, 0, 0);
    }
  });
  
  // Event handlers
  const handlePointerOver = (e: { stopPropagation: () => void }) => {
    e.stopPropagation();
    setHovered(true);
    onHover?.(true);
    document.body.style.cursor = 'pointer';
  };
  
  const handlePointerOut = (e: { stopPropagation: () => void }) => {
    e.stopPropagation();
    setHovered(false);
    onHover?.(false);
    document.body.style.cursor = 'auto';
  };
  
  const handleClick = (e: { stopPropagation: () => void }) => {
    e.stopPropagation();
    onClick?.();
  };
  
  // Selection ring with state-responsive color
  const selectionRingColor = useMemo(() => {
    if (entropy > 0.6) return '#ff4444';
    if (isActive) return '#00ff88';
    return '#00ffd5';
  }, [entropy, isActive]);
  
  const SelectionRing = isSelected ? (
    <mesh rotation={[Math.PI / 2, 0, 0]}>
      <ringGeometry args={[config.size * strength * 1.5, config.size * strength * 1.7, 32]} />
      <meshBasicMaterial color={selectionRingColor} transparent opacity={0.6} side={THREE.DoubleSide} />
    </mesh>
  ) : null;
  
  // Active indicator (pulsing ring when node is being processed)
  const ActiveIndicator = isActive ? (
    <mesh rotation={[Math.PI / 2, 0, 0]}>
      <ringGeometry args={[config.size * strength * 1.8, config.size * strength * 1.9, 32]} />
      <meshBasicMaterial 
        color="#00ff88" 
        transparent 
        opacity={0.4} 
        side={THREE.DoubleSide}
      />
    </mesh>
  ) : null;
  
  // State badge showing confidence/entropy
  const StateBadge = (entropy > 0.6 || confidence < 0.4) ? (
    <Html distanceFactor={10} style={{ pointerEvents: 'none' }}>
      <div style={{
        position: 'absolute',
        top: '-40px',
        left: '50%',
        transform: 'translateX(-50%)',
        padding: '2px 6px',
        borderRadius: '4px',
        fontSize: '0.5rem',
        fontWeight: 'bold',
        textTransform: 'uppercase',
        whiteSpace: 'nowrap',
        background: entropy > 0.6 ? 'rgba(239, 68, 68, 0.9)' : 'rgba(107, 114, 128, 0.9)',
        color: '#fff'
      }}>
        {entropy > 0.6 ? '⚠ High Entropy' : confidence < 0.4 ? '↓ Low Confidence' : ''}
      </div>
    </Html>
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
      
      {/* Active processing indicator */}
      {ActiveIndicator}
      
      {/* Glow light */}
      <pointLight
        ref={glowRef}
        color={config.color}
        intensity={hovered ? 2 : 0.8}
        distance={5}
        decay={2}
      />
      
      {/* State badge */}
      {StateBadge}
      
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
              opacity: 0.7,
              marginBottom: '0.25rem'
            }}>
              {type} • Strength: {Math.round(strength * 100)}%
            </div>
            {(confidence !== 0.7 || entropy !== 0.2) && (
              <div style={{
                fontSize: '0.5rem',
                display: 'flex',
                gap: '0.5rem',
                marginTop: '0.25rem'
              }}>
                <span style={{ color: confidence > 0.6 ? '#4ade80' : confidence < 0.4 ? '#f87171' : '#fbbf24' }}>
                  ● Conf: {Math.round(confidence * 100)}%
                </span>
                <span style={{ color: entropy > 0.6 ? '#f87171' : '#60a5fa' }}>
                  ● Ent: {Math.round(entropy * 100)}%
                </span>
              </div>
            )}
          </div>
        </Html>
      )}
    </group>
  );
};

export default MemoryNode3D;
