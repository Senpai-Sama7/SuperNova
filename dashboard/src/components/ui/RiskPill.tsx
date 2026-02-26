/**
 * RiskPill Component
 * Risk level indicator with color coding
 */
import React, { memo } from 'react';
import type { RiskPillProps } from '../../types';
import { Theme } from '../../theme';

export const RiskPill = memo<RiskPillProps>(function RiskPill({
  level,
  showLabel = true,
  size = 'md',
}) {
  const riskConfig = {
    low: { color: Theme.colors.accent, label: 'Low Risk' },
    medium: { color: Theme.colors.warning, label: 'Medium Risk' },
    high: { color: Theme.colors.error, label: 'High Risk' },
    critical: { color: Theme.colors.secondary, label: 'Critical Risk' },
  };

  const sizeStyles = {
    sm: { padding: '2px 6px', fontSize: '10px' },
    md: { padding: '3px 8px', fontSize: '11px' },
    lg: { padding: '4px 12px', fontSize: '12px' },
  };

  const config = riskConfig[level];

  const style: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderRadius: '4px',
    backgroundColor: `${config.color}20`,
    color: config.color,
    ...sizeStyles[size],
  };

  const dotStyle: React.CSSProperties = {
    width: size === 'sm' ? 4 : size === 'md' ? 6 : 8,
    height: size === 'sm' ? 4 : size === 'md' ? 6 : 8,
    borderRadius: '50%',
    backgroundColor: config.color,
  };

  return (
    <span style={style} role="status" aria-label={config.label}>
      <span style={dotStyle} aria-hidden="true" />
      {showLabel && config.label}
    </span>
  );
});

export default RiskPill;
