/**
 * AnimatedStatusDot Component
 * StatusDot with GSAP-enhanced pulse animation
 * 
 * @phase Phase 3 - Component Integration
 */
import React, { memo } from 'react';
import type { StatusDotProps } from '../../types';
import { StatusDot } from '../ui/StatusDot';
import { useGlowPulse } from '../../hooks/useAnimation';
import { Theme } from '../../theme';

export interface AnimatedStatusDotProps extends StatusDotProps {
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
  disableAnimation = false,
  ...statusDotProps
}) {
  const color = statusColors[statusDotProps.status] || Theme.colors.textMuted;

  // GSAP pulse animation (only when pulse is enabled and not disabled)
  const pulseRef = useGlowPulse({
    color,
    enabled: !disableAnimation && !!statusDotProps.pulse,
  });

  return (
    <span ref={pulseRef as React.RefObject<HTMLSpanElement>} style={{ display: 'inline-flex' }}>
      <StatusDot {...statusDotProps} pulse={false} />
    </span>
  );
});

export default AnimatedStatusDot;
