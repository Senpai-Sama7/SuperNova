/**
 * EntropyField - Turbulence Visualization Particle System
 * 
 * Visualizes semantic entropy as a field of chaotic particles.
 * - High entropy = chaotic, fast-moving particles
 * - Low entropy = calm, organized flow
 * - Colors shift from cyan (order) to red (chaos)
 * 
 * @author Phase 5 - Adaptive Atmosphere
 */

import React, { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

/** Props for EntropyField */
interface EntropyFieldProps {
  /** Entropy level 0-1 (higher = more turbulence) */
  entropy?: number;
  /** Number of particles in the field */
  particleCount?: number;
  /** Size of the field */
  bounds?: number;
  /** Whether field is visible */
  visible?: boolean;
}

/** Particle data structure */
interface ParticleData {
  position: THREE.Vector3;
  velocity: THREE.Vector3;
  basePosition: THREE.Vector3;
  phase: number;
  speed: number;
  size: number;
}

/**
 * Generate initial particle positions
 */
function generateParticles(count: number, bounds: number): ParticleData[] {
  const particles: ParticleData[] = [];
  
  for (let i = 0; i < count; i++) {
    const x = (Math.random() - 0.5) * bounds * 2;
    const y = (Math.random() - 0.5) * bounds * 2;
    const z = (Math.random() - 0.5) * bounds * 2;
    
    particles.push({
      position: new THREE.Vector3(x, y, z),
      velocity: new THREE.Vector3(0, 0, 0),
      basePosition: new THREE.Vector3(x, y, z),
      phase: Math.random() * Math.PI * 2,
      speed: 0.5 + Math.random() * 0.5,
      size: 0.02 + Math.random() * 0.04
    });
  }
  
  return particles;
}

/**
 * Apply turbulence/noise to particle movement
 * Simplex-like noise approximation for chaos
 */
function applyTurbulence(
  position: THREE.Vector3,
  time: number,
  entropy: number,
  phase: number
): THREE.Vector3 {
  const noiseScale = 0.3 + entropy * 0.5;
  const amplitude = entropy * 2;
  const frequency = 1 + entropy * 3;
  
  // Multi-frequency noise approximation
  const nx = Math.sin(position.y * noiseScale + time * frequency + phase) +
             Math.sin(position.z * noiseScale * 2 + time * frequency * 1.5) * 0.5;
  const ny = Math.sin(position.z * noiseScale + time * frequency + phase) +
             Math.sin(position.x * noiseScale * 2 + time * frequency * 1.3) * 0.5;
  const nz = Math.sin(position.x * noiseScale + time * frequency + phase) +
             Math.sin(position.y * noiseScale * 2 + time * frequency * 1.7) * 0.5;
  
  return new THREE.Vector3(
    nx * amplitude,
    ny * amplitude,
    nz * amplitude
  );
}

/**
 * Get color based on entropy level
 * Cyan (low entropy) -> Yellow (medium) -> Red (high entropy)
 */
function getEntropyColor(entropy: number): THREE.Color {
  const color = new THREE.Color();
  
  if (entropy < 0.5) {
    // Cyan to yellow
    color.setHSL(0.5 - entropy * 0.5, 0.8, 0.5);
  } else {
    // Yellow to red
    color.setHSL(0.15 - (entropy - 0.5) * 0.3, 0.9, 0.5);
  }
  
  return color;
}

export const EntropyField: React.FC<EntropyFieldProps> = ({
  entropy = 0.2,
  particleCount = 500,
  bounds = 15,
  visible = true
}) => {
  const pointsRef = useRef<THREE.Points>(null);
  const particlesRef = useRef<ParticleData[]>([]);
  const entropyRef = useRef(entropy);
  
  // Initialize particles
  useEffect(() => {
    particlesRef.current = generateParticles(particleCount, bounds);
  }, [particleCount, bounds]);
  
  // Update entropy ref for smooth transitions
  useEffect(() => {
    entropyRef.current = entropy;
  }, [entropy]);
  
  // Create geometry
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = 0;
      positions[i * 3 + 1] = 0;
      positions[i * 3 + 2] = 0;
      colors[i * 3] = 1;
      colors[i * 3 + 1] = 1;
      colors[i * 3 + 2] = 1;
      sizes[i] = 1;
    }
    
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    
    return geo;
  }, [particleCount]);
  
  // Animation loop
  useFrame((state) => {
    if (!pointsRef.current || !visible) return;
    
    const time = state.clock.elapsedTime;
    const positionAttr = pointsRef.current.geometry.attributes.position;
    const colorAttr = pointsRef.current.geometry.attributes.color;
    const sizeAttr = pointsRef.current.geometry.attributes.size;
    
    if (!positionAttr || !colorAttr || !sizeAttr) return;
    
    const positions = positionAttr.array as Float32Array;
    const colors = colorAttr.array as Float32Array;
    const sizes = sizeAttr.array as Float32Array;
    
    // Smooth entropy transition
    const currentEntropy = entropyRef.current;
    const targetEntropy = entropy;
    entropyRef.current += (targetEntropy - currentEntropy) * 0.05;
    
    const entropyValue = entropyRef.current;
    const baseColor = getEntropyColor(entropyValue);
    
    particlesRef.current.forEach((particle, i) => {
      // Apply turbulence
      const turbulence = applyTurbulence(
        particle.basePosition,
        time,
        entropyValue,
        particle.phase
      );
      
      // Calculate new position with turbulence
      const chaos = entropyValue * 3;
      const order = 1 - entropyValue;
      
      // Drift from base position + turbulence
      const drift = new THREE.Vector3(
        Math.sin(time * particle.speed + particle.phase) * chaos,
        Math.cos(time * particle.speed * 0.7 + particle.phase) * chaos,
        Math.sin(time * particle.speed * 0.5 + particle.phase) * chaos
      );
      
      // Combine order (base position) and chaos (turbulence + drift)
      particle.position.copy(particle.basePosition)
        .multiplyScalar(order)
        .add(turbulence)
        .add(drift);
      
      // Update position attribute
      positions[i * 3] = particle.position.x;
      positions[i * 3 + 1] = particle.position.y;
      positions[i * 3 + 2] = particle.position.z;
      
      // Color shifts with entropy and position
      const positionNoise = Math.sin(particle.position.y * 0.5 + time) * 0.5 + 0.5;
      const colorVariation = entropyValue * positionNoise;
      
      const particleColor = baseColor.clone();
      if (colorVariation > 0.3) {
        // Add some white sparks in high entropy
        particleColor.lerp(new THREE.Color(1, 1, 1), colorVariation * 0.3);
      }
      
      colors[i * 3] = particleColor.r;
      colors[i * 3 + 1] = particleColor.g;
      colors[i * 3 + 2] = particleColor.b;
      
      // Size pulses with entropy
      sizes[i] = particle.size * (1 + entropyValue * Math.sin(time * 3 + particle.phase));
    });
    
    // Mark attributes as needing update
    positionAttr.needsUpdate = true;
    colorAttr.needsUpdate = true;
    sizeAttr.needsUpdate = true;
    
    // Update material opacity based on entropy
    const material = pointsRef.current.material as THREE.PointsMaterial;
    material.opacity = 0.3 + entropyValue * 0.4;
  });
  
  if (!visible) return null;
  
  return (
    <points ref={pointsRef} geometry={geometry}>
      <pointsMaterial
        size={0.05}
        vertexColors
        transparent
        opacity={0.5}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
};

/**
 * EntropyWave - Secondary visualization as waves/rings emanating from center
 */
export const EntropyWave: React.FC<{
  entropy?: number;
  ringCount?: number;
}> = ({ entropy = 0.2, ringCount = 5 }) => {
  const groupRef = useRef<THREE.Group>(null);
  // Ring scales are computed from ring index, no need to track
  
  useFrame((state) => {
    if (!groupRef.current) return;
    
    const time = state.clock.elapsedTime;
    const chaos = entropy * 2;
    
    groupRef.current.children.forEach((child, i) => {
      const mesh = child as THREE.Mesh;
      const baseRadius = (i + 1) * 3;
      const speed = 0.5 + entropy * 1.5;
      
      // Pulsing expansion
      const pulse = Math.sin(time * speed + i * 0.5) * 0.3;
      const radius = baseRadius + pulse + chaos * Math.sin(time * 2 + i);
      
      // Update ring scale
      const scale = radius / baseRadius;
      mesh.scale.setScalar(scale);
      
      // Rotation speed increases with entropy
      mesh.rotation.z = time * (0.1 + entropy * 0.3) * (i % 2 === 0 ? 1 : -1);
      
      // Opacity fades with entropy
      const material = mesh.material as THREE.MeshBasicMaterial;
      material.opacity = (0.3 - i * 0.05) * (1 - entropy * 0.5);
    });
  });
  
  const waveColor = getEntropyColor(entropy);
  
  return (
    <group ref={groupRef} rotation={[Math.PI / 2, 0, 0]}>
      {Array.from({ length: ringCount }).map((_, i) => (
        <mesh key={i} position={[0, 0, i * 0.1 - ringCount * 0.05]}>
          <ringGeometry args={[(i + 1) * 3 - 0.1, (i + 1) * 3 + 0.1, 64]} />
          <meshBasicMaterial
            color={waveColor}
            transparent
            opacity={0.3 - i * 0.05}
            side={THREE.DoubleSide}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      ))}
    </group>
  );
};

export default EntropyField;
