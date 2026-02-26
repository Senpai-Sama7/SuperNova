/**
 * Dashboard Integration Tests
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NovaDashboard from '../NovaDashboard';

// Mock the fetch API
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('NovaDashboard Integration', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    // Mock successful API response
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        timestamp: new Date().toISOString(),
        stream: {
          timestamp: new Date().toISOString(),
          throughput: 100,
          latency: 50,
          queueDepth: 5,
          errorRate: 0.01,
          cpuUsage: 40,
          memoryUsage: 60,
        },
        agents: [],
        agentMetrics: {
          totalAgents: 0,
          activeAgents: 0,
          idleAgents: 0,
          errorAgents: 0,
          averageLoad: 0,
          averageSuccessRate: 0,
        },
        memoryNodes: [],
        memoryMetrics: {
          totalNodes: 0,
          episodicCount: 0,
          semanticCount: 0,
          proceduralCount: 0,
          workingCount: 0,
          avgRelevance: 0,
        },
        semanticClusters: [],
        pendingApprovals: [],
        cognitiveLoop: {
          currentPhase: 'PERCEIVE',
          phaseProgress: 50,
          cycleCount: 100,
          lastCycleDuration: 150,
          averageCycleDuration: 160,
          phaseHistory: [],
        },
        orchestration: null,
        confidence: {
          overall: 85,
          calibration: 90,
          semanticEntropy: 0.2,
          sampleCount: 1000,
          history: [80, 82, 85, 84, 85],
        },
        conformalBands: [],
        chatHistory: [],
      }),
    });
  });

  it('renders dashboard with title', async () => {
    render(<NovaDashboard />);
    expect(screen.getByText(/nova dashboard/i)).toBeInTheDocument();
  });

  it('renders navigation tabs', async () => {
    render(<NovaDashboard />);
    expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /agents/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /memory/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /decisions/i })).toBeInTheDocument();
  });

  it('switches between tabs', async () => {
    render(<NovaDashboard />);
    
    const agentsTab = screen.getByRole('tab', { name: /agents/i });
    await userEvent.click(agentsTab);
    
    expect(agentsTab).toHaveAttribute('aria-selected', 'true');
  });

  it('has halt button', async () => {
    render(<NovaDashboard />);
    expect(screen.getByRole('button', { name: /halt/i })).toBeInTheDocument();
  });

  it('toggles halt state when clicked', async () => {
    render(<NovaDashboard />);
    
    const haltButton = screen.getByRole('button', { name: /halt/i });
    await userEvent.click(haltButton);
    
    expect(screen.getByRole('button', { name: /resume/i })).toBeInTheDocument();
  });

  it('renders chat interface', async () => {
    render(<NovaDashboard />);
    expect(screen.getByRole('complementary', { name: /chat/i })).toBeInTheDocument();
  });

  it('sends chat message', async () => {
    render(<NovaDashboard />);
    
    const input = screen.getByRole('textbox', { name: /message input/i });
    await userEvent.type(input, 'Hello Nova');
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    await userEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('Hello Nova')).toBeInTheDocument();
    });
  });

  it('displays connection status', async () => {
    render(<NovaDashboard />);
    
    await waitFor(() => {
      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });
});
