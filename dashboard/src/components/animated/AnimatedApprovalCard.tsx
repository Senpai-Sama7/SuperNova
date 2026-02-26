/**
 * AnimatedApprovalCard Component
 * ApprovalCard with GSAP entrance animation and urgency effects
 * 
 * @phase Phase 3 - Component Integration
 */
import React, { memo } from 'react';
import type { ApprovalCardProps } from '../../types';
import { ApprovalCard } from '../cards/ApprovalCard';
import { useEntranceAnimation, useGlowPulse } from '../../hooks/useAnimation';

export interface AnimatedApprovalCardProps extends ApprovalCardProps {
  /** Animation delay in seconds */
  delay?: number;
  /** Disable animations */
  disableAnimation?: boolean;
  /** Entrance animation type */
  entranceType?: 'fade' | 'slideUp' | 'pop' | 'none';
  /** Glow color for urgent state */
  urgentGlowColor?: string;
  /** Time threshold (seconds) for urgent animation */
  urgentThreshold?: number;
}

export const AnimatedApprovalCard = memo<AnimatedApprovalCardProps>(function AnimatedApprovalCard({
  delay = 0,
  disableAnimation = false,
  entranceType = 'pop',
  urgentGlowColor = '#ef4444',
  urgentThreshold = 30,
  ...approvalCardProps
}) {
  const isUrgent = approvalCardProps.approval.remainingTime < urgentThreshold;

  // Entrance animation
  const entranceRef = useEntranceAnimation({
    type: disableAnimation ? 'none' : entranceType,
    delay,
    enabled: !disableAnimation,
  });

  // Urgency glow pulse for expiring approvals
  const glowRef = useGlowPulse({
    color: urgentGlowColor,
    enabled: !disableAnimation && isUrgent,
  });

  return (
    <div
      ref={(el) => {
        // Merge refs
        (entranceRef as React.MutableRefObject<HTMLElement | null>).current = el;
        (glowRef as React.MutableRefObject<HTMLElement | null>).current = el;
      }}
      style={{ 
        willChange: disableAnimation ? undefined : 'transform, opacity',
        borderRadius: '8px',
      }}
    >
      <ApprovalCard {...approvalCardProps} />
    </div>
  );
});

export default AnimatedApprovalCard;
