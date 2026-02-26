/**
 * Nova Dashboard - Main Application Component
 * AI Agent monitoring and control interface
 */
import React, { useState, useCallback, useMemo } from 'react';
import type { 
  TabId, 
  Agent, 
  ApprovalRequest, 
  ChatMessage,
  MemoryNode,
} from './types';
import { Theme, API_BASE } from './theme';
import { clamp, toFiniteNumber } from './utils/numberGuards';
import { computeSemanticEntropy } from './utils/entropy';
import { useNovaRealtime } from './hooks/useNovaRealtime';
import {
  Glow, StatusDot, MiniBar, AgentCard, ApprovalCard,
  CognitiveCycleRing, ConfidenceMeter, Sparkline,
  MemoryGraph, OrchestrationGraph,
  MCPServersPanel, MCPToolExplorer, SkillPanel, MCPExecutionLog,
} from './components';

// ============================================================================
// CONSTANTS
// ============================================================================

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: 'overview', label: 'Overview', icon: '◈' },
  { id: 'agents', label: 'Agents', icon: '◉' },
  { id: 'memory', label: 'Memory', icon: '◎' },
  { id: 'decisions', label: 'Decisions', icon: '⬡' },
  { id: 'mcp', label: 'MCP', icon: '⚙' },
];

// ============================================================================
// STYLES
// ============================================================================

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    backgroundColor: Theme.colors.bg,
    color: Theme.colors.text,
    fontFamily: Theme.fonts.main,
  },
  header: {
    padding: '20px 24px',
    borderBottom: `1px solid ${Theme.colors.border}`,
    backgroundColor: Theme.colors.surfaceLow,
    ...Theme.glass,
  },
  headerTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  title: {
    fontSize: '24px',
    fontWeight: 700,
    margin: 0,
    background: `linear-gradient(135deg, ${Theme.colors.accent}, ${Theme.colors.secondary})`,
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  statusContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  haltButton: (isHalted: boolean): React.CSSProperties => ({
    padding: '8px 16px',
    borderRadius: '6px',
    border: 'none',
    backgroundColor: isHalted ? Theme.colors.success : Theme.colors.error,
    color: '#fff',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  }),
  tabs: {
    display: 'flex',
    gap: '8px',
  },
  tab: (isActive: boolean): React.CSSProperties => ({
    padding: '8px 16px',
    borderRadius: '6px',
    border: 'none',
    backgroundColor: isActive ? `${Theme.colors.accent}20` : 'transparent',
    color: isActive ? Theme.colors.accent : Theme.colors.textMuted,
    fontWeight: isActive ? 600 : 400,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  }),
  main: {
    padding: '24px',
    display: 'grid',
    gap: '24px',
  },
  grid2: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '20px',
  },
  grid3: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '16px',
  },
  card: {
    backgroundColor: Theme.colors.surfaceLow,
    borderRadius: '12px',
    padding: '20px',
    border: `1px solid ${Theme.colors.border}`,
    ...Theme.glass,
  },
  cardTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: Theme.colors.textMuted,
    marginBottom: '16px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  metricRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  metricLabel: {
    fontSize: '12px',
    color: Theme.colors.textMuted,
  },
  metricValue: {
    fontSize: '18px',
    fontWeight: 700,
    color: Theme.colors.text,
  },
  chatContainer: {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    width: '380px',
    maxHeight: '500px',
    backgroundColor: Theme.colors.surfaceLow,
    borderRadius: '12px',
    border: `1px solid ${Theme.colors.border}`,
    ...Theme.glass,
    display: 'flex',
    flexDirection: 'column',
    zIndex: 100,
  },
  chatHeader: {
    padding: '16px',
    borderBottom: `1px solid ${Theme.colors.border}`,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  chatMessages: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
    maxHeight: '300px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  chatInput: {
    padding: '12px 16px',
    borderTop: `1px solid ${Theme.colors.border}`,
    display: 'flex',
    gap: '8px',
  },
  input: {
    flex: 1,
    padding: '10px 14px',
    borderRadius: '8px',
    border: `1px solid ${Theme.colors.border}`,
    backgroundColor: Theme.colors.bg,
    color: Theme.colors.text,
    fontSize: '14px',
    outline: 'none',
  },
  sendButton: {
    padding: '10px 18px',
    borderRadius: '8px',
    border: 'none',
    backgroundColor: Theme.colors.accent,
    color: Theme.colors.bg,
    fontWeight: 600,
    cursor: 'pointer',
  },
  message: (role: string): React.CSSProperties => ({
    alignSelf: role === 'user' ? 'flex-end' : 'flex-start',
    maxWidth: '80%',
    padding: '10px 14px',
    borderRadius: role === 'user' ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
    backgroundColor: role === 'user' ? Theme.colors.accent : Theme.colors.surfaceMid,
    color: role === 'user' ? Theme.colors.bg : Theme.colors.text,
    fontSize: '13px',
    lineHeight: 1.5,
  }),
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function NovaDashboard(): React.ReactElement {
  const [isHalted, setIsHalted] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([
    { id: 'welcome', role: 'system', content: 'Nova is online. How can I help?', timestamp: new Date().toISOString() },
  ]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [selectedMemoryNode, setSelectedMemoryNode] = useState<MemoryNode | null>(null);

  const {
    stream,
    agents,
    memoryNodes,
    pendingApprovals,
    metrics,
    cognitiveLoop,
    orchestration,
    conformalBands,
    semanticClusters,
    loading,
    error,
    refresh,
    wsState,
    wsReconnectAttempt,
    wsReconnect,
  } = useNovaRealtime(isHalted);

  const { entropy, confidence, clusters } = useMemo(
    () => computeSemanticEntropy(semanticClusters),
    [semanticClusters]
  );

  const handleDecide = useCallback(async (id: string, approved: boolean): Promise<void> => {
    try {
      await fetch(`${API_BASE}/api/v1/dashboard/approvals/${id}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved }),
      });
      void refresh();
    } catch (err) {
      console.error('Approval resolution failed:', err);
    }
  }, [refresh]);

  const sendMessage = useCallback((): void => {
    if (!chatInput.trim()) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: chatInput,
      timestamp: new Date().toISOString(),
    };

    setChatHistory(prev => [...prev, userMessage]);
    setChatInput('');

    fetch(`${API_BASE}/api/v1/agent/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: chatInput }),
    })
      .then(res => res.json())
      .then(data => {
        const assistantMessage: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: data.reply ?? data.message ?? 'Acknowledged.',
          timestamp: new Date().toISOString(),
        };
        setChatHistory(prev => [...prev, assistantMessage]);
      })
      .catch(() => {
        setChatHistory(prev => [...prev, {
          id: `err-${Date.now()}`,
          role: 'system',
          content: 'Failed to reach agent. Retrying...',
          timestamp: new Date().toISOString(),
        }]);
      });
  }, [chatInput]);

  const renderOverviewTab = (): React.ReactElement => (
    <div style={styles.grid2}>
      {/* Stream Metrics */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Stream Metrics</h3>
        <div style={styles.metricRow}>
          <span style={styles.metricLabel}>Throughput</span>
          <span style={styles.metricValue}>
            {toFiniteNumber(stream?.throughput).toFixed(1)} <small style={{ fontSize: '12px', color: Theme.colors.textMuted }}>ops/s</small>
          </span>
        </div>
        <div style={styles.metricRow}>
          <span style={styles.metricLabel}>Latency</span>
          <span style={styles.metricValue}>
            {toFiniteNumber(stream?.latency).toFixed(0)} <small style={{ fontSize: '12px', color: Theme.colors.textMuted }}>ms</small>
          </span>
        </div>
        <div style={styles.metricRow}>
          <span style={styles.metricLabel}>Queue Depth</span>
          <MiniBar value={toFiniteNumber(stream?.queueDepth)} max={100} color={Theme.colors.accent} showValue />
        </div>
        <div style={{ marginTop: '16px' }}>
          <Sparkline 
            data={metrics?.history?.slice(-20) ?? [50, 55, 60, 58, 62, 65, 70, 68, 72, 75]} 
            width={280} 
            height={40} 
          />
        </div>
      </div>

      {/* Cognitive Loop */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Cognitive Loop</h3>
        <div style={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
          <CognitiveCycleRing 
            phase={cognitiveLoop?.currentPhase ?? 'PERCEIVE'} 
            progress={toFiniteNumber(cognitiveLoop?.phaseProgress)} 
            size={180}
          />
        </div>
        <div style={{ textAlign: 'center', color: Theme.colors.textMuted, fontSize: '12px' }}>
          Cycle #{toFiniteNumber(cognitiveLoop?.cycleCount, 0).toFixed(0)} • {toFiniteNumber(cognitiveLoop?.lastCycleDuration, 0).toFixed(0)}ms avg
        </div>
      </div>

      {/* Confidence Metrics */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Confidence & Calibration</h3>
        <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
          <ConfidenceMeter value={toFiniteNumber(metrics?.overall)} size={120} />
          <div style={{ flex: 1 }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: Theme.colors.textMuted, marginBottom: '4px' }}>Semantic Entropy</div>
              <MiniBar value={entropy * 100} color={Theme.colors.warning} showValue />
            </div>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: Theme.colors.textMuted, marginBottom: '4px' }}>Clusters</div>
              <div style={{ fontSize: '18px', fontWeight: 700 }}>{clusters}</div>
            </div>
            <div>
              <div style={{ fontSize: '11px', color: Theme.colors.textMuted, marginBottom: '4px' }}>Samples</div>
              <div style={{ fontSize: '18px', fontWeight: 700 }}>{toFiniteNumber(metrics?.sampleCount, 0)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Active Agents */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Active Agents ({agents.filter(a => a.status === 'active').length}/{agents.length})</h3>
        <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
          {agents.slice(0, 4).map(agent => (
            <div key={agent.id} style={{ marginBottom: '8px' }}>
              <AgentCard agent={agent} compact onClick={setSelectedAgent} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderAgentsTab = (): React.ReactElement => (
    <div style={styles.grid3}>
      {agents.map(agent => (
        <AgentCard 
          key={agent.id} 
          agent={agent} 
          selected={selectedAgent?.id === agent.id}
          onClick={setSelectedAgent}
        />
      ))}
    </div>
  );

  const renderMemoryTab = (): React.ReactElement => (
    <div style={styles.grid2}>
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Memory Graph</h3>
        <MemoryGraph 
          data={{ nodes: memoryNodes, edges: [] }} 
          width={400} 
          height={300}
          onNodeClick={setSelectedMemoryNode}
          selectedNodeId={selectedMemoryNode?.id}
        />
      </div>
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Selected Memory</h3>
        {selectedMemoryNode ? (
          <div>
            <div style={{ marginBottom: '12px' }}>
              <span style={{ fontSize: '11px', color: Theme.colors.textMuted }}>Type</span>
              <div style={{ fontSize: '14px', fontWeight: 600, textTransform: 'capitalize' }}>{selectedMemoryNode.type}</div>
            </div>
            <div style={{ marginBottom: '12px' }}>
              <span style={{ fontSize: '11px', color: Theme.colors.textMuted }}>Label</span>
              <div style={{ fontSize: '14px' }}>{selectedMemoryNode.label}</div>
            </div>
            <div style={{ marginBottom: '12px' }}>
              <span style={{ fontSize: '11px', color: Theme.colors.textMuted }}>Relevance</span>
              <MiniBar value={(selectedMemoryNode.relevance ?? 0) * 100} color={Theme.colors.accent} showValue />
            </div>
            <div>
              <span style={{ fontSize: '11px', color: Theme.colors.textMuted }}>Timestamp</span>
              <div style={{ fontSize: '12px', fontFamily: Theme.fonts.mono }}>{selectedMemoryNode.timestamp}</div>
            </div>
          </div>
        ) : (
          <div style={{ color: Theme.colors.textMuted, fontSize: '14px' }}>Select a memory node to view details</div>
        )}
      </div>
    </div>
  );

  const renderDecisionsTab = (): React.ReactElement => (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ ...styles.cardTitle, margin: 0 }}>Pending Approvals ({pendingApprovals.length})</h3>
      </div>
      <div style={styles.grid2}>
        {pendingApprovals.map(approval => (
          <ApprovalCard 
            key={approval.id} 
            approval={approval} 
            onDecide={handleDecide}
          />
        ))}
        {pendingApprovals.length === 0 && (
          <div style={{ ...styles.card, textAlign: 'center', color: Theme.colors.textMuted }}>
            No pending approvals
          </div>
        )}
      </div>

      {orchestration && (
        <div style={{ ...styles.card, marginTop: '24px' }}>
          <h3 style={styles.cardTitle}>Orchestration Flow</h3>
          <OrchestrationGraph data={orchestration} width={600} height={300} />
        </div>
      )}
    </div>
  );

  const renderMCPTab = (): React.ReactElement => (
    <div style={styles.grid2}>
      <MCPServersPanel />
      <SkillPanel />
      <MCPToolExplorer />
      <MCPExecutionLog />
    </div>
  );

  const renderTabContent = (): React.ReactElement => {
    switch (activeTab) {
      case 'agents': return renderAgentsTab();
      case 'memory': return renderMemoryTab();
      case 'decisions': return renderDecisionsTab();
      case 'mcp': return renderMCPTab();
      default: return renderOverviewTab();
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerTop}>
          <Glow intensity="medium">
            <h1 style={styles.title}>◈ NOVA DASHBOARD</h1>
          </Glow>
          <div style={styles.statusContainer}>
            <StatusDot 
              status={loading ? 'busy' : error ? 'error' : 'online'} 
              label={loading ? 'Syncing...' : error ? 'Error' : 'Connected'} 
              pulse={!isHalted && !loading}
            />
            {wsState === 'reconnecting' && (
              <span style={{ fontSize: '11px', color: Theme.colors.warning }}>
                WS reconnecting ({wsReconnectAttempt}/5)…
              </span>
            )}
            {wsState === 'error' && (
              <button
                onClick={wsReconnect}
                style={{ padding: '4px 10px', borderRadius: '4px', border: `1px solid ${Theme.colors.error}`, backgroundColor: 'transparent', color: Theme.colors.error, cursor: 'pointer', fontSize: '11px' }}
              >
                Retry WS
              </button>
            )}
            <button 
              style={styles.haltButton(isHalted)}
              onClick={() => setIsHalted(!isHalted)}
              aria-pressed={isHalted}
            >
              {isHalted ? '▶ Resume' : '⏸ Halt'}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <nav role="tablist" style={styles.tabs} aria-label="Dashboard tabs">
          {TABS.map(tab => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`${tab.id}-panel`}
              style={styles.tab(activeTab === tab.id)}
              onClick={() => setActiveTab(tab.id)}
            >
              <span aria-hidden="true">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      {/* Main Content */}
      <main role="tabpanel" id={`${activeTab}-panel`} style={styles.main}>
        {error && (
          <div style={{ 
            backgroundColor: `${Theme.colors.error}20`, 
            border: `1px solid ${Theme.colors.error}`,
            borderRadius: '8px',
            padding: '16px',
            color: Theme.colors.error,
            marginBottom: '16px',
          }} role="alert">
            <strong>Error:</strong> {error.message}
            <button 
              onClick={() => void refresh()} 
              style={{ 
                marginLeft: '12px',
                padding: '4px 12px',
                borderRadius: '4px',
                border: `1px solid ${Theme.colors.error}`,
                backgroundColor: 'transparent',
                color: Theme.colors.error,
                cursor: 'pointer',
              }}
            >
              Retry
            </button>
          </div>
        )}
        {renderTabContent()}
      </main>

      {/* Chat Interface */}
      <aside style={styles.chatContainer} role="complementary" aria-label="Chat interface">
        <header style={styles.chatHeader}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <StatusDot status="online" pulse />
            <span style={{ fontWeight: 600 }}>Nova Assistant</span>
          </div>
        </header>
        <div 
          style={styles.chatMessages} 
          role="log" 
          aria-live="polite" 
          aria-label="Chat messages"
        >
          {chatHistory.map(msg => (
            <div 
              key={msg.id} 
              style={styles.message(msg.role)}
              role="article"
              aria-label={`${msg.role} message`}
            >
              {msg.content}
            </div>
          ))}
        </div>
        <form 
          style={styles.chatInput}
          onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
          role="form"
          aria-label="Send message"
        >
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Type a message..."
            style={styles.input}
            aria-label="Message input"
          />
          <button type="submit" style={styles.sendButton} aria-label="Send message">
            Send
          </button>
        </form>
      </aside>
    </div>
  );
}
