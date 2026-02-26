/**
 * AnimatedGlow Component
 * Glow component with GSAP-powered pulse animation
 * 
 * @phase Phase 3 - Component Integration
 */
import React, { memo, useRef } from 'react';
import type { GlowProps } from '../../types';
import { Glow } from '../ui/Glow';
import { useGlowPulse } from '../../hooks/useAnimation';

export interface AnimatedGlowProps extends GlowProps {
  /** Pulse animation intensity (0-30) */
  pulseIntensity?: number;
  /** Pulse duration in seconds */
  pulseDuration?: number;
  /** Disable pulse animation */
  disablePulse?: boolean;
}

export const AnimatedGlow = memo<AnimatedGlowProps>(function AnimatedGlow({
  pulseIntensity = 10,
  pulseDuration = 2,
  disablePulse = false,
  ...glowProps
}) {
  const glowRef = useRef<HTMLSpanElement>(null);

  // GSAP glow pulse animation
  useGlowPulse(glowRef, {
    color: glowProps.color,
    intensity: disablePulse ? 0 : pulseIntensity,
    duration: pulseDuration,
    disabled: disablePulse,
  });

  return (
    <span ref={glowRef} style={{ display: 'inline-block' }}>
      <Glow {...glowProps} animate={false} />
    </span>
  );
});

export default AnimatedGlow;
