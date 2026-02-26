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
import { useFrame } from '@react-three/fiber';
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

/** Color palettes for different states */
const COLOR_PALETTES = {
  highConfidence: {
    ambient: '#4c1d95',   // Deep purple
    main: '#00ffd5',      // Cyan
    accent: '#f472b6',    // Pink
    fog: '#0a0a0f'
  },
  mediumConfidence: {
    ambient: '#5b21b6',   // Purple
    main: '#60a5fa',      // Blue
    accent: '#fbbf24',    // Amber
    fog: '#0f0a1a'
  },
  lowConfidence: {
    ambient: '#7c3aed',   // Bright purple
    main: '#f59e0b',      // Orange (uncertainty)
    accent: '#ef4444',    // Red (warning)
    fog: '#1a0a0f'
  },
  error: {
    ambient: '#450a0a',   // Dark red
    main: '#dc2626',      // Red
    accent: '#f87171',    // Light red
    fog: '#1f0a0a'
  }
} as const;

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
 * Interpolate between colors
 */
function lerpColor(color1: string, color2: string, t: number): string {
  const c1 = new THREE.Color(color1);
  const c2 = new THREE.Color(color2);
  return c1.lerp(c2, t).getStyle();
}

/**
 * Calculate lighting state based on confidence and entropy
 */
function calculateLightingState(
  confidence: number,
  entropy: number,
  phase: AdaptiveLightingProps['cognitivePhase'],
  status: AdaptiveLightingProps['agentStatus']
): LightingState {
  // Determine base palette
  let palette = COLOR_PALETTES.mediumConfidence;
  if (status === 'error') {
    palette = COLOR_PALETTES.error;
  } else if (confidence > 0.7) {
    palette = COLOR_PALETTES.highConfidence;
  } else if (confidence < 0.4) {
    palette = COLOR_PALETTES.lowConfidence;
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
  const fogColor = confidence < 0.3 
    ? lerpColor(palette.fog, '#2a0a0a', 0.5)  // Red tint when uncertain
    : palette.fog;

  return {
    ambientColor: palette.ambient,
    ambientIntensity,
    mainColor: palette.main,
    mainIntensity,
    accentColor: palette.accent,
    accentIntensity,
    fogDensity,
    fogColor
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

  // Update fog on mount and when state changes
  useEffect(() => {
    // This runs in the React lifecycle, safe for scene access
  }, [targetState.fogColor, targetState.fogDensity]);

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
    const scene = state.scene;
    if (scene.fog && scene.fog instanceof THREE.FogExp2) {
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
