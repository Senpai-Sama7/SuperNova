/**
 * TypeScript type definitions for Omega MCP Server
 * Combined: Omni capabilities + PurpleShield cybersecurity
 */

// ============================================
// OMNI TYPES (Browser, System, Image, etc.)
// ============================================

/** Browser page info */
export interface PageInfo {
  url: string;
  title: string;
  viewport: { width: number; height: number };
}

/** System metrics */
export interface SystemMetrics {
  [key: string]: unknown;
  cpu: {
    usage_percent: number;
    cores: number;
    load_avg: number[];
  };
  memory: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    usage_percent: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
    usage_percent: number;
  };
  uptime_seconds: number;
}

/** Docker container info */
export interface ContainerInfo {
  id: string;
  name: string;
  image: string;
  status: string;
  state: string;
  ports: Array<{
    internal: number;
    external?: number;
    protocol: string;
  }>;
  created: string;
}

/** WebSocket message */
export interface WSMessage {
  type: 'sent' | 'received';
  data: string;
  timestamp: string;
}

/** Network scan result */
export interface PortScanResult {
  host: string;
  port: number;
  state: 'open' | 'closed' | 'filtered';
  service?: string;
}

/** OCR result */
export interface OCRResult {
  [key: string]: unknown;
  text: string;
  confidence: number;
  words: Array<{
    text: string;
    confidence: number;
    bbox: { x: number; y: number; width: number; height: number };
  }>;
}

// ============================================
// PURPLESHIELD CYBERSECURITY TYPES
// ============================================

/** MCP Tool Definition */
export interface MCPTool {
  name: string;
  description: string;
  category: 'red-team' | 'blue-team' | 'purple-team' | 'omni';
  tags?: string[];
  inputSchema: {
    type: 'object';
    properties: Record<string, {
      type: string;
      description?: string;
      default?: unknown;
      enum?: string[];
      minimum?: number;
      maximum?: number;
    }>;
    required?: string[];
  };
}

/** MCP Tool Execution */
export interface MCPToolExecution {
  toolName: string;
  inputs: Record<string, unknown>;
}

/** MCP Tool Result */
export interface MCPToolResult {
  success: boolean;
  output?: unknown;
  error?: string;
  metadata?: {
    duration?: number;
    timestamp?: Date;
  };
}

/** Subdomain information */
export interface SubdomainInfo {
  subdomain: string;
  source: string;
  ports?: number[];
}

/** DNS Record */
export interface DNSRecord {
  type: string;
  name: string;
  value: string;
  ttl?: number;
}

/** WHOIS data */
export interface WHOISData {
  domain: string;
  registrar?: string;
  created?: string;
  expires?: string;
  updated?: string;
  nameservers?: string[];
  status?: string[];
  raw: string;
}

/** HTTP Security Header */
export interface SecurityHeader {
  name: string;
  present: boolean;
  value?: string;
  score: number;
}

/** HTTP Header Analysis Result */
export interface HTTPHeaderResult {
  url: string;
  statusCode: number;
  headers: Record<string, string>;
  securityHeaders: Record<string, SecurityHeader>;
  securityScore: number;
  technologies: string[];
}

/** Threat Intelligence Result */
export interface ThreatIntelResult {
  ioc: string;
  iocType: 'ip' | 'domain' | 'hash';
  malicious: boolean;
  score: number;
  sources: string[];
  details?: Record<string, unknown>;
}

/** CVE Information */
export interface CVEInfo {
  id: string;
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  cvssScore: number;
  published: string;
  references: string[];
}

/** MITRE ATT&CK Technique */
export interface MITRETechnique {
  id: string;
  name: string;
  description: string;
  tactics: string[];
  platforms: string[];
  detection?: string;
}

/** Purple Team Exercise */
export interface PurpleTeamExercise {
  id: string;
  name: string;
  description: string;
  status: 'planned' | 'in-progress' | 'completed';
  techniques: string[];
  startTime?: string;
  endTime?: string;
  findings?: ExerciseFinding[];
}

/** Exercise Finding */
export interface ExerciseFinding {
  technique: string;
  detected: boolean;
  detectionTime?: number;
  notes?: string;
  severity?: 'low' | 'medium' | 'high';
}

/** Security Alert */
export interface SecurityAlert {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  source: string;
  timestamp: string;
  acknowledged: boolean;
  iocs?: string[];
}
