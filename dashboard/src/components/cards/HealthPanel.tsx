import { useState, useEffect } from 'react';

const STATUS_COLORS = { healthy: '#22c55e', degraded: '#f59e0b', unhealthy: '#ef4444', unknown: '#6b7280' };
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export default function HealthPanel() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    const poll = async () => {
      try {
        const r = await fetch(`${API_BASE}/health/deep`);
        if (active) { setHealth(await r.json()); setError(null); }
      } catch (e) { if (active) setError(e.message); }
    };
    poll();
    const id = setInterval(poll, 15000);
    return () => { active = false; clearInterval(id); };
  }, []);

  if (error) return <div style={{ padding: 16, color: '#ef4444' }}>Health check failed: {error}</div>;
  if (!health) return <div style={{ padding: 16, color: '#9ca3af' }}>Loading health...</div>;

  return (
    <div style={{ padding: 16, background: '#111827', borderRadius: 12, border: '1px solid #1f2937' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <div style={{ width: 10, height: 10, borderRadius: '50%', background: STATUS_COLORS[health.status] || '#6b7280' }} />
        <span style={{ color: '#f3f4f6', fontWeight: 600 }}>System Health: {health.status}</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 8 }}>
        {(health.services || []).map((svc) => (
          <div key={svc.name} style={{ padding: 10, background: '#1f2937', borderRadius: 8, borderLeft: `3px solid ${STATUS_COLORS[svc.status]}` }}>
            <div style={{ color: '#d1d5db', fontSize: 13, fontWeight: 500 }}>{svc.name}</div>
            <div style={{ color: STATUS_COLORS[svc.status], fontSize: 12 }}>{svc.status} · {svc.latency_ms}ms</div>
            {svc.detail && <div style={{ color: '#6b7280', fontSize: 11, marginTop: 2 }}>{svc.detail}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
