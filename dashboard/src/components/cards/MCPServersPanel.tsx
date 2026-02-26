/**
 * MCPServersPanel — displays MCP server health and tool counts.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Theme, API_BASE } from '../../theme';
import { StatusDot } from '../ui';

interface MCPServer {
  name: string;
  status: string;
  tool_count: number;
  url?: string;
}

export function MCPServersPanel(): React.ReactElement {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchServers = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/mcp/servers`);
      if (res.ok) setServers(await res.json());
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { void fetchServers(); }, [fetchServers]);

  return (
    <div style={{ backgroundColor: Theme.colors.surfaceLow, borderRadius: '12px', padding: '20px', border: `1px solid ${Theme.colors.border}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: Theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.5px', margin: 0 }}>
          MCP Servers ({servers.length})
        </h3>
        <button onClick={() => void fetchServers()} style={{ padding: '4px 10px', borderRadius: '4px', border: `1px solid ${Theme.colors.border}`, backgroundColor: 'transparent', color: Theme.colors.textMuted, cursor: 'pointer', fontSize: '11px' }}>
          ↻ Refresh
        </button>
      </div>
      {loading ? (
        <div style={{ color: Theme.colors.textMuted, fontSize: '13px' }}>Loading…</div>
      ) : servers.length === 0 ? (
        <div style={{ color: Theme.colors.textMuted, fontSize: '13px' }}>No MCP servers found</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {servers.map(s => (
            <div key={s.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', borderRadius: '8px', backgroundColor: Theme.colors.surfaceMid }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <StatusDot status={s.status === 'healthy' ? 'online' : 'error'} size="sm" />
                <span style={{ fontSize: '13px', fontWeight: 500 }}>{s.name}</span>
              </div>
              <span style={{ fontSize: '11px', color: Theme.colors.textMuted }}>{s.tool_count} tools</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
