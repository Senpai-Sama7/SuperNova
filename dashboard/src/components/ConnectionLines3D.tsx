/**
 * ConnectionLines3D - Neural Pathway Visualization
 * 
 * Renders glowing connections between related memory nodes
 * using efficient LineSegments for performance.
 * 
 * @author Geometry Engineering Team
 * @phase Phase 4 - 3D Memory Space
 */

import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

/** Connection data structure */
interface Connection {
  from: [number, number, number];
  to: [number, number, number];
  strength: number;
}

/** Props for ConnectionLines3D */
interface ConnectionLines3DProps {
  connections: Connection[];
  maxConnections?: number;
}

/** Maximum number of connections to render (performance limit) */
const DEFAULT_MAX_CONNECTIONS = 100;

export const ConnectionLines3D: React.FC<ConnectionLines3DProps> = ({
  connections,
  maxConnections = DEFAULT_MAX_CONNECTIONS
}) => {
  const linesRef = useRef<THREE.LineSegments>(null);
  const glowRef = useRef<THREE.LineSegments>(null);
  
  // Limit connections for performance
  const visibleConnections = useMemo(() => {
    return connections.slice(0, maxConnections);
  }, [connections, maxConnections]);

  // Build geometry from connections
  const { geometry, glowGeometry } = useMemo(() => {
    const positions: number[] = [];
    const colors: number[] = [];
    const glowPositions: number[] = [];
    
    visibleConnections.forEach(conn => {
      const [x1, y1, z1] = conn.from;
      const [x2, y2, z2] = conn.to;
      
      // Main line
      positions.push(x1, y1, z1, x2, y2, z2);
      
      // Color based on strength (cyan to purple gradient)
      const r = 0;
      const g = 1 * conn.strength;
      const b = 0.8 + (0.3 * (1 - conn.strength));
      colors.push(r, g, b, r, g, b);
      
      // Glow line (slightly offset for bloom effect)
      glowPositions.push(x1, y1, z1, x2, y2, z2);
    });
    
    // Main lines geometry
    const mainGeo = new THREE.BufferGeometry();
    mainGeo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    mainGeo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    
    // Glow lines geometry (wider, more transparent)
    const glowGeo = new THREE.BufferGeometry();
    glowGeo.setAttribute('position', new THREE.Float32BufferAttribute(glowPositions, 3));
    
    return { geometry: mainGeo, glowGeometry: glowGeo };
  }, [visibleConnections]);

  // Animate pulse effect
  useFrame((state) => {
    if (!linesRef.current || !glowRef.current) return;
    
    const time = state.clock.elapsedTime;
    
    // Pulse opacity
    const pulse = 0.5 + Math.sin(time * 2) * 0.3;
    
    // Update main line opacity
    const mainMaterial = linesRef.current.material as THREE.LineBasicMaterial;
    mainMaterial.opacity = 0.4 + pulse * 0.3;
    
    // Update glow line opacity
    const glowMaterial = glowRef.current.material as THREE.LineBasicMaterial;
    glowMaterial.opacity = 0.1 + pulse * 0.15;
  });

  // Don't render if no connections
  if (visibleConnections.length === 0) return null;

  return (
    <group>
      {/* Main connection lines */}
      <lineSegments ref={linesRef} geometry={geometry}>
        <lineBasicMaterial
          vertexColors
          transparent
          opacity={0.6}
          linewidth={2}
          blending={THREE.AdditiveBlending}
        />
      </lineSegments>
      
      {/* Glow effect lines */}
      <lineSegments ref={glowRef} geometry={glowGeometry}>
        <lineBasicMaterial
          color="#00ffd5"
          transparent
          opacity={0.2}
          linewidth={4}
          blending={THREE.AdditiveBlending}
        />
      </lineSegments>
      
      {/* Particle flow along connections (optional visual enhancement) */}
      <ConnectionParticles connections={visibleConnections} />
    </group>
  );
};

/** Animated particles flowing along connections */
const ConnectionParticles: React.FC<{ connections: Connection[] }> = ({ connections }) => {
  const particlesRef = useRef<THREE.Points>(null);
  
  // Create particle positions along connection lines
  const particleGeometry = useMemo(() => {
    const positions: number[] = [];
    const speeds: number[] = [];
    
    connections.forEach((conn, index) => {
      const [x1, y1, z1] = conn.from;
      const [x2, y2, z2] = conn.to;
      
      // Add 2-3 particles per connection
      const particleCount = Math.max(1, Math.floor(conn.strength * 3));
      
      for (let i = 0; i < particleCount; i++) {
        const t = Math.random();
        const x = x1 + (x2 - x1) * t;
        const y = y1 + (y2 - y1) * t;
        const z = z1 + (z2 - z1) * t;
        
        positions.push(x, y, z);
        speeds.push(index + i * 0.5); // Offset animation per particle
      }
    });
    
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geo.setAttribute('speed', new THREE.Float32BufferAttribute(speeds, 1));
    
    return geo;
  }, [connections]);

  // Animate particles flowing along connections
  useFrame((state) => {
    if (!particlesRef.current || connections.length === 0) return;
    
    const positionAttr = particlesRef.current.geometry.attributes.position;
    const speedAttr = particlesRef.current.geometry.attributes.speed;
    if (!positionAttr || !speedAttr) return;
    
    const positions = positionAttr.array as Float32Array;
    const speeds = speedAttr.array as Float32Array;
    const time = state.clock.elapsedTime;
    
    let posIndex = 0;
    connections.forEach((conn) => {
      const [x1, y1, z1] = conn.from;
      const [x2, y2, z2] = conn.to;
      const particleCount = Math.max(1, Math.floor(conn.strength * 3));
      
      for (let i = 0; i < particleCount; i++) {
        // Flow animation
        const speed = speeds[posIndex] || 1;
        const t = (time * 0.5 * conn.strength + speed * 0.3) % 1;
        
        positions[posIndex * 3] = x1 + (x2 - x1) * t;
        positions[posIndex * 3 + 1] = y1 + (y2 - y1) * t;
        positions[posIndex * 3 + 2] = z1 + (z2 - z1) * t;
        
        posIndex++;
      }
    });
    
    positionAttr.needsUpdate = true;
  });

  if (connections.length === 0) return null;

  return (
    <points ref={particlesRef} geometry={particleGeometry}>
      <pointsMaterial
        color="#00ffd5"
        size={0.08}
        transparent
        opacity={0.8}
        blending={THREE.AdditiveBlending}
        sizeAttenuation
      />
    </points>
  );
};

export default ConnectionLines3D;
