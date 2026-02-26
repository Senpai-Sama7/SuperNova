/**
 * Sparkline Component
 * Mini line chart for trend visualization
 */
import React, { memo, useMemo } from 'react';
import type { SparklineProps } from '../../types';
import { Theme } from '../../theme';

export const Sparkline = memo<SparklineProps>(function Sparkline({
  data,
  width = 120,
  height = 30,
  color = Theme.colors.accent,
  strokeWidth = 2,
  showArea = true,
  showDots = false,
}) {
  const pathD = useMemo(() => {
    if (!data || data.length < 2) return '';

    const max = Math.max(...data, 1);
    const min = Math.min(...data, 0);
    const range = max - min || 1;

    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return { x, y };
    });

    return points.reduce((path, point, index) => {
      if (index === 0) return `M ${point.x} ${point.y}`;
      return `${path} L ${point.x} ${point.y}`;
    }, '');
  }, [data, height, width]);

  const areaD = useMemo(() => {
    if (!pathD || !showArea) return '';
    return `${pathD} L ${width} ${height} L 0 ${height} Z`;
  }, [pathD, showArea, height, width]);

  if (!data || data.length < 2) {
    return (
      <svg width={width} height={height} role="img" aria-label="No data available">
        <text x={width / 2} y={height / 2} textAnchor="middle" fill={Theme.colors.textMuted} fontSize="10">
          --
        </text>
      </svg>
    );
  }

  return (
    <svg width={width} height={height} role="img" aria-label={`Trend chart showing ${data.length} data points`}>
      <defs>
        <linearGradient id={`sparkline-gradient-${color.replace('#', '')}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      
      {showArea && areaD && (
        <path
          d={areaD}
          fill={`url(#sparkline-gradient-${color.replace('#', '')})`}
          aria-hidden="true"
        />
      )}
      
      <path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      />
      
      {showDots && data.map((_, index) => {
        const x = (index / (data.length - 1)) * width;
        const max = Math.max(...data, 1);
        const min = Math.min(...data, 0);
        const range = max - min || 1;
        const y = height - ((data[index] - min) / range) * height;
        return (
          <circle
            key={index}
            cx={x}
            cy={y}
            r={2}
            fill={color}
            aria-hidden="true"
          />
        );
      })}
    </svg>
  );
});

export default Sparkline;
