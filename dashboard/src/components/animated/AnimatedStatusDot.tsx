/**
 * AnimatedStatusDot Component
 * StatusDot with GSAP-enhanced pulse animation
 * 
 * @phase Phase 3 - Component Integration
 */
import React, { memo, useRef } from 'react';
import type { StatusDotProps } from '../../types';
import { StatusDot } from '../ui/StatusDot';
import { useGlowPulse } from '../../hooks/useAnimation';
import { Theme } from '../../theme';

export interface AnimatedStatusDotProps extends StatusDotProps {
  /** Pulse animation intensity (0-20) */
  pulseIntensity?: number;
  /** Pulse duration in seconds */
  pulseDuration?: number;
  /** Disable GSAP pulse (fallback to CSS) */
  disableAnimation?: boolean;
}

const statusColors: Record<string, string> = {
  online: Theme.colors.success,
  offline: Theme.colors.textMuted,
  busy: Theme.colors.error,
  away: Theme.colors.warning,
  error: Theme.colors.error,
};

export const AnimatedStatusDot = memo<AnimatedStatusDotProps>(function AnimatedStatusDot({
  pulseIntensity = 8,
  pulseDuration = 2,
  disableAnimation = false,
  ...statusDotProps
}) {
  const dotRef = useRef<HTMLSpanElement>(null);
  const color = statusColors[statusDotProps.status] || Theme.colors.textMuted;

  // GSAP pulse animation (only when pulse is enabled and not disabled)
  useGlowPulse(dotRef, {
    color,
    intensity: disableAnimation || !statusDotProps.pulse ? 0 : pulseIntensity,
    duration: pulseDuration,
    disabled: disableAnimation || !statusDotProps.pulse,
  });

  return (
    <span ref={dotRef} style={{ display: 'inline-flex' }}>
      <StatusDot {...statusDotProps} pulse={false} />
    </span>
  );
});

export default AnimatedStatusDot;
