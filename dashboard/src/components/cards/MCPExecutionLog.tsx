/**
 * MCPExecutionLog — real-time log of MCP tool executions from WebSocket events.
 */
import React, { useState, useCallback } from 'react';
import { Theme } from '../../theme';

export interface MCPExecution {
  id: string;
  tool: string;
  status: 'running' | 'success' | 'error';
  timestamp: string;
  latencyMs?: number;
  input?: string;
  output?: string;
}

interface MCPExecutionLogProps {
  executions?: MCPExecution[];
}

export function MCPExecutionLog({ executions = [] }: MCPExecutionLogProps): React.ReactElement {
  const [expanded, setExpanded] = useState<string | null>(null);

  const toggle = useCallback((id: string) => {
    setExpanded(prev => prev === id ? null : id);
  }, []);

  const statusColor = (s: MCPExecution['status']) =>
    s === 'success' ? Theme.colors.success : s === 'error' ? Theme.colors.error : Theme.colors.warning;

  return (
    <div style={{ backgroundColor: Theme.colors.surfaceLow, borderRadius: '12px', padding: '20px', border: `1px solid ${Theme.colors.border}` }}>
      <h3 style={{ fontSize: '14px', fontWeight: 600, color: Theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '16px' }}>
        MCP Execution Log ({executions.length})
      </h3>
      {executions.length === 0 ? (
        <div style={{ color: Theme.colors.textMuted, fontSize: '13px' }}>No MCP executions yet</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '300px', overflowY: 'auto' }}>
          {executions.map(ex => (
            <div key={ex.id} style={{ padding: '8px 10px', borderRadius: '6px', backgroundColor: Theme.colors.surfaceMid, cursor: 'pointer' }} onClick={() => toggle(ex.id)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: statusColor(ex.status), display: 'inline-block' }} />
                  <span style={{ fontSize: '12px', fontFamily: Theme.fonts.mono, fontWeight: 500 }}>{ex.tool}</span>
                </div>
                <span style={{ fontSize: '10px', color: Theme.colors.textMuted }}>
                  {ex.latencyMs != null ? `${ex.latencyMs}ms` : '…'}
                </span>
              </div>
              {expanded === ex.id && ex.output && (
                <pre style={{ marginTop: '6px', padding: '6px', borderRadius: '4px', backgroundColor: Theme.colors.bg, color: Theme.colors.text, fontSize: '10px', fontFamily: Theme.fonts.mono, maxHeight: '80px', overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                  {ex.output}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
