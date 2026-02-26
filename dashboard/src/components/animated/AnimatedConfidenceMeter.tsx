/**
 * AnimatedConfidenceMeter Component
 * ConfidenceMeter with GSAP number animation and arc transitions
 * 
 * @phase Phase 3 - Component Integration
 */
import React, { memo, useRef, useEffect, useState } from 'react';
import type { ConfidenceMeterProps } from '../../types';
import { ConfidenceMeter } from '../charts/ConfidenceMeter';
import { useAnimatedNumber } from '../../hooks/useAnimation';
import { gsap } from 'gsap';
import { prefersReducedMotion, clamp } from '../../lib/animations';

export interface AnimatedConfidenceMeterProps extends ConfidenceMeterProps {
  /** Animation duration in seconds */
  duration?: number;
  /** Disable animations */
  disableAnimation?: boolean;
  /** Delay before animation starts */
  delay?: number;
}

export const AnimatedConfidenceMeter = memo<AnimatedConfidenceMeterProps>(function AnimatedConfidenceMeter({
  value,
  duration = 0.8,
  disableAnimation = false,
  delay = 0,
  ...confidenceMeterProps
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const arcRef = useRef<SVGPathElement>(null);
  const [displayValue, setDisplayValue] = useState(0);
  const previousValue = useRef(0);
  
  const isReducedMotion = prefersReducedMotion();
  const shouldAnimate = !disableAnimation && !isReducedMotion;

  // Animate the number value
  const numberRef = useAnimatedNumber(value, {
    duration: shouldAnimate ? duration : 0,
    decimals: 0,
  });

  // Animate arc stroke-dashoffset
  useEffect(() => {
    if (!arcRef.current || !shouldAnimate) {
      setDisplayValue(value);
      return;
    }

    const radius = (confidenceMeterProps.size || 120 - 20) / 2;
    const circumference = Math.PI * radius;
    const startOffset = circumference * (1 - previousValue.current / 100);
    const endOffset = circumference * (1 - value / 100);

    gsap.fromTo(
      arcRef.current,
      { strokeDashoffset: startOffset },
      {
        strokeDashoffset: endOffset,
        duration,
        delay,
        ease: 'power2.out',
      }
    );

    // Animate the displayed value
    const valueObj = { val: previousValue.current };
    gsap.to(valueObj, {
      val: value,
      duration,
      delay,
      ease: 'power2.out',
      onUpdate: () => setDisplayValue(valueObj.val),
    });

    previousValue.current = value;

    return () => {
      gsap.killTweensOf(arcRef.current);
      gsap.killTweensOf(valueObj);
    };
  }, [value, duration, delay, shouldAnimate, confidenceMeterProps.size]);

  // Entrance animation
  useEffect(() => {
    if (!containerRef.current || !shouldAnimate) return;

    gsap.fromTo(
      containerRef.current,
      { opacity: 0, scale: 0.9 },
      {
        opacity: 1,
        scale: 1,
        duration: 0.4,
        delay,
        ease: 'back.out(1.7)',
      }
    );
  }, [delay, shouldAnimate]);

  return (
    <div ref={containerRef} style={{ willChange: shouldAnimate ? 'transform, opacity' : undefined }}>
      <ConfidenceMeter
        {...confidenceMeterProps}
        value={displayValue}
      />
    </div>
  );
});

export default AnimatedConfidenceMeter;
