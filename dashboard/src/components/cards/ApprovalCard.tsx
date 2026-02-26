/**
 * ApprovalCard Component
 * HITL approval request with countdown timer
 */
import React, { memo, useState, useEffect, useCallback } from 'react';
import type { ApprovalCardProps } from '../../types';
import { Theme } from '../../theme';
import { RiskPill } from '../ui/RiskPill';
import { Badge } from '../ui/Badge';
import { clampPercentage } from '../../utils/numberGuards';

export const ApprovalCard = memo<ApprovalCardProps>(function ApprovalCard({
  approval,
  onDecide,
  compact = false,
}) {
  const [remainingTime, setRemainingTime] = useState(approval.remainingTime);
  const [isDeciding, setIsDeciding] = useState(false);

  useEffect(() => {
    setRemainingTime(approval.remainingTime);
  }, [approval.remainingTime]);

  useEffect(() => {
    if (remainingTime <= 0) return;
    
    const interval = setInterval(() => {
      setRemainingTime((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(interval);
  }, [remainingTime]);

  const handleDecide = useCallback(async (approved: boolean) => {
    setIsDeciding(true);
    try {
      await onDecide(approval.id, approved);
    } finally {
      setIsDeciding(false);
    }
  }, [approval.id, onDecide]);

  const timeProgress = clampPercentage((remainingTime / approval.timeout) * 100);
  const isExpiring = remainingTime < 30;

  const cardStyle: React.CSSProperties = {
    backgroundColor: Theme.colors.surfaceLow,
    border: `1px solid ${Theme.colors.border}`,
    borderRadius: '8px',
    padding: compact ? '12px' : '16px',
    position: 'relative',
    overflow: 'hidden',
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: '12px',
    marginBottom: '12px',
  };

  const actionStyle: React.CSSProperties = {
    fontSize: compact ? '13px' : '14px',
    fontWeight: 600,
    color: Theme.colors.text,
    wordBreak: 'break-word',
  };

  const descriptionStyle: React.CSSProperties = {
    fontSize: '12px',
    color: Theme.colors.textMuted,
    marginBottom: '12px',
    lineHeight: 1.5,
  };

  const footerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '12px',
    flexWrap: 'wrap',
  };

  const timerStyle: React.CSSProperties = {
    fontSize: '11px',
    color: isExpiring ? Theme.colors.error : Theme.colors.textMuted,
    fontWeight: isExpiring ? 600 : 400,
    fontVariantNumeric: 'tabular-nums',
  };

  const buttonsStyle: React.CSSProperties = {
    display: 'flex',
    gap: '8px',
  };

  const buttonBaseStyle: React.CSSProperties = {
    padding: '6px 14px',
    borderRadius: '6px',
    border: 'none',
    fontSize: '12px',
    fontWeight: 600,
    cursor: isDeciding ? 'not-allowed' : 'pointer',
    opacity: isDeciding ? 0.6 : 1,
    transition: 'all 0.2s ease',
  };

  const approveStyle: React.CSSProperties = {
    ...buttonBaseStyle,
    backgroundColor: Theme.colors.success,
    color: '#000',
  };

  const denyStyle: React.CSSProperties = {
    ...buttonBaseStyle,
    backgroundColor: 'transparent',
    color: Theme.colors.error,
    border: `1px solid ${Theme.colors.error}`,
  };

  const progressBarStyle: React.CSSProperties = {
    position: 'absolute',
    bottom: 0,
    left: 0,
    height: '2px',
    width: `${timeProgress}%`,
    backgroundColor: isExpiring ? Theme.colors.error : Theme.colors.accent,
    transition: 'width 1s linear',
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <article style={cardStyle} role="article" aria-label={`Approval request from ${approval.agentName}`}>
      <div style={headerStyle}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ color: Theme.colors.accent, fontSize: '12px' }}>{approval.agentName}</span>
            <RiskPill level={approval.riskLevel} size="sm" />
          </div>
          <h4 style={actionStyle}>{approval.action}</h4>
        </div>
        <Badge variant="info" size="sm">HITL</Badge>
      </div>

      <p style={descriptionStyle}>{approval.description}</p>

      <footer style={footerStyle}>
        <span style={timerStyle} role="timer" aria-label={`Time remaining: ${formatTime(remainingTime)}`}>
          {isExpiring && '⚠️ '}Expires in {formatTime(remainingTime)}
        </span>
        <div style={buttonsStyle} role="group" aria-label="Approval actions">
          <button
            style={approveStyle}
            onClick={() => handleDecide(true)}
            disabled={isDeciding}
            aria-label="Approve action"
          >
            {isDeciding ? '...' : 'Approve'}
          </button>
          <button
            style={denyStyle}
            onClick={() => handleDecide(false)}
            disabled={isDeciding}
            aria-label="Deny action"
          >
            Deny
          </button>
        </div>
      </footer>

      <div style={progressBarStyle} aria-hidden="true" />
    </article>
  );
});

export default ApprovalCard;
