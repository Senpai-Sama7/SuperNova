/**
 * Glow Component
 * Adds animated glow effect to child elements
 */
import React, { memo } from 'react';
import type { GlowProps } from '../../types';
import { Theme } from '../../theme';

export const Glow = memo<GlowProps>(function Glow({
  children,
  color = Theme.colors.accent,
  intensity = 'medium',
  className = '',
  animate = true,
}) {
  const intensityMap = {
    low: '0 0 10px',
    medium: '0 0 20px',
    high: '0 0 40px',
  };

  const glowStyle: React.CSSProperties = {
    filter: `${intensityMap[intensity]} ${color}`,
    transition: animate ? 'filter 0.3s ease' : undefined,
  };

  return (
    <span className={className} style={glowStyle}>
      {children}
    </span>
  );
});

export default Glow;
