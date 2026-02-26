/**
 * AnimatedGlow Component
 * Glow component with GSAP-powered pulse animation
 * 
 * @phase Phase 3 - Component Integration
 */
import React, { memo } from 'react';
import type { GlowProps } from '../../types';
import { Glow } from '../ui/Glow';
import { useGlowPulse } from '../../hooks/useAnimation';

export interface AnimatedGlowProps extends GlowProps {
  /** Disable pulse animation */
  disablePulse?: boolean;
}

export const AnimatedGlow = memo<AnimatedGlowProps>(function AnimatedGlow({
  disablePulse = false,
  ...glowProps
}) {
  // GSAP glow pulse animation
  const glowRef = useGlowPulse({
    color: glowProps.color || '#00ffd5',
    enabled: !disablePulse && glowProps.animate !== false,
  });

  return (
    <span ref={glowRef as React.RefObject<HTMLSpanElement>} style={{ display: 'inline-block' }}>
      <Glow {...glowProps} animate={false} />
    </span>
  );
});

export default AnimatedGlow;
