/**
 * GSAP Animation Configuration & Utilities
 * 
 * Centralized animation system for Neural Constellation Dashboard.
 * Provides type-safe GSAP integration with performance optimization.
 * 
 * @phase Phase 2 - Motion System
 * @author Animation Architect
 */

import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

// ============================================================================
// PLUGIN REGISTRATION
// ============================================================================

// Register GSAP plugins (only in browser)
if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Clamp a value between min and max
 */
export const clamp = (value: number, min: number, max: number): number => {
  return Math.min(Math.max(value, min), max);
};

// ============================================================================
// ANIMATION CONSTANTS
// ============================================================================

export const ANIMATION = {
  duration: {
    instant: 0.15,
    micro: 0.15,
    fast: 0.2,
    standard: 0.3,
    emphasis: 0.5,
    slow: 0.8,
    dramatic: 1.2,
  },
  ease: {
    standard: 'power2.out',
    enter: 'power2.out',
    exit: 'power2.in',
    bounce: 'back.out(1.7)',
    spring: 'elastic.out(1, 0.5)',
    smooth: 'power3.inOut',
    linear: 'none',
  },
  stagger: {
    fast: 0.03,
    standard: 0.05,
    slow: 0.1,
    cascade: 0.08,
  },
} as const;

// ============================================================================
// PERFORMANCE MONITORING
// ============================================================================

interface PerformanceMetrics {
  activeAnimations: number;
  totalAnimations: number;
  averageFrameTime: number;
  droppedFrames: number;
}

class AnimationProfiler {
  private metrics: PerformanceMetrics = {
    activeAnimations: 0,
    totalAnimations: 0,
    averageFrameTime: 0,
    droppedFrames: 0,
  };

  private rafId: number | null = null;
  private lastTime = 0;
  private frameTimes: number[] = [];

  start(): void {
    if (typeof window === 'undefined') return;
    this.lastTime = performance.now();
    this.monitorFrameRate();
  }

  stop(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
    }
  }

  private monitorFrameRate = (): void => {
    const currentTime = performance.now();
    const frameTime = currentTime - this.lastTime;
    this.lastTime = currentTime;

    this.frameTimes.push(frameTime);
    if (this.frameTimes.length > 60) {
      this.frameTimes.shift();
    }

    const avgFrameTime = this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
    this.metrics.averageFrameTime = avgFrameTime;
    this.metrics.droppedFrames = this.frameTimes.filter(t => t > 16.67).length;

    this.rafId = requestAnimationFrame(this.monitorFrameRate);
  };

  trackAnimationStart(): void {
    this.metrics.activeAnimations++;
    this.metrics.totalAnimations++;
  }

  trackAnimationComplete(): void {
    this.metrics.activeAnimations = Math.max(0, this.metrics.activeAnimations - 1);
  }

  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  isPerformanceGood(): boolean {
    return this.metrics.averageFrameTime < 16.67 && this.metrics.droppedFrames < 5;
  }
}

export const animationProfiler = new AnimationProfiler();

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Check if reduced motion preference is enabled
 */
export const prefersReducedMotion = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/**
 * Get animation duration respecting reduced motion
 */
export const getSafeDuration = (duration: number): number => {
  return prefersReducedMotion() ? 0 : duration;
};

/**
 * Create a GSAP timeline with defaults
 */
export const createTimeline = (
  defaults?: gsap.TimelineVars
): gsap.core.Timeline => {
  const safeDefaults = prefersReducedMotion()
    ? { duration: 0, ...defaults }
    : defaults;

  return gsap.timeline({
    defaults: {
      ease: ANIMATION.ease.standard,
      duration: ANIMATION.duration.standard,
      ...safeDefaults,
    },
  });
};

// ============================================================================
// ENTRANCE ANIMATIONS
// ============================================================================

/**
 * Fade in animation
 */
export const fadeIn = (
  element: gsap.TweenTarget,
  duration = ANIMATION.duration.standard
): gsap.core.Tween => {
  const safeDuration = getSafeDuration(duration);
  
  return gsap.fromTo(
    element,
    { opacity: 0 },
    { 
      opacity: 1, 
      duration: safeDuration,
      ease: ANIMATION.ease.enter,
      onStart: () => animationProfiler.trackAnimationStart(),
      onComplete: () => animationProfiler.trackAnimationComplete(),
    }
  );
};

/**
 * Slide up and fade in
 */
export const slideUpFadeIn = (
  element: gsap.TweenTarget,
  duration = ANIMATION.duration.standard,
  yOffset = 30
): gsap.core.Tween => {
  const safeDuration = getSafeDuration(duration);
  
  return gsap.fromTo(
    element,
    { opacity: 0, y: yOffset },
    {
      opacity: 1,
      y: 0,
      duration: safeDuration,
      ease: ANIMATION.ease.enter,
      onStart: () => animationProfiler.trackAnimationStart(),
      onComplete: () => animationProfiler.trackAnimationComplete(),
    }
  );
};

/**
 * Scale and fade in (pop effect)
 */
export const popIn = (
  element: gsap.TweenTarget,
  duration = ANIMATION.duration.emphasis
): gsap.core.Tween => {
  const safeDuration = getSafeDuration(duration);
  
  return gsap.fromTo(
    element,
    { opacity: 0, scale: 0.8 },
    {
      opacity: 1,
      scale: 1,
      duration: safeDuration,
      ease: ANIMATION.ease.bounce,
      onStart: () => animationProfiler.trackAnimationStart(),
      onComplete: () => animationProfiler.trackAnimationComplete(),
    }
  );
};

/**
 * Staggered entrance for multiple elements
 */
export const staggerEntrance = (
  elements: gsap.TweenTarget,
  options: {
    duration?: number;
    stagger?: number;
    yOffset?: number;
    from?: 'start' | 'center' | 'end';
  } = {}
): gsap.core.Timeline => {
  const {
    duration = ANIMATION.duration.standard,
    stagger = ANIMATION.stagger.standard,
    yOffset = 20,
    from = 'start',
  } = options;

  const safeDuration = getSafeDuration(duration);
  
  const tl = createTimeline();
  
  tl.fromTo(
    elements,
    { opacity: 0, y: yOffset },
    {
      opacity: 1,
      y: 0,
      duration: safeDuration,
      stagger: {
        each: stagger,
        from,
      },
      ease: ANIMATION.ease.enter,
    }
  );

  return tl;
};

// ============================================================================
// EXIT ANIMATIONS
// ============================================================================

/**
 * Fade out
 */
export const fadeOut = (
  element: gsap.TweenTarget,
  duration = ANIMATION.duration.fast
): gsap.core.Tween => {
  const safeDuration = getSafeDuration(duration);
  
  return gsap.to(element, {
    opacity: 0,
    duration: safeDuration,
    ease: ANIMATION.ease.exit,
    onStart: () => animationProfiler.trackAnimationStart(),
    onComplete: () => animationProfiler.trackAnimationComplete(),
  });
};

/**
 * Slide down and fade out
 */
export const slideDownFadeOut = (
  element: gsap.TweenTarget,
  duration = ANIMATION.duration.fast,
  yOffset = 20
): gsap.core.Tween => {
  const safeDuration = getSafeDuration(duration);
  
  return gsap.to(element, {
    opacity: 0,
    y: yOffset,
    duration: safeDuration,
    ease: ANIMATION.ease.exit,
    onStart: () => animationProfiler.trackAnimationStart(),
    onComplete: () => animationProfiler.trackAnimationComplete(),
  });
};

/**
 * Scale down and fade out
 */
export const scaleOut = (
  element: gsap.TweenTarget,
  duration = ANIMATION.duration.fast
): gsap.core.Tween => {
  const safeDuration = getSafeDuration(duration);
  
  return gsap.to(element, {
    opacity: 0,
    scale: 0.9,
    duration: safeDuration,
    ease: ANIMATION.ease.exit,
    onStart: () => animationProfiler.trackAnimationStart(),
    onComplete: () => animationProfiler.trackAnimationComplete(),
  });
};

// ============================================================================
// INTERACTION ANIMATIONS
// ============================================================================

/**
 * Hover scale effect
 */
export const hoverScale = (
  element: HTMLElement,
  scale = 1.05
): gsap.core.Tween => {
  if (prefersReducedMotion()) return gsap.to(element, { duration: 0 });
  
  return gsap.to(element, {
    scale,
    duration: ANIMATION.duration.micro,
    ease: ANIMATION.ease.standard,
  });
};

/**
 * Glow pulse animation
 */
export const glowPulse = (
  element: gsap.TweenTarget,
  color: string
): gsap.core.Tween => {
  if (prefersReducedMotion()) return gsap.to(element, { duration: 0 });
  
  return gsap.fromTo(
    element,
    { boxShadow: `0 0 10px ${color}30` },
    {
      boxShadow: `0 0 30px ${color}60`,
      duration: 1.5,
      ease: 'power1.inOut',
      yoyo: true,
      repeat: -1,
    }
  );
};

/**
 * Number counting animation
 */
export const animateNumber = (
  element: HTMLElement,
  from: number,
  to: number,
  duration: number = ANIMATION.duration.emphasis,
  formatter?: (value: number) => string
): gsap.core.Tween => {
  const safeDuration = getSafeDuration(duration);
  const obj = { value: from };

  return gsap.to(obj, {
    value: to,
    duration: safeDuration,
    ease: ANIMATION.ease.standard,
    onUpdate: () => {
      const formatted = formatter
        ? formatter(obj.value)
        : Math.round(obj.value).toString();
      element.textContent = formatted;
    },
    onStart: () => animationProfiler.trackAnimationStart(),
    onComplete: () => animationProfiler.trackAnimationComplete(),
  });
};

// ============================================================================
// TAB TRANSITIONS
// ============================================================================

interface TabTransitionOptions {
  direction?: 'left' | 'right' | 'up' | 'down';
  duration?: number;
}

/**
 * Tab exit animation
 */
export const tabExit = (
  element: gsap.TweenTarget,
  options: TabTransitionOptions = {}
): gsap.core.Tween => {
  const { direction = 'left', duration = ANIMATION.duration.standard } = options;
  const safeDuration = getSafeDuration(duration);

  const xOffset = direction === 'left' ? -50 : direction === 'right' ? 50 : 0;
  const yOffset = direction === 'up' ? -50 : direction === 'down' ? 50 : 0;

  return gsap.to(element, {
    opacity: 0,
    x: xOffset,
    y: yOffset,
    scale: 0.95,
    duration: safeDuration,
    ease: ANIMATION.ease.exit,
    onStart: () => animationProfiler.trackAnimationStart(),
    onComplete: () => animationProfiler.trackAnimationComplete(),
  });
};

/**
 * Tab enter animation
 */
export const tabEnter = (
  element: gsap.TweenTarget,
  options: TabTransitionOptions = {}
): gsap.core.Tween => {
  const { direction = 'right', duration = ANIMATION.duration.standard } = options;
  const safeDuration = getSafeDuration(duration);

  const xOffset = direction === 'left' ? 50 : direction === 'right' ? -50 : 0;
  const yOffset = direction === 'up' ? 50 : direction === 'down' ? -50 : 0;

  return gsap.fromTo(
    element,
    { opacity: 0, x: xOffset, y: yOffset, scale: 0.95 },
    {
      opacity: 1,
      x: 0,
      y: 0,
      scale: 1,
      duration: safeDuration,
      ease: ANIMATION.ease.enter,
      onStart: () => animationProfiler.trackAnimationStart(),
      onComplete: () => animationProfiler.trackAnimationComplete(),
    }
  );
};

// ============================================================================
// SCROLL ANIMATIONS
// ============================================================================

/**
 * Create scroll-triggered animation
 */
export const createScrollTrigger = (
  element: HTMLElement,
  animation: gsap.TweenVars,
  triggerOptions?: ScrollTrigger.Vars
): ScrollTrigger | null => {
  if (prefersReducedMotion()) {
    gsap.set(element, { opacity: 1, y: 0 });
    return null;
  }

  return ScrollTrigger.create({
    trigger: element,
    start: 'top 80%',
    end: 'bottom 20%',
    toggleActions: 'play none none reverse',
    ...triggerOptions,
    animation: gsap.fromTo(element, { opacity: 0, y: 30 }, {
      opacity: 1,
      y: 0,
      duration: ANIMATION.duration.standard,
      ease: ANIMATION.ease.enter,
      ...animation,
    }),
  });
};

// ============================================================================
// REACT INTEGRATION
// ============================================================================

/**
 * Cleanup all GSAP animations for a component
 */
export const cleanupAnimations = (context: gsap.Context): void => {
  context.revert();
};

/**
 * Pause all animations (for performance or user preference)
 */
export const pauseAllAnimations = (): void => {
  gsap.globalTimeline.pause();
};

/**
 * Resume all animations
 */
export const resumeAllAnimations = (): void => {
  gsap.globalTimeline.resume();
};

// ============================================================================
// EXPORTS
// ============================================================================

export { gsap, ScrollTrigger };
export type { PerformanceMetrics };
