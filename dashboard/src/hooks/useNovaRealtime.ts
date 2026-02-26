/**
 * useNovaRealtime Hook
 * Real-time dashboard data via HTTP polling + WebSocket streaming with exponential backoff.
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  UseNovaRealtimeReturn,
  DashboardSnapshot,
  ConnectionState,
} from '../types';
import { API_BASE } from '../theme';

const POLL_INTERVAL_MS = 3000;
const SNAPSHOT_URL = `${API_BASE}/api/v1/dashboard/snapshot`;
const WS_BASE = API_BASE.replace(/^http/, 'ws');
const BACKOFF_BASE_MS = 1000;
const MAX_RECONNECT_ATTEMPTS = 5;

export function useNovaRealtime(isHalted = false): UseNovaRealtimeReturn {
  const [data, setData] = useState<DashboardSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [wsState, setWsState] = useState<ConnectionState>('disconnected');
  const [wsAttempt, setWsAttempt] = useState(0);

  const abortRef = useRef<AbortController | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sessionIdRef = useRef<string>('default');
  const tokenRef = useRef<string>('');

  // ── HTTP Polling for snapshot ──────────────────────────────────────────────
  const refresh = useCallback(async (): Promise<void> => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    try {
      setLoading(true);
      const res = await fetch(SNAPSHOT_URL, {
        signal: abortRef.current.signal,
        headers: { Accept: 'application/json' },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const snapshot: DashboardSnapshot = await res.json();
      setData(snapshot);
      setError(null);
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, []);

  // ── WebSocket with exponential backoff ─────────────────────────────────────
  const connectWs = useCallback((attempt: number) => {
    if (isHalted) return;
    wsRef.current?.close();

    const url = `${WS_BASE}/agent/stream/${sessionIdRef.current}?token=${tokenRef.current}`;
    setWsState(attempt === 0 ? 'connecting' : 'reconnecting');
    setWsAttempt(attempt);

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsState('connected');
      setWsAttempt(0);
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        // Merge streaming events into snapshot data as they arrive
        if (msg.type === 'token' || msg.type === 'tool_start' || msg.type === 'tool_result') {
          // These are real-time events — components can subscribe via state
          setData(prev => prev ? { ...prev, _lastWsEvent: msg } as DashboardSnapshot : prev);
        }
      } catch { /* ignore malformed frames */ }
    };

    ws.onclose = (ev) => {
      if (ev.code === 4001) {
        setWsState('error');
        setError(new Error('WebSocket auth failed'));
        return;
      }
      if (attempt < MAX_RECONNECT_ATTEMPTS) {
        const delay = BACKOFF_BASE_MS * Math.pow(2, attempt); // 1s, 2s, 4s, 8s, 16s
        setWsState('reconnecting');
        setWsAttempt(attempt + 1);
        reconnectTimerRef.current = setTimeout(() => connectWs(attempt + 1), delay);
      } else {
        setWsState('error');
      }
    };

    ws.onerror = () => {
      // onclose will fire after onerror — reconnect logic lives there
    };
  }, [isHalted]);

  const wsReconnect = useCallback(() => {
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    connectWs(0);
  }, [connectWs]);

  // ── Lifecycle ──────────────────────────────────────────────────────────────
  useEffect(() => {
    void refresh();
    if (!isHalted) {
      const interval = setInterval(() => void refresh(), POLL_INTERVAL_MS);
      return () => {
        clearInterval(interval);
        abortRef.current?.abort();
      };
    }
    return () => abortRef.current?.abort();
  }, [isHalted, refresh]);

  // WebSocket lifecycle — only connect if we have a token
  useEffect(() => {
    if (tokenRef.current && !isHalted) {
      connectWs(0);
    }
    return () => {
      wsRef.current?.close();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    };
  }, [isHalted, connectWs]);

  return {
    stream: data?.stream ?? null,
    agents: data?.agents ?? [],
    memoryNodes: data?.memoryNodes ?? [],
    pendingApprovals: data?.pendingApprovals ?? [],
    metrics: data?.confidence ?? null,
    cognitiveLoop: data?.cognitiveLoop ?? null,
    orchestration: data?.orchestration ?? null,
    conformalBands: data?.conformalBands ?? [],
    semanticClusters: data?.semanticClusters ?? [],
    loading,
    error,
    refresh,
    wsState,
    wsReconnectAttempt: wsAttempt,
    wsReconnect,
  };
}

export default useNovaRealtime;
