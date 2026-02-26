/**
 * AnimatedAgentCard Component
 * AgentCard with GSAP entrance and hover animations
 * 
 * @phase Phase 3 - Component Integration
 */
import React, { memo, useRef } from 'react';
import type { AgentCardProps } from '../../types';
import { AgentCard } from '../cards/AgentCard';
import { useEntranceAnimation, useHoverAnimation } from '../../hooks/useAnimation';

export interface AnimatedAgentCardProps extends AgentCardProps {
  /** Animation delay in seconds (for staggered list animations) */
  delay?: number;
  /** Disable animations for this card */
  disableAnimation?: boolean;
  /** Entrance animation type */
  entranceType?: 'fade' | 'slideUp' | 'slideDown' | 'slideLeft' | 'slideRight' | 'pop' | 'scale';
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
  const cardRef = useRef<HTMLElement>(null);
  
  // Entrance animation on mount
  useEntranceAnimation(cardRef, {
    type: entranceType,
    duration: disableAnimation ? 0 : undefined,
    delay,
    once: true,
  });

  // Hover animation
  const { handlers } = useHoverAnimation({
    scale: disableAnimation ? 1 : hoverScale,
    duration: 0.2,
  });

  return (
    <div
      ref={cardRef as React.RefObject<HTMLDivElement>}
      onMouseEnter={handlers.onMouseEnter}
      onMouseLeave={handlers.onMouseLeave}
      style={{ willChange: disableAnimation ? undefined : 'transform, opacity' }}
    >
      <AgentCard {...agentCardProps} />
    </div>
  );
});

export default AnimatedAgentCard;
