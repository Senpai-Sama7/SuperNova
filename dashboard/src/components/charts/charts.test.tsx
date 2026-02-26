/**
 * Chart Components Tests
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Sparkline } from './Sparkline';
import { CognitiveCycleRing } from './CognitiveCycleRing';
import { ConfidenceMeter } from './ConfidenceMeter';
import { MemoryGraph } from './MemoryGraph';
import { ConformalBandChart } from './ConformalBandChart';
import type { MemoryGraphData, ConformalBand } from '../../types';

describe('Sparkline', () => {
  it('renders with data', () => {
    render(<Sparkline data={[10, 20, 30, 40, 50]} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('shows no data message when empty', () => {
    render(<Sparkline data={[]} />);
    expect(screen.getByText('--')).toBeInTheDocument();
  });

  it('has accessible label', () => {
    render(<Sparkline data={[1, 2, 3]} />);
    expect(screen.getByRole('img')).toHaveAttribute('aria-label', expect.stringContaining('3 data points'));
  });
});

describe('CognitiveCycleRing', () => {
  it('renders with phase', () => {
    render(<CognitiveCycleRing phase="REASON" progress={50} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('displays phase name', () => {
    render(<CognitiveCycleRing phase="PERCEIVE" progress={25} />);
    expect(screen.getByText('PERCEIVE')).toBeInTheDocument();
  });

  it('displays progress percentage', () => {
    render(<CognitiveCycleRing phase="ACT" progress={75} />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('has accessible label', () => {
    render(<CognitiveCycleRing phase="REFLECT" progress={30} />);
    expect(screen.getByRole('img')).toHaveAttribute('aria-label', expect.stringContaining('REFLECT'));
  });
});

describe('ConfidenceMeter', () => {
  it('renders with value', () => {
    render(<ConfidenceMeter value={75} />);
    expect(screen.getByRole('meter')).toBeInTheDocument();
  });

  it('displays percentage', () => {
    render(<ConfidenceMeter value={82} />);
    expect(screen.getByText('82%')).toBeInTheDocument();
  });

  it('shows PROCEED for high confidence', () => {
    render(<ConfidenceMeter value={85} thresholds={{ proceed: 80, monitor: 50 }} />);
    expect(screen.getByText('PROCEED')).toBeInTheDocument();
  });

  it('shows MONITOR for medium confidence', () => {
    render(<ConfidenceMeter value={65} thresholds={{ proceed: 80, monitor: 50 }} />);
    expect(screen.getByText('MONITOR')).toBeInTheDocument();
  });

  it('shows DEFER for low confidence', () => {
    render(<ConfidenceMeter value={30} thresholds={{ proceed: 80, monitor: 50 }} />);
    expect(screen.getByText('DEFER')).toBeInTheDocument();
  });

  it('has correct ARIA attributes', () => {
    render(<ConfidenceMeter value={60} />);
    const meter = screen.getByRole('meter');
    expect(meter).toHaveAttribute('aria-valuenow', '60');
    expect(meter).toHaveAttribute('aria-valuemin', '0');
    expect(meter).toHaveAttribute('aria-valuemax', '100');
  });
});

describe('MemoryGraph', () => {
  const mockData: MemoryGraphData = {
    nodes: [
      { id: '1', type: 'episodic', label: 'Memory 1', timestamp: new Date().toISOString(), connections: [] },
      { id: '2', type: 'semantic', label: 'Memory 2', timestamp: new Date().toISOString(), connections: [] },
    ],
    edges: [{ source: '1', target: '2', strength: 0.8 }],
  };

  it('renders with nodes', () => {
    render(<MemoryGraph data={mockData} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('shows no data message when empty', () => {
    render(<MemoryGraph data={{ nodes: [], edges: [] }} />);
    expect(screen.getByText('No memory data')).toBeInTheDocument();
  });

  it('has accessible label', () => {
    render(<MemoryGraph data={mockData} />);
    expect(screen.getByRole('img')).toHaveAttribute('aria-label', expect.stringContaining('2 nodes'));
  });

  it('nodes are keyboard accessible', () => {
    render(<MemoryGraph data={mockData} />);
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });
});

describe('ConformalBandChart', () => {
  const mockData: ConformalBand[] = [
    { timestamp: '2024-01-01', lower: 10, upper: 20, actual: 15, coverage: 0.95 },
    { timestamp: '2024-01-02', lower: 12, upper: 22, actual: 18, coverage: 0.95 },
    { timestamp: '2024-01-03', lower: 11, upper: 21, coverage: 0.95 },
  ];

  it('renders with data', () => {
    render(<ConformalBandChart data={mockData} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('shows no data message when empty', () => {
    render(<ConformalBandChart data={[]} />);
    expect(screen.getByText('No prediction data')).toBeInTheDocument();
  });

  it('displays average coverage', () => {
    render(<ConformalBandChart data={mockData} />);
    expect(screen.getByText(/95.0% coverage/i)).toBeInTheDocument();
  });

  it('has accessible label', () => {
    render(<ConformalBandChart data={mockData} />);
    expect(screen.getByRole('img')).toHaveAttribute('aria-label', expect.stringContaining('coverage'));
  });
});
