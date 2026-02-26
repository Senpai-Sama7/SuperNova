/**
 * AnimatedConfidenceMeter Component
 * ConfidenceMeter with GSAP number animation and arc transitions
 * 
 * @phase Phase 3 - Component Integration
 */
import { useRef, useEffect, useState } from 'react';
import type { ConfidenceMeterProps } from '../../types';
import { ConfidenceMeter } from '../charts/ConfidenceMeter';
import { gsap } from 'gsap';
import { prefersReducedMotion } from '../../lib/animations';

export interface AnimatedConfidenceMeterProps extends ConfidenceMeterProps {
  /** Animation duration in seconds */
  duration?: number;
  /** Disable animations */
  disableAnimation?: boolean;
  /** Delay before animation starts */
  delay?: number;
}

export const AnimatedConfidenceMeter = function AnimatedConfidenceMeter({
  value,
  duration = 0.8,
  disableAnimation = false,
  delay = 0,
  ...confidenceMeterProps
}: AnimatedConfidenceMeterProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement>(null);
  const [displayValue, setDisplayValue] = useState(0);
  const previousValue = useRef(0);
  
  const isReducedMotion = prefersReducedMotion();
  const shouldAnimate = !disableAnimation && !isReducedMotion;

  // Animate the displayed value
  useEffect(() => {
    if (!shouldAnimate) {
      setDisplayValue(value);
      previousValue.current = value;
      return;
    }

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
      gsap.killTweensOf(valueObj);
    };
  }, [value, duration, delay, shouldAnimate]);

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
};

export default AnimatedConfidenceMeter;
