import { useState, useCallback } from 'react';
import { API_BASE } from '../../theme';

/**
 * ExportButton — triggers memory export download from /memory/export.
 */
export function ExportButton() {
  const [loading, setLoading] = useState(false);

  const handleExport = useCallback(async (format: 'json' | 'markdown') => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token') || '';
      const resp = await fetch(
        `${API_BASE}/memory/export?format=${format}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const blob = await resp.blob();
      const ext = format === 'markdown' ? 'md' : 'json';
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `supernova-export.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch { /* silent */ }
    setLoading(false);
  }, []);

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <button
        onClick={() => handleExport('json')}
        disabled={loading}
        style={{
          padding: '8px 16px',
          borderRadius: 6,
          border: '1px solid #444',
          background: '#1a1a2e',
          color: '#e0e0e0',
          cursor: loading ? 'wait' : 'pointer',
        }}
      >
        {loading ? 'Exporting…' : '📥 Export JSON'}
      </button>
      <button
        onClick={() => handleExport('markdown')}
        disabled={loading}
        style={{
          padding: '8px 16px',
          borderRadius: 6,
          border: '1px solid #444',
          background: '#1a1a2e',
          color: '#e0e0e0',
          cursor: loading ? 'wait' : 'pointer',
        }}
      >
        {loading ? 'Exporting…' : '📝 Export Markdown'}
      </button>
    </div>
  );
}
