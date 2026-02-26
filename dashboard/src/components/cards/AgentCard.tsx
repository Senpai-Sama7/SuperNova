/**
 * AgentCard Component
 * Displays agent status, role, and metrics
 */
import React, { memo, useMemo } from 'react';
import type { AgentCardProps, AgentRole } from '../../types';
import { Theme } from '../../theme';
import { StatusDot } from '../ui/StatusDot';
import { MiniBar } from '../ui/MiniBar';

export const AgentCard = memo<AgentCardProps>(function AgentCard({
  agent,
  onClick,
  selected = false,
  compact = false,
}) {
  const roleIcons: Record<AgentRole, string> = {
    planner: '◈',
    researcher: '◉',
    executor: '◎',
    auditor: '⬡',
    creative: '✦',
  };

  const statusColors: Record<string, string> = {
    active: Theme.colors.accent,
    reasoning: Theme.colors.secondary,
    waiting: Theme.colors.warning,
    idle: Theme.colors.textMuted,
    error: Theme.colors.error,
  };

  const successRateColor = useMemo(() => {
    if (agent.successRate >= 95) return Theme.colors.success;
    if (agent.successRate >= 90) return Theme.colors.warning;
    return Theme.colors.error;
  }, [agent.successRate]);

  const cardStyle: React.CSSProperties = {
    backgroundColor: Theme.colors.surfaceLow,
    border: `1px solid ${selected ? Theme.colors.accent : Theme.colors.border}`,
    borderRadius: '8px',
    padding: compact ? '12px' : '16px',
    cursor: onClick ? 'pointer' : 'default',
    transition: 'all 0.2s ease',
    opacity: agent.status === 'idle' ? 0.7 : 1,
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: compact ? '8px' : '12px',
  };

  const iconStyle: React.CSSProperties = {
    width: compact ? '32px' : '40px',
    height: compact ? '32px' : '40px',
    borderRadius: '8px',
    backgroundColor: `${statusColors[agent.status]}20`,
    color: statusColors[agent.status],
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: compact ? '16px' : '20px',
  };

  const taskStyle: React.CSSProperties = {
    fontSize: compact ? '11px' : '12px',
    color: Theme.colors.textMuted,
    marginTop: '4px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  };

  const metricsStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '8px',
    marginTop: compact ? '8px' : '12px',
    paddingTop: compact ? '8px' : '12px',
    borderTop: `1px solid ${Theme.colors.border}`,
  };

  const metricStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  };

  return (
    <article
      style={cardStyle}
      onClick={() => onClick?.(agent)}
      role="button"
      tabIndex={onClick ? 0 : -1}
      aria-pressed={selected}
      aria-label={`Agent ${agent.name}, ${agent.role}, status ${agent.status}`}
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick(agent);
        }
      }}
    >
      <header style={headerStyle}>
        <span style={iconStyle} aria-hidden="true">
          {roleIcons[agent.role]}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <strong style={{ color: Theme.colors.text, fontSize: compact ? '13px' : '14px' }}>
              {agent.name}
            </strong>
            <StatusDot status={agent.status === 'active' ? 'online' : agent.status === 'error' ? 'error' : 'away'} size="sm" pulse={agent.status === 'active'} />
          </div>
          <div style={{ fontSize: '11px', color: Theme.colors.textMuted, textTransform: 'capitalize' }}>
            {agent.role}
          </div>
        </div>
      </header>

      {agent.task && (
        <div style={taskStyle} title={agent.taskDescription || agent.task}>
          {agent.task}
        </div>
      )}

      <div style={metricsStyle}>
        <div style={metricStyle}>
          <span style={{ fontSize: '10px', color: Theme.colors.textMuted }}>Load</span>
          <MiniBar value={agent.load} color={agent.load > 80 ? Theme.colors.warning : Theme.colors.accent} showValue />
        </div>
        <div style={metricStyle}>
          <span style={{ fontSize: '10px', color: Theme.colors.textMuted }}>Success</span>
          <span style={{ fontSize: '11px', color: successRateColor, fontWeight: 600 }}>
            {agent.successRate.toFixed(1)}%
          </span>
        </div>
      </div>

      {!compact && agent.progress > 0 && (
        <div style={{ marginTop: '10px' }}>
          <MiniBar value={agent.progress} color={Theme.colors.secondary} showValue />
        </div>
      )}
    </article>
  );
});

export default AgentCard;
