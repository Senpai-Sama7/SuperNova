/**
 * AdaptiveLighting - Dynamic Lighting Based on Agent State
 * 
 * Adjusts scene lighting based on confidence metrics and cognitive state.
 * - High confidence: Bright, stable cyan lighting
 * - Low confidence: Dim, shifting purple/red tones
 * - High entropy: Chaotic, flickering effects
 * 
 * @author Phase 5 - Adaptive Atmosphere
 */

import React, { useRef, useMemo, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

/** Lighting state configuration */
interface LightingState {
  ambientColor: string;
  ambientIntensity: number;
  mainColor: string;
  mainIntensity: number;
  accentColor: string;
  accentIntensity: number;
  fogDensity: number;
  fogColor: string;
}

/** Props for AdaptiveLighting */
interface AdaptiveLightingProps {
  /** Confidence level 0-1 (higher = brighter, more stable) */
  confidence?: number;
  /** Entropy level 0-1 (higher = more chaos/flicker) */
  entropy?: number;
  /** Cognitive phase affecting lighting mood */
  cognitivePhase?: 'PERCEIVE' | 'REMEMBER' | 'REASON' | 'ACT' | 'REFLECT' | 'CONSOLIDATE';
  /** Agent status affecting base lighting */
  agentStatus?: 'active' | 'reasoning' | 'waiting' | 'idle' | 'error';
}

/** Phase-specific lighting adjustments */
const PHASE_MODIFIERS: Record<string, { intensity: number; hue: number }> = {
  PERCEIVE: { intensity: 1.0, hue: 0 },      // Neutral
  REMEMBER: { intensity: 0.9, hue: -20 },    // Slightly warmer
  REASON: { intensity: 1.2, hue: 0 },        // Brighter
  ACT: { intensity: 1.3, hue: 10 },          // Warm, energetic
  REFLECT: { intensity: 0.7, hue: -30 },     // Dim, introspective
  CONSOLIDATE: { intensity: 0.8, hue: 0 }    // Calm
};

/**
 * Calculate lighting state based on confidence and entropy
 */
function calculateLightingState(
  confidence: number,
  entropy: number,
  phase: AdaptiveLightingProps['cognitivePhase'],
  status: AdaptiveLightingProps['agentStatus']
): LightingState {
  // Determine colors based on confidence and status
  let ambientColor = '#5b21b6';   // Purple
  let mainColor = '#60a5fa';      // Blue
  let accentColor = '#fbbf24';    // Amber
  let fogColor = '#0f0a1a';       // Dark purple
  
  if (status === 'error') {
    ambientColor = '#450a0a';     // Dark red
    mainColor = '#dc2626';        // Red
    accentColor = '#f87171';      // Light red
    fogColor = '#1f0a0a';         // Dark red fog
  } else if (confidence > 0.7) {
    ambientColor = '#4c1d95';     // Deep purple
    mainColor = '#00ffd5';        // Cyan
    accentColor = '#f472b6';      // Pink
    fogColor = '#0a0a0f';         // Dark
  } else if (confidence < 0.4) {
    ambientColor = '#7c3aed';     // Bright purple
    mainColor = '#f59e0b';        // Orange (uncertainty)
    accentColor = '#ef4444';      // Red (warning)
    fogColor = '#1a0a0f';         // Dark red
  }

  // Base intensities
  let ambientIntensity = 0.3 + (confidence * 0.2);
  let mainIntensity = 1.0 + (confidence * 0.5);
  let accentIntensity = 0.6 + (confidence * 0.3);
  
  // Apply phase modifier
  const phaseMod = phase ? PHASE_MODIFIERS[phase] : { intensity: 1, hue: 0 };
  ambientIntensity *= phaseMod.intensity;
  mainIntensity *= phaseMod.intensity;
  
  // Entropy affects stability (higher entropy = more variation)
  const entropyVariation = 1 + (entropy * 0.5);
  mainIntensity *= entropyVariation;
  
  // Fog density increases with entropy (more obscured)
  const fogDensity = 0.02 + (entropy * 0.03);
  
  // Fog color shifts with confidence
  const finalFogColor = confidence < 0.3 
    ? '#2a0a0a'  // Red tint when uncertain
    : fogColor;

  return {
    ambientColor,
    ambientIntensity,
    mainColor,
    mainIntensity,
    accentColor,
    accentIntensity,
    fogDensity,
    fogColor: finalFogColor
  };
}

export const AdaptiveLighting: React.FC<AdaptiveLightingProps> = ({
  confidence = 0.7,
  entropy = 0.2,
  cognitivePhase = 'PERCEIVE',
  agentStatus = 'active'
}) => {
  const ambientRef = useRef<THREE.AmbientLight>(null);
  const mainRef = useRef<THREE.PointLight>(null);
  const accentRef = useRef<THREE.PointLight>(null);
  const rimRef = useRef<THREE.DirectionalLight>(null);
  const { scene } = useThree();
  
  // Calculate target lighting state
  const targetState = useMemo(() => 
    calculateLightingState(confidence, entropy, cognitivePhase, agentStatus),
    [confidence, entropy, cognitivePhase, agentStatus]
  );
  
  // Current state for smooth interpolation
  const currentState = useRef({
    ambientIntensity: targetState.ambientIntensity,
    mainIntensity: targetState.mainIntensity,
    accentIntensity: targetState.accentIntensity,
    fogDensity: targetState.fogDensity,
    flickerOffset: Math.random() * 100
  });

  // Update fog on mount
  useEffect(() => {
    if (scene.fog instanceof THREE.FogExp2) {
      scene.fog.color.set(targetState.fogColor);
    }
  }, [scene.fog, targetState.fogColor]);

  useFrame((state) => {
    const time = state.clock.elapsedTime;
    const flicker = currentState.current.flickerOffset;
    
    // Entropy-driven flicker effect
    const flickerIntensity = entropy > 0.5 
      ? Math.sin(time * (5 + entropy * 10) + flicker) * entropy * 0.2
      : 0;
    
    // Smooth interpolation factor
    const lerpFactor = 0.05;
    
    // Interpolate current state toward target
    currentState.current.ambientIntensity += 
      (targetState.ambientIntensity - currentState.current.ambientIntensity) * lerpFactor;
    currentState.current.mainIntensity += 
      (targetState.mainIntensity - currentState.current.mainIntensity) * lerpFactor;
    currentState.current.accentIntensity += 
      (targetState.accentIntensity - currentState.current.accentIntensity) * lerpFactor;
    currentState.current.fogDensity += 
      (targetState.fogDensity - currentState.current.fogDensity) * lerpFactor;
    
    // Apply flicker to main intensity
    const finalMainIntensity = currentState.current.mainIntensity + flickerIntensity;
    
    // Update lights
    if (ambientRef.current) {
      ambientRef.current.intensity = currentState.current.ambientIntensity;
      ambientRef.current.color.set(targetState.ambientColor);
    }
    
    if (mainRef.current) {
      mainRef.current.intensity = Math.max(0.1, finalMainIntensity);
      mainRef.current.color.set(targetState.mainColor);
      
      // Main light pulses with entropy
      if (entropy > 0.3) {
        const pulse = Math.sin(time * (1 + entropy * 2)) * 0.2;
        mainRef.current.position.x = 10 + pulse * 2;
        mainRef.current.position.z = 10 + Math.cos(time * 0.5) * pulse;
      }
    }
    
    if (accentRef.current) {
      accentRef.current.intensity = currentState.current.accentIntensity;
      accentRef.current.color.set(targetState.accentColor);
    }
    
    // Update rim light based on confidence
    if (rimRef.current) {
      rimRef.current.intensity = 0.3 + confidence * 0.4;
      // Rim light gets more dramatic with high entropy
      if (entropy > 0.6) {
        rimRef.current.position.x = Math.sin(time * 0.5) * 5;
      }
    }
    
    // Update fog
    if (scene.fog instanceof THREE.FogExp2) {
      scene.fog.density = currentState.current.fogDensity;
      scene.fog.color.set(targetState.fogColor);
    }
  });

  return (
    <>
      {/* Ambient lighting - base atmosphere */}
      <ambientLight
        ref={ambientRef}
        intensity={targetState.ambientIntensity}
        color={targetState.ambientColor}
      />
      
      {/* Main point light - confidence indicator */}
      <pointLight
        ref={mainRef}
        position={[10, 10, 10]}
        intensity={targetState.mainIntensity}
        color={targetState.mainColor}
        distance={60}
        decay={2}
      />
      
      {/* Accent light - secondary color */}
      <pointLight
        ref={accentRef}
        position={[-10, -10, -5]}
        intensity={targetState.accentIntensity}
        color={targetState.accentColor}
        distance={50}
        decay={2}
      />
      
      {/* Rim light for edge definition */}
      <directionalLight
        ref={rimRef}
        position={[0, 10, 0]}
        intensity={0.5}
        color="#ffffff"
      />
    </>
  );
};

export default AdaptiveLighting;
