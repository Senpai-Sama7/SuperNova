/**
 * Transition Wrapper Component
 * 
 * Handles tab/section transitions with GSAP animations.
 * Provides AnimatePresence-like functionality for tab switching.
 * 
 * @phase Phase 2 - Motion System
 */

import React, { useEffect, useRef, useState } from 'react';
import { gsap } from '../lib/animations';
import { prefersReducedMotion, tabEnter, tabExit } from '../lib/animations';

interface TransitionWrapperProps {
  children: React.ReactNode;
  tabId: string;
  direction?: 'left' | 'right' | 'up' | 'down';
  className?: string;
  /** Animation duration in seconds */
  duration?: number;
}

/**
 * TransitionWrapper
 * 
 * Wraps tab content and animates transitions between tabs.
 * Uses GSAP for smooth, performant animations.
 * 
 * @example
 * ```tsx
 * <TransitionWrapper tabId={activeTab} direction="right">
 *   {tabContent}
 * </TransitionWrapper>
 * ```
 */
export const TransitionWrapper: React.FC<TransitionWrapperProps> = ({
  children,
  tabId,
  direction = 'right',
  className = '',
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  duration: _duration = 0.3,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const previousTabId = useRef(tabId);
  const [displayChildren, setDisplayChildren] = useState(children);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    // If tab hasn't changed, just update content without animation
    if (tabId === previousTabId.current) {
      setDisplayChildren(children);
      return;
    }

    if (!containerRef.current) return;

    // Determine animation direction
    const isForward = getTabIndex(tabId) > getTabIndex(previousTabId.current);
    const enterDirection = isForward ? direction : getOppositeDirection(direction);
    const exitDirection = isForward ? getOppositeDirection(direction) : direction;

    if (prefersReducedMotion()) {
      setDisplayChildren(children);
      previousTabId.current = tabId;
      return;
    }

    setIsAnimating(true);

    const element = containerRef.current;

    // Exit animation
    const exitTween = tabExit(element, { direction: exitDirection });

    exitTween.eventCallback('onComplete', () => {
      setDisplayChildren(children);
      previousTabId.current = tabId;

      // Enter animation (next frame to ensure DOM update)
      requestAnimationFrame(() => {
        if (containerRef.current) {
          const enterTween = tabEnter(containerRef.current, {
            direction: enterDirection,
          });
          enterTween.eventCallback('onComplete', () => {
            setIsAnimating(false);
          });
        }
      });
    });

    return () => {
      exitTween.kill();
    };
  }, [tabId, children, direction]);

  // Handle initial mount animation
  useEffect(() => {
    if (!containerRef.current || prefersReducedMotion()) return;

    gsap.fromTo(
      containerRef.current,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.3, ease: 'power2.out' }
    );
  }, []);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        willChange: isAnimating ? 'transform, opacity' : 'auto',
      }}
      aria-live="polite"
      aria-busy={isAnimating}
    >
      {displayChildren}
    </div>
  );
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

const TAB_ORDER = ['overview', 'agents', 'memory', 'decisions'];

function getTabIndex(tabId: string): number {
  return TAB_ORDER.indexOf(tabId);
}

function getOppositeDirection(
  direction: 'left' | 'right' | 'up' | 'down'
): 'left' | 'right' | 'up' | 'down' {
  const opposites: Record<'left' | 'right' | 'up' | 'down', 'left' | 'right' | 'up' | 'down'> = {
    left: 'right',
    right: 'left',
    up: 'down',
    down: 'up',
  };
  return opposites[direction];
}

export default TransitionWrapper;
