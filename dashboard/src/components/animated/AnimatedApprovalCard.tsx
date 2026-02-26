/**
 * AnimatedApprovalCard Component
 * ApprovalCard with GSAP entrance animation and urgency effects
 * 
 * @phase Phase 3 - Component Integration
 */
import React, { memo, useRef } from 'react';
import type { ApprovalCardProps } from '../../types';
import { ApprovalCard } from '../cards/ApprovalCard';
import { useEntranceAnimation, useGlowPulse } from '../../hooks/useAnimation';

export interface AnimatedApprovalCardProps extends ApprovalCardProps {
  /** Animation delay in seconds */
  delay?: number;
  /** Disable animations */
  disableAnimation?: boolean;
  /** Entrance animation type */
  entranceType?: 'fade' | 'slideUp' | 'slideDown' | 'slideLeft' | 'slideRight' | 'pop' | 'scale';
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
  const cardRef = useRef<HTMLElement>(null);
  const isUrgent = approvalCardProps.approval.remainingTime < urgentThreshold;

  // Entrance animation
  useEntranceAnimation(cardRef, {
    type: entranceType,
    duration: disableAnimation ? 0 : undefined,
    delay,
    once: true,
  });

  // Urgency glow pulse for expiring approvals
  useGlowPulse(cardRef, {
    color: urgentGlowColor,
    intensity: isUrgent ? 15 : 0,
    duration: 1.5,
    disabled: disableAnimation || !isUrgent,
  });

  return (
    <div
      ref={cardRef as React.RefObject<HTMLDivElement>}
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
