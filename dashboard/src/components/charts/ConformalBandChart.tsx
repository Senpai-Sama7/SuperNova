/**
 * ConformalBandChart Component
 * Uncertainty quantification visualization with prediction bands
 */
import { memo, useMemo } from 'react';
import type { ConformalBandChartProps } from '../../types';
import { Theme } from '../../theme';

export const ConformalBandChart = memo<ConformalBandChartProps>(function ConformalBandChart({
  data,
  width = 400,
  height = 200,
  showActual = true,
}) {
  const padding = { top: 20, right: 30, bottom: 30, left: 40 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const { xScale, yScale, yMin, yMax } = useMemo(() => {
    if (!data.length) {
      return { xScale: () => 0, yScale: () => 0, yMin: 0, yMax: 1 };
    }

    const allValues = data.flatMap(d => [d.lower, d.upper, ...(showActual && d.actual !== undefined ? [d.actual] : [])]);
    const yMin = Math.min(...allValues) * 0.95;
    const yMax = Math.max(...allValues) * 1.05;

    return {
      xScale: (index: number) => (index / Math.max(data.length - 1, 1)) * chartWidth,
      yScale: (value: number) => chartHeight - ((value - yMin) / (yMax - yMin)) * chartHeight,
      yMin,
      yMax,
    };
  }, [data, chartHeight, chartWidth, showActual]);

  const bandPath = useMemo(() => {
    if (!data.length) return '';

    const upperPath = data.map((d, i) => {
      const x = xScale(i);
      const y = yScale(d.upper);
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(' ');

    const lowerPath = data.map((_, i) => {
      const dataPoint = data[data.length - 1 - i];
      if (!dataPoint) return '';
      const x = xScale(data.length - 1 - i);
      const y = yScale(dataPoint.lower);
      return `L ${x} ${y}`;
    }).filter(Boolean).join(' ');

    return `${upperPath} ${lowerPath} Z`;
  }, [data, xScale, yScale]);

  const actualPath = useMemo(() => {
    if (!showActual) return '';
    return data
      .filter(d => d.actual !== undefined)
      .map((d, i) => {
        const x = xScale(i);
        const y = yScale(d.actual!);
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  }, [data, showActual, xScale, yScale]);

  if (!data.length) {
    return (
      <svg width={width} height={height} role="img" aria-label="No conformal prediction data">
        <text x={width / 2} y={height / 2} textAnchor="middle" fill={Theme.colors.textMuted} fontSize="12">
          No prediction data
        </text>
      </svg>
    );
  }

  const averageCoverage = data.reduce((sum, d) => sum + d.coverage, 0) / data.length;

  return (
    <svg width={width} height={height} role="img" aria-label={`Conformal prediction bands with ${(averageCoverage * 100).toFixed(1)}% coverage`}>
      <defs>
        <linearGradient id="bandGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={Theme.colors.accent} stopOpacity="0.3" />
          <stop offset="100%" stopColor={Theme.colors.accent} stopOpacity="0.1" />
        </linearGradient>
      </defs>

      <g transform={`translate(${padding.left}, ${padding.top})`}>
        {/* Y-axis */}
        <g aria-hidden="true">
          {[0, 0.25, 0.5, 0.75, 1].map((tick) => {
            const y = yScale(yMin + (yMax - yMin) * tick);
            return (
              <g key={tick}>
                <line
                  x1={0}
                  y1={y}
                  x2={chartWidth}
                  y2={y}
                  stroke={Theme.colors.border}
                  strokeDasharray="2 2"
                  opacity={0.5}
                />
                <text
                  x={-8}
                  y={y + 3}
                  textAnchor="end"
                  fill={Theme.colors.textMuted}
                  fontSize="9"
                >
                  {(yMin + (yMax - yMin) * tick).toFixed(1)}
                </text>
              </g>
            );
          })}
        </g>

        {/* Prediction band */}
        <path
          d={bandPath}
          fill="url(#bandGradient)"
          stroke={Theme.colors.accent}
          strokeWidth={1}
          opacity={0.6}
          aria-hidden="true"
        />

        {/* Actual values */}
        {showActual && actualPath && (
          <path
            d={actualPath}
            fill="none"
            stroke={Theme.colors.success}
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          />
        )}

        {/* Coverage indicator */}
        <text
          x={chartWidth}
          y={-5}
          textAnchor="end"
          fill={Theme.colors.accent}
          fontSize="10"
          fontWeight={600}
        >
          {(averageCoverage * 100).toFixed(1)}% coverage
        </text>
      </g>
    </svg>
  );
});

export default ConformalBandChart;
