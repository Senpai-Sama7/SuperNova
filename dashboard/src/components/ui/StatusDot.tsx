/**
 * StatusDot Component
 * Visual indicator for online/offline/busy status
 */
import React, { memo } from 'react';
import type { StatusDotProps } from '../../types';
import { Theme } from '../../theme';

export const StatusDot = memo<StatusDotProps>(function StatusDot({
  status,
  size = 'md',
  pulse = true,
  label,
}) {
  const statusColors: Record<string, string> = {
    online: Theme.colors.success,
    offline: Theme.colors.textMuted,
    busy: Theme.colors.error,
    away: Theme.colors.warning,
    error: Theme.colors.error,
  };

  const sizeMap = {
    sm: 6,
    md: 10,
    lg: 14,
  };

  const dotSize = sizeMap[size];
  const color = statusColors[status] || Theme.colors.textMuted;

  const dotStyle: React.CSSProperties = {
    width: dotSize,
    height: dotSize,
    borderRadius: '50%',
    backgroundColor: color,
    boxShadow: pulse ? `0 0 ${dotSize}px ${color}` : undefined,
    animation: pulse ? 'pulse 2s infinite' : undefined,
  };

  const containerStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
  };

  return (
    <span style={containerStyle} role="status" aria-label={label || `${status} status`}>
      <span style={dotStyle} aria-hidden="true" />
      {label && (
        <span style={{ fontSize: '12px', color: Theme.colors.textMuted }}>{label}</span>
      )}
    </span>
  );
});

export default StatusDot;
