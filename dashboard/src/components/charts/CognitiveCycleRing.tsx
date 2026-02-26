/**
 * CognitiveCycleRing Component
 * Visualizes the 6-phase cognitive loop
 */
import React, { memo, useMemo } from 'react';
import type { CognitiveCycleRingProps, CognitivePhase } from '../../types';
import { Theme } from '../../theme';

const PHASES: CognitivePhase[] = [
  'PERCEIVE',
  'REMEMBER',
  'REASON',
  'ACT',
  'REFLECT',
  'CONSOLIDATE',
];

export const CognitiveCycleRing = memo<CognitiveCycleRingProps & { mcpToolName?: string }>(function CognitiveCycleRing({
  phase,
  progress,
  size = 200,
  showLabels = true,
  mcpToolName,
}) {
  const center = size / 2;
  const radius = (size - 40) / 2;
  const strokeWidth = 8;
  const circumference = 2 * Math.PI * radius;
  const segmentLength = circumference / 6;
  const gap = 4;

  const currentPhaseIndex = PHASES.indexOf(phase);

  const getSegmentColor = useMemo(() => (index: number): string => {
    if (index === currentPhaseIndex) return Theme.colors.accent;
    if (index < currentPhaseIndex) return Theme.colors.success;
    return Theme.colors.surfaceMid;
  }, [currentPhaseIndex]);

  const getSegmentOffset = (index: number): number => {
    return index * segmentLength + gap * index;
  };

  const labelPositions = useMemo(() => {
    return PHASES.map((_, index) => {
      const angle = (index * 60 - 90) * (Math.PI / 180);
      const labelRadius = radius + 25;
      return {
        x: center + labelRadius * Math.cos(angle),
        y: center + labelRadius * Math.sin(angle),
      };
    });
  }, [center, radius]);

  const containerStyle: React.CSSProperties = {
    position: 'relative',
    width: size,
    height: size,
  };

  const centerLabelStyle: React.CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    textAlign: 'center',
  };

  return (
    <div style={containerStyle} role="img" aria-label={`Cognitive cycle: ${phase}, ${progress.toFixed(0)}% complete`}>
      <svg width={size} height={size} aria-hidden="true">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background ring */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={Theme.colors.surfaceMid}
          strokeWidth={strokeWidth}
          opacity={0.3}
        />

        {/* Phase segments */}
        {PHASES.map((phaseName, index) => (
          <circle
            key={phaseName}
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={getSegmentColor(index)}
            strokeWidth={strokeWidth}
            strokeDasharray={`${segmentLength - gap} ${circumference - segmentLength + gap}`}
            strokeDashoffset={-getSegmentOffset(index)}
            strokeLinecap="round"
            filter={index === currentPhaseIndex ? 'url(#glow)' : undefined}
            style={{
              transition: 'all 0.3s ease',
              opacity: index === currentPhaseIndex ? 1 : index < currentPhaseIndex ? 0.7 : 0.4,
            }}
          />
        ))}

        {/* Progress indicator on current phase */}
        {currentPhaseIndex >= 0 && (
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={Theme.colors.accent}
            strokeWidth={strokeWidth + 2}
            strokeDasharray={`${(segmentLength - gap) * (progress / 100)} ${circumference}`}
            strokeDashoffset={-getSegmentOffset(currentPhaseIndex)}
            strokeLinecap="round"
            filter="url(#glow)"
            opacity={0.8}
          />
        )}

        {/* Phase labels */}
        {showLabels && labelPositions.map((pos, index) => pos && PHASES[index] && (
          <text
            key={PHASES[index]}
            x={pos.x}
            y={pos.y}
            textAnchor="middle"
            dominantBaseline="middle"
            fill={index === currentPhaseIndex ? Theme.colors.accent : Theme.colors.textMuted}
            fontSize="9"
            fontWeight={index === currentPhaseIndex ? 600 : 400}
            style={{ fontFamily: Theme.fonts.mono }}
          >
            {PHASES[index].slice(0, 3)}
          </text>
        ))}
      </svg>

      <div style={centerLabelStyle}>
        <div style={{ fontSize: '14px', fontWeight: 700, color: Theme.colors.accent }}>
          {phase}
        </div>
        <div style={{ fontSize: '11px', color: Theme.colors.textMuted }}>
          {progress.toFixed(0)}%
        </div>
        {mcpToolName && phase === 'ACT' && (
          <div style={{ fontSize: '9px', color: Theme.colors.secondary, marginTop: '2px', fontFamily: Theme.fonts.mono }}>
            🔧 {mcpToolName}
          </div>
        )}
      </div>
    </div>
  );
});

export default CognitiveCycleRing;
