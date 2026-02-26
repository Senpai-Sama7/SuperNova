/**
 * SuperNova Dashboard Type Definitions
 * Centralized type system for the AI Agent Dashboard
 */

// ============================================================================
// AGENT TYPES
// ============================================================================

export type AgentRole = 'planner' | 'researcher' | 'executor' | 'auditor' | 'creative';
export type AgentStatus = 'active' | 'reasoning' | 'waiting' | 'idle' | 'error';

export interface Agent {
  id: string;
  name: string;
  role: AgentRole;
  status: AgentStatus;
  task?: string;
  taskDescription?: string;
  progress: number; // 0-100
  load: number; // 0-100
  successRate: number; // 0-100
  lastActive: string; // ISO timestamp
  avatar?: string;
  metadata?: Record<string, unknown>;
}

export interface AgentMetrics {
  totalAgents: number;
  activeAgents: number;
  idleAgents: number;
  errorAgents: number;
  averageLoad: number;
  averageSuccessRate: number;
}

// ============================================================================
// MEMORY TYPES
// ============================================================================

export type MemoryNodeType = 'episodic' | 'semantic' | 'procedural' | 'working';

export interface MemoryNode {
  id: string;
  type: MemoryNodeType;
  label: string;
  content?: string;
  timestamp: string; // ISO timestamp
  relevance?: number; // 0-1
  strength?: number; // 0-1
  connections: string[]; // IDs of connected nodes
  metadata?: Record<string, unknown>;
  x?: number; // For graph visualization
  y?: number;
}

export interface MemoryGraphData {
  nodes: MemoryNode[];
  edges: Array<{
    source: string;
    target: string;
    strength?: number;
  }>;
}

export interface SemanticCluster {
  id: string;
  label: string;
  confidence: number; // 0-1
  size: number;
  items: string[];
  centroid?: number[];
}

export interface MemoryMetrics {
  totalNodes: number;
  episodicCount: number;
  semanticCount: number;
  proceduralCount: number;
  workingCount: number;
  avgRelevance: number;
}

// ============================================================================
// APPROVAL / HITL TYPES
// ============================================================================

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface ApprovalRequest {
  id: string;
  agentId: string;
  agentName: string;
  action: string;
  description: string;
  riskLevel: RiskLevel;
  timestamp: string;
  timeout: number; // seconds
  remainingTime: number; // seconds
  payload?: Record<string, unknown>;
  context?: string;
}

export interface ApprovalDecision {
  approvalId: string;
  approved: boolean;
  decidedAt: string;
  decidedBy?: string;
  reason?: string;
}

// ============================================================================
// COGNITIVE LOOP TYPES
// ============================================================================

export type CognitivePhase = 
  | 'PERCEIVE' 
  | 'REMEMBER' 
  | 'REASON' 
  | 'ACT' 
  | 'REFLECT' 
  | 'CONSOLIDATE';

export interface CognitiveLoopState {
  currentPhase: CognitivePhase;
  phaseProgress: number; // 0-100
  cycleCount: number;
  lastCycleDuration: number; // ms
  averageCycleDuration: number; // ms
  phaseHistory: Array<{
    phase: CognitivePhase;
    startedAt: string;
    duration: number;
  }>;
}

// ============================================================================
// STREAM / METRICS TYPES
// ============================================================================

export interface StreamMetrics {
  timestamp: string;
  throughput: number; // tokens/sec or ops/sec
  latency: number; // ms
  queueDepth: number;
  errorRate: number; // 0-1
  cpuUsage: number; // 0-100
  memoryUsage: number; // 0-100
}

export interface ConfidenceMetrics {
  overall: number; // 0-100
  calibration: number; // 0-100
  semanticEntropy: number; // 0-1
  sampleCount: number;
  history: number[]; // Last N confidence values
}

export interface ConformalBand {
  timestamp: string;
  lower: number;
  upper: number;
  actual?: number;
  coverage: number; // 0-1
}

// ============================================================================
// ORCHESTRATION TYPES
// ============================================================================

export type OrchestrationStrategy = 
  | 'sequential' 
  | 'parallel' 
  | 'hierarchical' 
  | 'adaptive';

export interface OrchestrationNode {
  id: string;
  type: 'agent' | 'gateway' | 'aggregator' | 'router';
  label: string;
  status: 'active' | 'pending' | 'completed' | 'failed';
  x: number;
  y: number;
  connections: string[];
  metadata?: Record<string, unknown>;
}

export interface OrchestrationGraph {
  nodes: OrchestrationNode[];
  edges: Array<{
    source: string;
    target: string;
    label?: string;
    status: 'active' | 'pending' | 'completed';
  }>;
  strategy: OrchestrationStrategy;
}

// ============================================================================
// DASHBOARD STATE TYPES
// ============================================================================

export type TabId = 'overview' | 'agents' | 'memory' | 'decisions' | 'mcp' | 'settings';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    agentId?: string;
    confidence?: number;
    sources?: string[];
  };
}

export interface DashboardSnapshot {
  timestamp: string;
  stream: StreamMetrics;
  agents: Agent[];
  agentMetrics: AgentMetrics;
  memoryNodes: MemoryNode[];
  memoryMetrics: MemoryMetrics;
  semanticClusters: SemanticCluster[];
  pendingApprovals: ApprovalRequest[];
  cognitiveLoop: CognitiveLoopState;
  orchestration: OrchestrationGraph;
  confidence: ConfidenceMetrics;
  conformalBands: ConformalBand[];
  chatHistory: ChatMessage[];
}

// ============================================================================
// THEME TYPES
// ============================================================================

export interface ColorPalette {
  bg: string;
  accent: string;
  secondary: string;
  warning: string;
  error: string;
  text: string;
  textMuted: string;
  success: string;
  info: string;
  surfaceLow: string;
  surfaceMid: string;
  border: string;
  glassBorder: string;
}

export interface FontStack {
  display: string;
  mono: string;
  main: string;
}

export interface GlassEffect {
  backdropFilter: string;
  backgroundColor: string;
  border: string;
  boxShadow: string;
  blur: string;
}

export interface Theme {
  colors: ColorPalette;
  fonts: FontStack;
  glass: GlassEffect;
}

// ============================================================================
// COMPONENT PROP TYPES
// ============================================================================

export interface GlowProps {
  children: React.ReactNode;
  color?: string;
  intensity?: 'low' | 'medium' | 'high';
  className?: string;
  animate?: boolean;
}

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export interface StatusDotProps {
  status: 'online' | 'offline' | 'busy' | 'away' | 'error';
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
  label?: string;
}

export interface MiniBarProps {
  value: number; // 0-100
  max?: number;
  color?: string;
  height?: number;
  showValue?: boolean;
  className?: string;
}

export interface RiskPillProps {
  level: RiskLevel;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export interface AgentCardProps {
  agent: Agent;
  onClick?: (agent: Agent) => void;
  selected?: boolean;
  compact?: boolean;
}

export interface ApprovalCardProps {
  approval: ApprovalRequest;
  onDecide: (id: string, approved: boolean) => void;
  compact?: boolean;
}

export interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  strokeWidth?: number;
  showArea?: boolean;
  showDots?: boolean;
}

export interface CognitiveCycleRingProps {
  phase: CognitivePhase;
  progress: number;
  size?: number;
  showLabels?: boolean;
}

export interface ConfidenceMeterProps {
  value: number; // 0-100
  size?: number;
  showLabel?: boolean;
  thresholds?: {
    proceed: number;
    monitor: number;
  };
}

export interface MemoryGraphProps {
  data: MemoryGraphData;
  width?: number;
  height?: number;
  onNodeClick?: (node: MemoryNode) => void;
  selectedNodeId?: string;
}

export interface OrchestrationGraphProps {
  data: OrchestrationGraph;
  width?: number;
  height?: number;
  onNodeClick?: (node: OrchestrationNode) => void;
}

export interface ConformalBandChartProps {
  data: ConformalBand[];
  width?: number;
  height?: number;
  showActual?: boolean;
}

// ============================================================================
// HOOK TYPES
// ============================================================================

export type ConnectionState = 'connecting' | 'connected' | 'reconnecting' | 'disconnected' | 'error';

export interface UseNovaRealtimeReturn {
  stream: StreamMetrics | null;
  agents: Agent[];
  memoryNodes: MemoryNode[];
  pendingApprovals: ApprovalRequest[];
  metrics: ConfidenceMetrics | null;
  cognitiveLoop: CognitiveLoopState | null;
  orchestration: OrchestrationGraph | null;
  conformalBands: ConformalBand[];
  semanticClusters: SemanticCluster[];
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
  wsState: ConnectionState;
  wsReconnectAttempt: number;
  wsReconnect: () => void;
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;

export interface SemanticEntropyResult {
  entropy: number;
  confidence: number;
  clusters: number;
  distribution: number[];
}
