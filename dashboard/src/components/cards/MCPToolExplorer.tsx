/**
 * MCPToolExplorer — lists MCP tools with descriptions and test interface.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Theme, API_BASE } from '../../theme';

interface MCPTool {
  name: string;
  description: string;
  server: string;
  parameters?: Record<string, unknown>;
}

export function MCPToolExplorer(): React.ReactElement {
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [testTool, setTestTool] = useState<string | null>(null);
  const [testInput, setTestInput] = useState('{}');
  const [testResult, setTestResult] = useState<string | null>(null);

  const fetchTools = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/mcp/tools`);
      if (res.ok) setTools(await res.json());
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { void fetchTools(); }, [fetchTools]);

  const executeTool = useCallback(async (name: string) => {
    setTestResult(null);
    try {
      const res = await fetch(`${API_BASE}/mcp/tools/${name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: testInput,
      });
      const data = await res.json();
      setTestResult(JSON.stringify(data, null, 2));
    } catch (err) {
      setTestResult(`Error: ${err instanceof Error ? err.message : 'Unknown'}`);
    }
  }, [testInput]);

  return (
    <div style={{ backgroundColor: Theme.colors.surfaceLow, borderRadius: '12px', padding: '20px', border: `1px solid ${Theme.colors.border}` }}>
      <h3 style={{ fontSize: '14px', fontWeight: 600, color: Theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '16px' }}>
        MCP Tools ({tools.length})
      </h3>
      {loading ? (
        <div style={{ color: Theme.colors.textMuted, fontSize: '13px' }}>Loading…</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '400px', overflowY: 'auto' }}>
          {tools.map(t => (
            <div key={t.name} style={{ padding: '10px 12px', borderRadius: '8px', backgroundColor: Theme.colors.surfaceMid }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 600, fontFamily: Theme.fonts.mono }}>{t.name}</span>
                <button
                  onClick={() => setTestTool(testTool === t.name ? null : t.name)}
                  style={{ padding: '2px 8px', borderRadius: '4px', border: `1px solid ${Theme.colors.accent}`, backgroundColor: 'transparent', color: Theme.colors.accent, cursor: 'pointer', fontSize: '10px' }}
                >
                  {testTool === t.name ? 'Close' : 'Test'}
                </button>
              </div>
              <div style={{ fontSize: '11px', color: Theme.colors.textMuted, marginTop: '4px' }}>{t.description}</div>
              <div style={{ fontSize: '10px', color: Theme.colors.secondary, marginTop: '2px' }}>via {t.server}</div>
              {testTool === t.name && (
                <div style={{ marginTop: '8px' }}>
                  <textarea
                    value={testInput}
                    onChange={e => setTestInput(e.target.value)}
                    style={{ width: '100%', height: '60px', padding: '6px', borderRadius: '4px', border: `1px solid ${Theme.colors.border}`, backgroundColor: Theme.colors.bg, color: Theme.colors.text, fontFamily: Theme.fonts.mono, fontSize: '11px', resize: 'vertical' }}
                    placeholder='{"param": "value"}'
                  />
                  <button
                    onClick={() => void executeTool(t.name)}
                    style={{ marginTop: '4px', padding: '4px 12px', borderRadius: '4px', border: 'none', backgroundColor: Theme.colors.accent, color: Theme.colors.bg, cursor: 'pointer', fontSize: '11px', fontWeight: 600 }}
                  >
                    Execute
                  </button>
                  {testResult && (
                    <pre style={{ marginTop: '6px', padding: '6px', borderRadius: '4px', backgroundColor: Theme.colors.bg, color: Theme.colors.text, fontSize: '10px', fontFamily: Theme.fonts.mono, maxHeight: '120px', overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                      {testResult}
                    </pre>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
