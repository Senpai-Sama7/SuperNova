/**
 * Animation React Hooks
 * 
 * Custom hooks for GSAP animations in React components.
 * Provides declarative, type-safe animation control.
 * 
 * @phase Phase 2 - Motion System
 * @author React Hooks Engineer
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { gsap } from 'gsap';
import {
  animateNumber,
  prefersReducedMotion,
  ANIMATION,
  type PerformanceMetrics,
  animationProfiler,
} from '../lib/animations';

// ============================================================================
// USE ANIMATED NUMBER
// ============================================================================

interface UseAnimatedNumberOptions {
  duration?: number;
  formatter?: (value: number) => string;
  decimals?: number;
}

/**
 * Hook for animating number changes
 * @param value - Target number value
 * @param options - Animation options
 * @returns Ref to attach to element and current display value
 * 
 * @example
 * ```tsx
 * const numberRef = useAnimatedNumber(confidence, { decimals: 2 });
 * return <span ref={numberRef}>0</span>;
 * ```
 */
export function useAnimatedNumber(
  value: number,
  options: UseAnimatedNumberOptions = {}
): React.RefObject<HTMLSpanElement | null> {
  const { duration = ANIMATION.duration.emphasis, formatter, decimals = 0 } = options;
  const elementRef = useRef<HTMLSpanElement>(null);
  const previousValue = useRef(value);
  const tweenRef = useRef<gsap.core.Tween | null>(null);

  useEffect(() => {
    if (!elementRef.current) return;
    if (prefersReducedMotion()) {
      elementRef.current.textContent = formatter
        ? formatter(value)
        : value.toFixed(decimals);
      return;
    }

    // Kill previous tween
    if (tweenRef.current) {
      tweenRef.current.kill();
    }

    const from = previousValue.current;
    const to = value;

    tweenRef.current = animateNumber(
      elementRef.current,
      from,
      to,
      duration,
      formatter ?? ((v: number) => v.toFixed(decimals))
    );

    previousValue.current = value;

    return () => {
      tweenRef.current?.kill();
    };
  }, [value, duration, formatter, decimals]);

  return elementRef;
}

// ============================================================================
// USE ENTRANCE ANIMATION
// ============================================================================

type EntranceType = 'fade' | 'slideUp' | 'pop' | 'none';

interface UseEntranceAnimationOptions {
  type?: EntranceType;
  duration?: number;
  delay?: number;
  yOffset?: number;
  enabled?: boolean;
}

/**
 * Hook for entrance animations on mount
 * @param options - Animation options
 * @returns Ref to attach to element
 * 
 * @example
 * ```tsx
 * const cardRef = useEntranceAnimation({ type: 'slideUp', delay: 0.2 });
 * return <div ref={cardRef}>Content</div>;
 * ```
 */
export function useEntranceAnimation(
  options: UseEntranceAnimationOptions = {}
): React.RefObject<HTMLElement | null> {
  const {
    type = 'fade',
    duration = ANIMATION.duration.standard,
    delay = 0,
    yOffset = 30,
    enabled = true,
  } = options;

  const elementRef = useRef<HTMLElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!enabled || !elementRef.current || hasAnimated.current) return;
    if (prefersReducedMotion()) {
      gsap.set(elementRef.current, { opacity: 1, y: 0, scale: 1 });
      return;
    }

    hasAnimated.current = true;

    const element = elementRef.current;

    // Set initial state
    gsap.set(element, { opacity: 0 });
    if (type === 'slideUp') gsap.set(element, { y: yOffset });
    if (type === 'pop') gsap.set(element, { scale: 0.8 });

    // Create entrance animation
    const tl = gsap.timeline({ delay });

    switch (type) {
      case 'fade':
        tl.to(element, { opacity: 1, duration, ease: 'power2.out' });
        break;
      case 'slideUp':
        tl.to(element, { opacity: 1, y: 0, duration, ease: 'power2.out' });
        break;
      case 'pop':
        tl.to(element, {
          opacity: 1,
          scale: 1,
          duration,
          ease: 'back.out(1.7)',
        });
        break;
      case 'none':
        gsap.set(element, { opacity: 1, y: 0, scale: 1 });
        break;
    }

    return () => {
      tl.kill();
    };
  }, [type, duration, delay, yOffset, enabled]);

  return elementRef;
}

// ============================================================================
// USE HOVER ANIMATION
// ============================================================================

interface UseHoverAnimationOptions {
  scale?: number;
  duration?: number;
  enabled?: boolean;
}

/**
 * Hook for hover scale animations
 * @param options - Animation options
 * @returns Ref and event handlers
 * 
 * @example
 * ```tsx
 * const { ref, handlers } = useHoverAnimation({ scale: 1.05 });
 * return <div ref={ref} {...handlers}>Content</div>;
 * ```
 */
export function useHoverAnimation(
  options: UseHoverAnimationOptions = {}
): {
  ref: React.RefObject<HTMLElement | null>;
  handlers: {
    onMouseEnter: () => void;
    onMouseLeave: () => void;
  };
} {
  const { scale = 1.05, duration = ANIMATION.duration.micro, enabled = true } = options;
  const elementRef = useRef<HTMLElement>(null);
  const tweenRef = useRef<gsap.core.Tween | null>(null);

  const onMouseEnter = useCallback(() => {
    if (!enabled || !elementRef.current) return;
    if (prefersReducedMotion()) return;

    if (tweenRef.current) tweenRef.current.kill();
    tweenRef.current = gsap.to(elementRef.current, {
      scale,
      duration,
      ease: 'power2.out',
    });
  }, [scale, duration, enabled]);

  const onMouseLeave = useCallback(() => {
    if (!enabled || !elementRef.current) return;
    if (prefersReducedMotion()) return;

    if (tweenRef.current) tweenRef.current.kill();
    tweenRef.current = gsap.to(elementRef.current, {
      scale: 1,
      duration,
      ease: 'power2.out',
    });
  }, [duration, enabled]);

  useEffect(() => {
    return () => {
      tweenRef.current?.kill();
    };
  }, []);

  return {
    ref: elementRef,
    handlers: {
      onMouseEnter,
      onMouseLeave,
    },
  };
}

// ============================================================================
// USE STAGGER ANIMATION
// ============================================================================

interface UseStaggerAnimationOptions {
  itemSelector: string;
  duration?: number;
  stagger?: number;
  yOffset?: number;
  delay?: number;
  enabled?: boolean;
}

/**
 * Hook for staggered entrance animations on child elements
 * @param options - Animation options
 * @returns Ref to container element
 * 
 * @example
 * ```tsx
 * const containerRef = useStaggerAnimation({ itemSelector: '.card' });
 * return (
 *   <div ref={containerRef}>
 *     {items.map(i => <div key={i} className="card">{i}</div>)}
 *   </div>
 * );
 * ```
 */
export function useStaggerAnimation(
  options: UseStaggerAnimationOptions
): React.RefObject<HTMLElement | null> {
  const {
    itemSelector,
    duration = ANIMATION.duration.standard,
    stagger = ANIMATION.stagger.standard,
    yOffset = 20,
    delay = 0,
    enabled = true,
  } = options;

  const containerRef = useRef<HTMLElement>(null);
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!enabled || !containerRef.current || hasAnimated.current) return;
    if (prefersReducedMotion()) return;

    const items = containerRef.current.querySelectorAll(itemSelector);
    if (items.length === 0) return;

    hasAnimated.current = true;

    gsap.set(items, { opacity: 0, y: yOffset });

    const tl = gsap.timeline({ delay });
    tl.to(items, {
      opacity: 1,
      y: 0,
      duration,
      stagger,
      ease: 'power2.out',
    });

    return () => {
      tl.kill();
    };
  }, [itemSelector, duration, stagger, yOffset, delay, enabled]);

  return containerRef;
}

// ============================================================================
// USE ANIMATION PERFORMANCE
// ============================================================================

/**
 * Hook for monitoring animation performance
 * @returns Performance metrics and control functions
 * 
 * @example
 * ```tsx
 * const { metrics, isPerformanceGood, pause, resume } = useAnimationPerformance();
 * 
 * useEffect(() => {
 *   if (!isPerformanceGood) {
 *     console.warn('Animation performance degraded');
 *   }
 * }, [isPerformanceGood]);
 * ```
 */
export function useAnimationPerformance(): {
  metrics: PerformanceMetrics | null;
  isPerformanceGood: boolean;
  pause: () => void;
  resume: () => void;
} {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    animationProfiler.start();

    intervalRef.current = setInterval(() => {
      setMetrics(animationProfiler.getMetrics());
    }, 1000);

    return () => {
      animationProfiler.stop();
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const pause = useCallback(() => {
    gsap.globalTimeline.pause();
  }, []);

  const resume = useCallback(() => {
    gsap.globalTimeline.resume();
  }, []);

  return {
    metrics,
    isPerformanceGood: animationProfiler.isPerformanceGood(),
    pause,
    resume,
  };
}

// ============================================================================
// USE REDUCED MOTION
// ============================================================================

/**
 * Hook for detecting reduced motion preference
 * @returns Boolean indicating if reduced motion is preferred
 * 
 * @example
 * ```tsx
 * const reducedMotion = useReducedMotion();
 * return (
 *   <motion.div
 *     animate={reducedMotion ? {} : { scale: 1.1 }}
 *   />
 * );
 * ```
 */
export function useReducedMotion(): boolean {
  const [reducedMotion, setReducedMotion] = useState<boolean>(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return reducedMotion;
}

// ============================================================================
// USE GLOW PULSE
// ============================================================================

interface UseGlowPulseOptions {
  color: string;
  enabled?: boolean;
}

/**
 * Hook for glow pulse animation
 * @param options - Animation options
 * @returns Ref to attach to element
 * 
 * @example
 * ```tsx
 * const glowRef = useGlowPulse({ color: '#00ffd5' });
 * return <div ref={glowRef}>Content</div>;
 * ```
 */
export function useGlowPulse(
  options: UseGlowPulseOptions
): React.RefObject<HTMLElement | null> {
  const { color, enabled = true } = options;
  const elementRef = useRef<HTMLElement>(null);
  const tweenRef = useRef<gsap.core.Tween | null>(null);

  useEffect(() => {
    if (!enabled || !elementRef.current) return;
    if (prefersReducedMotion()) return;

    tweenRef.current = gsap.fromTo(
      elementRef.current,
      { boxShadow: `0 0 10px ${color}30` },
      {
        boxShadow: `0 0 30px ${color}60`,
        duration: 1.5,
        ease: 'power1.inOut',
        yoyo: true,
        repeat: -1,
      }
    );

    return () => {
      tweenRef.current?.kill();
    };
  }, [color, enabled]);

  return elementRef;
}

// ============================================================================
// USE EXIT ANIMATION
// ============================================================================

interface UseExitAnimationOptions {
  onExit: () => void;
  duration?: number;
  type?: 'fade' | 'slideDown' | 'scale';
}

/**
 * Hook for exit animations before unmounting
 * @param options - Animation options
 * @returns Trigger function to start exit animation
 * 
 * @example
 * ```tsx
 * const triggerExit = useExitAnimation({ onExit: () => removeItem(id) });
 * return <div onClick={triggerExit}>Click to remove</div>;
 * ```
 */
export function useExitAnimation(
  options: UseExitAnimationOptions
): () => void {
  const { onExit, duration = ANIMATION.duration.fast, type = 'fade' } = options;
  const elementRef = useRef<HTMLElement | null>(null);
  const isExiting = useRef(false);

  const triggerExit = useCallback(() => {
    if (isExiting.current || !elementRef.current) {
      onExit();
      return;
    }

    isExiting.current = true;

    if (prefersReducedMotion()) {
      onExit();
      return;
    }

    const element = elementRef.current;

    const tl = gsap.timeline({
      onComplete: onExit,
    });

    switch (type) {
      case 'fade':
        tl.to(element, { opacity: 0, duration, ease: 'power2.in' });
        break;
      case 'slideDown':
        tl.to(element, { opacity: 0, y: 20, duration, ease: 'power2.in' });
        break;
      case 'scale':
        tl.to(element, { opacity: 0, scale: 0.9, duration, ease: 'power2.in' });
        break;
    }
  }, [onExit, duration, type]);

  return triggerExit;
}
