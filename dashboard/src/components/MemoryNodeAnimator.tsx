/**
 * MemoryNodeAnimator - Real-Time Memory Update Animations
 * 
 * Handles smooth animations for memory nodes being added or removed:
 * - Entry animation: Scale up from 0 with a "pop" effect
 * - Exit animation: Scale down with fade out
 * - Update animation: Pulse when memory strength changes
 * - Connection animation: Draw connections with growing effect
 * 
 * @author Phase 5 - Adaptive Atmosphere
 */

import React, { useRef, useMemo, useEffect, useState, useCallback } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { MemoryNode } from './MemorySpace3D';

/** Props for MemoryNodeAnimator wrapper */
interface MemoryNodeAnimatorProps {
  node: MemoryNode;
  children: React.ReactNode;
  /** Called when entry animation completes */
  onEntryComplete?: (id: string) => void;
  /** Called when exit animation completes */
  onExitComplete?: (id: string) => void;
  /** Current cognitive state affects animation style */
  cognitiveState?: 'focused' | 'scattered' | 'stable';
  /** Is this node currently entering */
  isEntering?: boolean;
  /** Is this node currently exiting */
  isExiting?: boolean;
}

/** Animation constants */
const ANIMATION = {
  enterSpeed: 0.15,
  exitSpeed: 0.08,
  pulseSpeed: 0.2,
  springTension: 0.3,
  springFriction: 0.8
} as const;

/**
 * Animated memory node wrapper
 */
export const MemoryNodeAnimator: React.FC<MemoryNodeAnimatorProps> = ({
  node,
  children,
  onEntryComplete,
  onExitComplete,
  cognitiveState = 'stable',
  isEntering = false,
  isExiting = false
}) => {
  const groupRef = useRef<THREE.Group>(null);
  
  // Animation state
  const animState = useRef({
    scale: isEntering ? 0 : 1,
    targetScale: 1,
    velocity: 0,
    pulse: 0,
    pulseVelocity: 0,
    opacity: isEntering ? 0 : 1,
    hasEntered: !isEntering,
    jitter: { x: 0, y: 0, z: 0 }
  });
  
  // Trigger pulse on strength change
  const lastStrengthRef = useRef(node.strength);
  useEffect(() => {
    if (Math.abs(node.strength - lastStrengthRef.current) > 0.1) {
      animState.current.pulse = 1;
      lastStrengthRef.current = node.strength;
    }
  }, [node.strength]);
  
  // Animation loop
  useFrame((_, delta) => {
    if (!groupRef.current) return;
    
    const anim = animState.current;
    const dt = Math.min(delta, 0.1); // Cap delta time
    
    // Handle entry animation
    if (isEntering && !anim.hasEntered) {
      anim.targetScale = 1;
      anim.scale += (anim.targetScale - anim.scale) * ANIMATION.enterSpeed;
      anim.opacity += (1 - anim.opacity) * ANIMATION.enterSpeed;
      
      if (Math.abs(anim.scale - 1) < 0.01) {
        anim.hasEntered = true;
        anim.scale = 1;
        anim.opacity = 1;
        onEntryComplete?.(node.id);
      }
    }
    
    // Handle exit animation
    if (isExiting) {
      anim.targetScale = 0;
      anim.scale += (anim.targetScale - anim.scale) * ANIMATION.exitSpeed;
      anim.opacity += (0 - anim.opacity) * ANIMATION.exitSpeed;
      
      if (anim.scale < 0.01) {
        anim.scale = 0;
        anim.opacity = 0;
        onExitComplete?.(node.id);
      }
    }
    
    // Spring physics for smooth scaling
    const force = (anim.targetScale - anim.scale) * ANIMATION.springTension;
    anim.velocity += force * dt * 60;
    anim.velocity *= ANIMATION.springFriction;
    anim.scale += anim.velocity * dt * 60;
    
    // Pulse animation (spring)
    if (anim.pulse > 0.001) {
      const pulseForce = -anim.pulse * 0.3;
      anim.pulseVelocity += pulseForce * dt * 60;
      anim.pulseVelocity *= 0.85; // Damping
      anim.pulse += anim.pulseVelocity * dt * 60;
      
      if (anim.pulse < 0) anim.pulse = 0;
    }
    
    // Calculate final scale with pulse
    const pulseScale = 1 + anim.pulse * 0.3;
    const finalScale = Math.max(0, anim.scale * pulseScale);
    
    // Apply scale
    groupRef.current.scale.setScalar(finalScale);
    
    // Cognitive state affects position jitter
    if (cognitiveState === 'scattered') {
      const time = Date.now() / 1000;
      anim.jitter.x = Math.sin(time * 3 + node.position[0]) * 0.08;
      anim.jitter.y = Math.cos(time * 2.5 + node.position[1]) * 0.08;
      anim.jitter.z = Math.sin(time * 2 + node.position[2]) * 0.08;
      
      groupRef.current.position.set(
        node.position[0] + anim.jitter.x,
        node.position[1] + anim.jitter.y,
        node.position[2] + anim.jitter.z
      );
    } else if (cognitiveState === 'focused') {
      // Subtle breathing motion
      const time = Date.now() / 1000;
      const breath = Math.sin(time * 0.5) * 0.02;
      groupRef.current.position.set(
        node.position[0],
        node.position[1] + breath,
        node.position[2]
      );
    } else {
      groupRef.current.position.set(...node.position);
    }
  });
  
  return (
    <group ref={groupRef} position={node.position}>
      {children}
    </group>
  );
};

/**
 * Connection growth animation
 * Animates connections drawing from source to target
 */
export const AnimatedConnection: React.FC<{
  from: [number, number, number];
  to: [number, number, number];
  strength: number;
  delay?: number;
  color?: string;
}> = ({ from, to, strength, delay = 0, color = '#00ffd5' }) => {
  const lineRef = useRef<THREE.Line>(null);
  const progressRef = useRef(0);
  const delayRef = useRef(delay);
  
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(6);
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    return geo;
  }, []);
  
  useFrame((_, delta) => {
    if (!lineRef.current) return;
    
    const positionAttr = lineRef.current.geometry.attributes.position;
    if (!positionAttr) return;
    
    // Handle delay
    if (delayRef.current > 0) {
      delayRef.current -= delta;
      return;
    }
    
    // Animate progress
    progressRef.current += delta * 2; // 0.5 second draw time
    const progress = Math.min(progressRef.current, 1);
    
    const positions = positionAttr.array as Float32Array;
    
    // Start point always fixed
    positions[0] = from[0];
    positions[1] = from[1];
    positions[2] = from[2];
    
    // End point grows toward target
    positions[3] = from[0] + (to[0] - from[0]) * progress;
    positions[4] = from[1] + (to[1] - from[1]) * progress;
    positions[5] = from[2] + (to[2] - from[2]) * progress;
    
    positionAttr.needsUpdate = true;
    
    // Fade in
    const material = lineRef.current.material as THREE.LineBasicMaterial;
    material.opacity = 0.6 * strength * progress;
  });
  
  return (
    <primitive object={new THREE.Line(geometry, new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity: 0,
      blending: THREE.AdditiveBlending
    }))} ref={lineRef} />
  );
};

/**
 * Memory addition effect - particles spawning at position
 */
export const MemorySpawnEffect: React.FC<{
  position: [number, number, number];
  color?: string;
  onComplete?: () => void;
}> = ({ position, color = '#00ffd5', onComplete }) => {
  const particlesRef = useRef<THREE.Points>(null);
  const [alive, setAlive] = useState(true);
  const frameCount = useRef(0);
  
  const particleCount = 20;
  const velocities = useRef(
    Array.from({ length: particleCount }, () => ({
      x: (Math.random() - 0.5) * 0.3,
      y: (Math.random() - 0.5) * 0.3,
      z: (Math.random() - 0.5) * 0.3
    }))
  );
  
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = position[0];
      positions[i * 3 + 1] = position[1];
      positions[i * 3 + 2] = position[2];
    }
    
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    return geo;
  }, [position]);
  
  useFrame(() => {
    if (!particlesRef.current) return;
    
    frameCount.current++;
    const positionAttr = particlesRef.current.geometry.attributes.position;
    if (!positionAttr) return;
    
    const positions = positionAttr.array as Float32Array;
    let stillMoving = false;
    
    for (let i = 0; i < particleCount; i++) {
      // Update position
      positions[i * 3] += velocities.current[i].x;
      positions[i * 3 + 1] += velocities.current[i].y;
      positions[i * 3 + 2] += velocities.current[i].z;
      
      // Slow down with friction
      velocities.current[i].x *= 0.92;
      velocities.current[i].y *= 0.92;
      velocities.current[i].z *= 0.92;
      
      // Check if still moving
      const speed = Math.abs(velocities.current[i].x) + 
                    Math.abs(velocities.current[i].y) + 
                    Math.abs(velocities.current[i].z);
      if (speed > 0.005) stillMoving = true;
    }
    
    positionAttr.needsUpdate = true;
    
    // Fade out material
    const material = particlesRef.current.material as THREE.PointsMaterial;
    material.opacity *= 0.96;
    
    // Complete after ~2 seconds or when stopped
    if (frameCount.current > 120 || (!stillMoving && material.opacity < 0.05)) {
      setAlive(false);
      onComplete?.();
    }
  });
  
  if (!alive) return null;
  
  return (
    <points ref={particlesRef} geometry={geometry}>
      <pointsMaterial
        color={color}
        size={0.08}
        transparent
        opacity={1}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  );
};

/**
 * Memory merge effect - when memories connect/combine
 */
export const MemoryMergeEffect: React.FC<{
  from: [number, number, number];
  to: [number, number, number];
  color?: string;
  onComplete?: () => void;
}> = ({ from, to, color = '#00ffd5', onComplete }) => {
  const particleCount = 15;
  const particlesRef = useRef<THREE.Points>(null);
  const [alive, setAlive] = useState(true);
  const progressRef = useRef(0);
  
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    
    // Start at 'from' position with random offset
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = from[0] + (Math.random() - 0.5) * 0.5;
      positions[i * 3 + 1] = from[1] + (Math.random() - 0.5) * 0.5;
      positions[i * 3 + 2] = from[2] + (Math.random() - 0.5) * 0.5;
    }
    
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    return geo;
  }, [from]);
  
  useFrame((state, delta) => {
    if (!particlesRef.current) return;
    
    progressRef.current += delta * 1.5;
    const t = Math.min(progressRef.current, 1);
    
    const positionAttr = particlesRef.current.geometry.attributes.position;
    if (!positionAttr) return;
    
    const positions = positionAttr.array as Float32Array;
    
    for (let i = 0; i < particleCount; i++) {
      // Lerp toward target with some noise
      const noiseX = Math.sin(state.clock.elapsedTime * 5 + i) * 0.1 * (1 - t);
      const noiseY = Math.cos(state.clock.elapsedTime * 5 + i) * 0.1 * (1 - t);
      const noiseZ = Math.sin(state.clock.elapsedTime * 3 + i) * 0.1 * (1 - t);
      
      const startX = from[0] + (Math.random() - 0.5) * 0.5;
      const startY = from[1] + (Math.random() - 0.5) * 0.5;
      const startZ = from[2] + (Math.random() - 0.5) * 0.5;
      
      positions[i * 3] = startX + (to[0] - startX) * t + noiseX;
      positions[i * 3 + 1] = startY + (to[1] - startY) * t + noiseY;
      positions[i * 3 + 2] = startZ + (to[2] - startZ) * t + noiseZ;
    }
    
    positionAttr.needsUpdate = true;
    
    // Fade out near end
    const material = particlesRef.current.material as THREE.PointsMaterial;
    material.opacity = 1 - Math.pow(t, 3);
    
    if (t >= 1) {
      setAlive(false);
      onComplete?.();
    }
  });
  
  if (!alive) return null;
  
  return (
    <points ref={particlesRef} geometry={geometry}>
      <pointsMaterial
        color={color}
        size={0.06}
        transparent
        opacity={1}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  );
};

/**
 * Hook to manage memory node animations
 */
export function useMemoryAnimations(
  memories: MemoryNode[],
  options: {
    onNodeEnter?: (id: string) => void;
    onNodeExit?: (id: string) => void;
  } = {}
) {
  const { onNodeEnter, onNodeExit } = options;
  
  const [enteringNodes, setEnteringNodes] = useState<Set<string>>(new Set());
  const [exitingNodes, setExitingNodes] = useState<Set<string>>(new Set());
  const [spawnEffects, setSpawnEffects] = useState<string[]>([]);
  const [mergeEffects, setMergeEffects] = useState<Array<{ id: string; from: string; to: string }>>([]);
  const prevMemoriesRef = useRef<MemoryNode[]>([]);
  
  // Detect changes in memories array
  useEffect(() => {
    const prevIds = new Set(prevMemoriesRef.current.map(m => m.id));
    const currentIds = new Set(memories.map(m => m.id));
    
    // Find added nodes
    const added = memories.filter(m => !prevIds.has(m.id));
    if (added.length > 0) {
      setEnteringNodes(prev => {
        const next = new Set(prev);
        added.forEach(m => next.add(m.id));
        return next;
      });
      setSpawnEffects(prev => [...prev, ...added.map(m => m.id)]);
      added.forEach(m => onNodeEnter?.(m.id));
    }
    
    // Find removed nodes
    const removed = prevMemoriesRef.current.filter(m => !currentIds.has(m.id));
    if (removed.length > 0) {
      setExitingNodes(prev => {
        const next = new Set(prev);
        removed.forEach(m => next.add(m.id));
        return next;
      });
      removed.forEach(m => onNodeExit?.(m.id));
    }
    
    prevMemoriesRef.current = memories;
  }, [memories, onNodeEnter, onNodeExit]);
  
  const completeEnter = useCallback((id: string) => {
    setEnteringNodes(prev => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }, []);
  
  const completeExit = useCallback((id: string) => {
    setExitingNodes(prev => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }, []);
  
  const completeSpawn = useCallback((id: string) => {
    setSpawnEffects(prev => prev.filter(sid => sid !== id));
  }, []);
  
  const completeMerge = useCallback((id: string) => {
    setMergeEffects(prev => prev.filter(m => m.id !== id));
  }, []);
  
  return {
    enteringNodes,
    exitingNodes,
    spawnEffects,
    mergeEffects,
    completeEnter,
    completeExit,
    completeSpawn,
    completeMerge,
    triggerMerge: (from: string, to: string) => {
      const id = `${from}-${to}-${Date.now()}`;
      setMergeEffects(prev => [...prev, { id, from, to }]);
    }
  };
}

export default MemoryNodeAnimator;
