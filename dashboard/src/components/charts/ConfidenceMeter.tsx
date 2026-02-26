/**
 * ConfidenceMeter Component
 * Semi-circular gauge for decision confidence
 */
import React, { memo, useMemo } from 'react';
import type { ConfidenceMeterProps } from '../../types';
import { Theme } from '../../theme';
import { clampPercentage } from '../../utils/numberGuards';

export const ConfidenceMeter = memo<ConfidenceMeterProps>(function ConfidenceMeter({
  value,
  size = 120,
  showLabel = true,
  thresholds = { proceed: 80, monitor: 50 },
}) {
  const safeValue = clampPercentage(value);
  
  const decision = useMemo(() => {
    if (safeValue >= thresholds.proceed) {
      return { label: 'PROCEED', color: Theme.colors.success };
    }
    if (safeValue >= thresholds.monitor) {
      return { label: 'MONITOR', color: Theme.colors.warning };
    }
    return { label: 'DEFER', color: Theme.colors.error };
  }, [safeValue, thresholds]);

  const radius = (size - 20) / 2;
  const center = size / 2;
  const circumference = Math.PI * radius;
  const strokeDashoffset = circumference * (1 - safeValue / 100);

  const containerStyle: React.CSSProperties = {
    position: 'relative',
    width: size,
    height: size / 2 + 20,
  };

  const centerLabelStyle: React.CSSProperties = {
    position: 'absolute',
    bottom: '10px',
    left: '50%',
    transform: 'translateX(-50%)',
    textAlign: 'center',
  };

  return (
    <div style={containerStyle} role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={safeValue} aria-label={`Confidence: ${safeValue.toFixed(0)}%, ${decision.label}`}>
      <svg width={size} height={size / 2 + 10} aria-hidden="true">
        {/* Background arc */}
        <path
          d={`M 10 ${center} A ${radius} ${radius} 0 0 1 ${size - 10} ${center}`}
          fill="none"
          stroke={Theme.colors.surfaceMid}
          strokeWidth="10"
          strokeLinecap="round"
        />
        
        {/* Value arc */}
        <path
          d={`M 10 ${center} A ${radius} ${radius} 0 0 1 ${size - 10} ${center}`}
          fill="none"
          stroke={decision.color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />

        {/* Tick marks */}
        {[0, 25, 50, 75, 100].map((tick) => {
          const angle = (tick / 100) * 180 - 180;
          const rad = (angle * Math.PI) / 180;
          const x1 = center + (radius - 15) * Math.cos(rad);
          const y1 = center + (radius - 15) * Math.sin(rad);
          const x2 = center + (radius - 5) * Math.cos(rad);
          const y2 = center + (radius - 5) * Math.sin(rad);
          
          return (
            <line
              key={tick}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={Theme.colors.textMuted}
              strokeWidth="1"
            />
          );
        })}
      </svg>

      {showLabel && (
        <div style={centerLabelStyle}>
          <div style={{ fontSize: '18px', fontWeight: 700, color: decision.color }}>
            {safeValue.toFixed(0)}%
          </div>
          <div style={{ fontSize: '10px', color: Theme.colors.textMuted, fontWeight: 600 }}>
            {decision.label}
          </div>
        </div>
      )}
    </div>
  );
});

export default ConfidenceMeter;
