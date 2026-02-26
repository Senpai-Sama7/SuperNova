/**
 * MiniBar Component
 * Compact progress bar for metric visualization
 */
import React, { memo } from 'react';
import type { MiniBarProps } from '../../types';
import { Theme } from '../../theme';
import { clampPercentage } from '../../utils/numberGuards';

export const MiniBar = memo<MiniBarProps>(function MiniBar({
  value,
  max = 100,
  color = Theme.colors.accent,
  height = 4,
  showValue = false,
  className = '',
}) {
  const percentage = clampPercentage((value / max) * 100);

  const containerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    width: '100%',
  };

  const trackStyle: React.CSSProperties = {
    flex: 1,
    height,
    backgroundColor: Theme.colors.surfaceMid,
    borderRadius: height / 2,
    overflow: 'hidden',
  };

  const fillStyle: React.CSSProperties = {
    width: `${percentage}%`,
    height: '100%',
    backgroundColor: color,
    borderRadius: height / 2,
    transition: 'width 0.3s ease',
  };

  return (
    <div className={className} style={containerStyle} role="progressbar" aria-valuenow={value} aria-valuemax={max}>
      <div style={trackStyle}>
        <div style={fillStyle} />
      </div>
      {showValue && (
        <span style={{ fontSize: '11px', color: Theme.colors.textMuted, minWidth: '32px', textAlign: 'right' }}>
          {Math.round(percentage)}%
        </span>
      )}
    </div>
  );
});

export default MiniBar;
