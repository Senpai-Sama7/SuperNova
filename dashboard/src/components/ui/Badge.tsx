/**
 * Badge Component
 * Status and category badges with variant support
 */
import React, { memo } from 'react';
import type { BadgeProps } from '../../types';
import { Theme } from '../../theme';

export const Badge = memo<BadgeProps>(function Badge({
  children,
  variant = 'default',
  size = 'md',
  className = '',
}) {
  const variantColors: Record<string, React.CSSProperties> = {
    default: {
      backgroundColor: Theme.colors.surfaceMid,
      color: Theme.colors.text,
    },
    success: {
      backgroundColor: 'rgba(52, 211, 153, 0.2)',
      color: Theme.colors.success,
    },
    warning: {
      backgroundColor: 'rgba(251, 191, 36, 0.2)',
      color: Theme.colors.warning,
    },
    error: {
      backgroundColor: 'rgba(248, 113, 113, 0.2)',
      color: Theme.colors.error,
    },
    info: {
      backgroundColor: 'rgba(56, 189, 248, 0.2)',
      color: Theme.colors.info,
    },
  };

  const sizeStyles: Record<string, React.CSSProperties> = {
    sm: {
      padding: '2px 6px',
      fontSize: '10px',
      borderRadius: '4px',
    },
    md: {
      padding: '4px 10px',
      fontSize: '12px',
      borderRadius: '6px',
    },
    lg: {
      padding: '6px 14px',
      fontSize: '14px',
      borderRadius: '8px',
    },
  };

  const style: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    fontWeight: 500,
    ...variantColors[variant],
    ...sizeStyles[size],
  };

  return (
    <span className={className} style={style} role="status">
      {children}
    </span>
  );
});

export default Badge;
