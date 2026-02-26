/**
 * AnimatedMiniBar Component
 * MiniBar with GSAP width and number animations
 * 
 * @phase Phase 3 - Component Integration
 */
import React, { memo, useRef, useEffect, useState } from 'react';
import type { MiniBarProps } from '../../types';
import { MiniBar } from '../ui/MiniBar';
import { gsap } from 'gsap';
import { prefersReducedMotion } from '../../lib/animations';
import { clamp } from '../../utils/numberGuards';

export interface AnimatedMiniBarProps extends MiniBarProps {
  /** Animation duration in seconds */
  duration?: number;
  /** Disable animations */
  disableAnimation?: boolean;
  /** Delay before animation starts */
  delay?: number;
}

export const AnimatedMiniBar = memo<AnimatedMiniBarProps>(function AnimatedMiniBar({
  value,
  max = 100,
  duration = 0.5,
  disableAnimation = false,
  delay = 0,
  ...miniBarProps
}) {
  const fillRef = useRef<HTMLDivElement>(null);
  const [displayValue, setDisplayValue] = useState(0);
  const previousValue = useRef(0);
  
  const isReducedMotion = prefersReducedMotion();
  const shouldAnimate = !disableAnimation && !isReducedMotion;
  const percentage = clamp((value / max) * 100, 0, 100);
  const previousPercentage = clamp((previousValue.current / max) * 100, 0, 100);

  // Animate width
  useEffect(() => {
    if (!fillRef.current || !shouldAnimate) {
      setDisplayValue(percentage);
      return;
    }

    gsap.fromTo(
      fillRef.current,
      { width: `${previousPercentage}%` },
      {
        width: `${percentage}%`,
        duration,
        delay,
        ease: 'power2.out',
      }
    );

    // Animate displayed value
    const valueObj = { val: previousValue.current };
    gsap.to(valueObj, {
      val: value,
      duration,
      delay,
      ease: 'power2.out',
      onUpdate: () => {
        const pct = clamp((valueObj.val / max) * 100, 0, 100);
        setDisplayValue(pct);
      },
    });

    previousValue.current = value;

    return () => {
      gsap.killTweensOf(fillRef.current);
      gsap.killTweensOf(valueObj);
    };
  }, [value, max, duration, delay, shouldAnimate, percentage, previousPercentage]);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%' }}>
      <div
        style={{
          flex: 1,
          height: miniBarProps.height || 4,
          backgroundColor: 'var(--surface-mid)',
          borderRadius: (miniBarProps.height || 4) / 2,
          overflow: 'hidden',
        }}
      >
        <div
          ref={fillRef}
          style={{
            width: shouldAnimate ? `${previousPercentage}%` : `${percentage}%`,
            height: '100%',
            backgroundColor: miniBarProps.color || 'var(--accent)',
            borderRadius: (miniBarProps.height || 4) / 2,
            willChange: shouldAnimate ? 'width' : undefined,
          }}
        />
      </div>
      {miniBarProps.showValue && (
        <span
          style={{
            fontSize: '11px',
            color: 'var(--text-muted)',
            minWidth: '32px',
            textAlign: 'right',
            fontVariantNumeric: 'tabular-nums',
          }}
        >
          {Math.round(displayValue)}%
        </span>
      )}
    </div>
  );
});

export default AnimatedMiniBar;
