/**
 * Card Components Tests
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AgentCard } from './AgentCard';
import { ApprovalCard } from './ApprovalCard';
import type { Agent, ApprovalRequest } from '../../types';

const mockAgent: Agent = {
  id: 'agent-1',
  name: 'Test Agent',
  role: 'planner',
  status: 'active',
  task: 'Processing data',
  taskDescription: 'Processing some test data',
  progress: 50,
  load: 75,
  successRate: 95,
  lastActive: new Date().toISOString(),
};

const mockApproval: ApprovalRequest = {
  id: 'approval-1',
  agentId: 'agent-1',
  agentName: 'Test Agent',
  action: 'Delete file',
  description: 'Delete the temporary file',
  riskLevel: 'medium',
  timestamp: new Date().toISOString(),
  timeout: 120,
  remainingTime: 60,
};

describe('AgentCard', () => {
  it('renders agent information', () => {
    render(<AgentCard agent={mockAgent} />);
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText('Processing data')).toBeInTheDocument();
  });

  it('renders in compact mode', () => {
    render(<AgentCard agent={mockAgent} compact />);
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });

  it('shows selected state', () => {
    render(<AgentCard agent={mockAgent} selected />);
    // Card should have visual indication of selection
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn();
    render(<AgentCard agent={mockAgent} onClick={handleClick} />);
    
    await userEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledWith(mockAgent);
  });

  it('has correct ARIA attributes', () => {
    render(<AgentCard agent={mockAgent} />);
    const card = screen.getByRole('article');
    expect(card).toHaveAttribute('aria-label', expect.stringContaining('Test Agent'));
  });

  it('is keyboard accessible', async () => {
    const handleClick = vi.fn();
    render(<AgentCard agent={mockAgent} onClick={handleClick} />);
    
    const card = screen.getByRole('button');
    card.focus();
    await userEvent.keyboard('{Enter}');
    expect(handleClick).toHaveBeenCalled();
  });
});

describe('ApprovalCard', () => {
  it('renders approval information', () => {
    render(<ApprovalCard approval={mockApproval} onDecide={vi.fn()} />);
    expect(screen.getByText('Delete file')).toBeInTheDocument();
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
  });

  it('calls onDecide with true when approve clicked', async () => {
    const handleDecide = vi.fn();
    render(<ApprovalCard approval={mockApproval} onDecide={handleDecide} />);
    
    await userEvent.click(screen.getByRole('button', { name: /approve/i }));
    expect(handleDecide).toHaveBeenCalledWith('approval-1', true);
  });

  it('calls onDecide with false when deny clicked', async () => {
    const handleDecide = vi.fn();
    render(<ApprovalCard approval={mockApproval} onDecide={handleDecide} />);
    
    await userEvent.click(screen.getByRole('button', { name: /deny/i }));
    expect(handleDecide).toHaveBeenCalledWith('approval-1', false);
  });

  it('displays risk level', () => {
    render(<ApprovalCard approval={mockApproval} onDecide={vi.fn()} />);
    expect(screen.getByRole('status')).toHaveTextContent(/medium/i);
  });

  it('shows timer', () => {
    render(<ApprovalCard approval={mockApproval} onDecide={vi.fn()} />);
    expect(screen.getByRole('timer')).toBeInTheDocument();
  });

  it('has accessible buttons', () => {
    render(<ApprovalCard approval={mockApproval} onDecide={vi.fn()} />);
    expect(screen.getByRole('button', { name: /approve action/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /deny action/i })).toBeInTheDocument();
  });

  it('disables buttons while deciding', async () => {
    const slowDecide = vi.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
    render(<ApprovalCard approval={mockApproval} onDecide={slowDecide} />);
    
    const approveButton = screen.getByRole('button', { name: /approve/i });
    await userEvent.click(approveButton);
    
    expect(approveButton).toBeDisabled();
  });
});
