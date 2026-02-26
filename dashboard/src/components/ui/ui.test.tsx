/**
 * UI Components Tests
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Glow } from './Glow';
import { Badge } from './Badge';
import { StatusDot } from './StatusDot';
import { MiniBar } from './MiniBar';
import { RiskPill } from './RiskPill';

describe('Glow', () => {
  it('renders children correctly', () => {
    render(<Glow>Test Content</Glow>);
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<Glow className="custom-class">Content</Glow>);
    expect(screen.getByText('Content')).toHaveClass('custom-class');
  });
});

describe('Badge', () => {
  it('renders children correctly', () => {
    render(<Badge>Test Badge</Badge>);
    expect(screen.getByText('Test Badge')).toBeInTheDocument();
  });

  it('has correct role', () => {
    render(<Badge>Status</Badge>);
    expect(screen.getByRole('status')).toHaveTextContent('Status');
  });

  it('renders different variants', () => {
    const { rerender } = render(<Badge variant="success">Success</Badge>);
    expect(screen.getByText('Success')).toBeInTheDocument();
    
    rerender(<Badge variant="error">Error</Badge>);
    expect(screen.getByText('Error')).toBeInTheDocument();
    
    rerender(<Badge variant="warning">Warning</Badge>);
    expect(screen.getByText('Warning')).toBeInTheDocument();
  });
});

describe('StatusDot', () => {
  it('renders with online status', () => {
    render(<StatusDot status="online" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<StatusDot status="online" label="Connected" />);
    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  it('has accessible label', () => {
    render(<StatusDot status="offline" />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'offline status');
  });

  it('renders all status types', () => {
    const statuses = ['online', 'offline', 'busy', 'away', 'error'] as const;
    statuses.forEach(status => {
      const { unmount } = render(<StatusDot status={status} />);
      expect(screen.getByRole('status')).toBeInTheDocument();
      unmount();
    });
  });
});

describe('MiniBar', () => {
  it('renders progress bar', () => {
    render(<MiniBar value={50} />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('has correct ARIA attributes', () => {
    render(<MiniBar value={75} max={100} />);
    const bar = screen.getByRole('progressbar');
    expect(bar).toHaveAttribute('aria-valuenow', '75');
    expect(bar).toHaveAttribute('aria-valuemax', '100');
  });

  it('displays value when showValue is true', () => {
    render(<MiniBar value={42} showValue />);
    expect(screen.getByText('42%')).toBeInTheDocument();
  });

  it('does not display value when showValue is false', () => {
    render(<MiniBar value={42} showValue={false} />);
    expect(screen.queryByText('42%')).not.toBeInTheDocument();
  });

  it('clamps value to 0-100 range', () => {
    render(<MiniBar value={150} showValue />);
    expect(screen.getByText('100%')).toBeInTheDocument();
    
    render(<MiniBar value={-20} showValue />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });
});

describe('RiskPill', () => {
  it('renders all risk levels', () => {
    const levels = ['low', 'medium', 'high', 'critical'] as const;
    levels.forEach(level => {
      const { unmount } = render(<RiskPill level={level} />);
      expect(screen.getByRole('status')).toBeInTheDocument();
      unmount();
    });
  });

  it('displays label by default', () => {
    render(<RiskPill level="high" />);
    expect(screen.getByText('High Risk')).toBeInTheDocument();
  });

  it('hides label when showLabel is false', () => {
    render(<RiskPill level="high" showLabel={false} />);
    expect(screen.queryByText('High Risk')).not.toBeInTheDocument();
  });

  it('has accessible label', () => {
    render(<RiskPill level="critical" />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Critical Risk');
  });
});
