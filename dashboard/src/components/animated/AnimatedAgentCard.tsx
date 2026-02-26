/**
 * AnimatedAgentCard Component
 * AgentCard with GSAP entrance and hover animations
 * 
 * @phase Phase 3 - Component Integration
 */
import React, { memo } from 'react';
import type { AgentCardProps } from '../../types';
import { AgentCard } from '../cards/AgentCard';
import { useEntranceAnimation, useHoverAnimation } from '../../hooks/useAnimation';

export interface AnimatedAgentCardProps extends AgentCardProps {
  /** Animation delay in seconds (for staggered list animations) */
  delay?: number;
  /** Disable animations for this card */
  disableAnimation?: boolean;
  /** Entrance animation type */
  entranceType?: 'fade' | 'slideUp' | 'pop' | 'none';
  /** Hover scale amount (1.0 = no scale) */
  hoverScale?: number;
}

export const AnimatedAgentCard = memo<AnimatedAgentCardProps>(function AnimatedAgentCard({
  delay = 0,
  disableAnimation = false,
  entranceType = 'slideUp',
  hoverScale = 1.02,
  ...agentCardProps
}) {
  // Entrance animation on mount
  const entranceRef = useEntranceAnimation({
    type: disableAnimation ? 'none' : entranceType,
    delay,
    enabled: !disableAnimation,
  });

  // Hover animation
  const { ref: hoverRef, handlers } = useHoverAnimation({
    scale: disableAnimation ? 1 : hoverScale,
    duration: 0.2,
    enabled: !disableAnimation,
  });

  return (
    <div
      ref={(el) => {
        // Merge refs
        (entranceRef as React.MutableRefObject<HTMLElement | null>).current = el;
        (hoverRef as React.MutableRefObject<HTMLElement | null>).current = el;
      }}
      onMouseEnter={handlers.onMouseEnter}
      onMouseLeave={handlers.onMouseLeave}
      style={{ willChange: disableAnimation ? undefined : 'transform, opacity' }}
    >
      <AgentCard {...agentCardProps} />
    </div>
  );
});

export default AnimatedAgentCard;
