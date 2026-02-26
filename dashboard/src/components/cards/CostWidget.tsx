import { useState, useEffect, useCallback } from 'react';
import { Theme } from '../../theme';
import { API_BASE } from '../../theme';

interface CostSummary {
  daily_spend: number;
  monthly_spend: number;
  daily_limit: number | null;
  monthly_limit: number | null;
  daily_projection: number;
  daily_pct: number;
  confirmation_threshold: number;
  tracking_enabled: boolean;
}

const POLL_INTERVAL = 10_000;

export function CostWidget() {
  const [data, setData] = useState<CostSummary | null>(null);
  const [alerts, setAlerts] = useState<number[]>([]);

  const fetchCosts = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/costs`);
      if (res.ok) {
        const d = await res.json();
        setData(d);
        if (d.daily_pct >= 100) setAlerts(p => p.includes(100) ? p : [...p, 100]);
        else if (d.daily_pct >= 80) setAlerts(p => p.includes(80) ? p : [...p, 80]);
        else if (d.daily_pct >= 50) setAlerts(p => p.includes(50) ? p : [...p, 50]);
      }
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    fetchCosts();
    const id = setInterval(fetchCosts, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [fetchCosts]);

  if (!data || !data.tracking_enabled) return null;

  const pct = data.daily_pct;
  const barColor = pct >= 100 ? '#ff4444' : pct >= 80 ? '#ffaa00' : Theme.colors.accent;
  const latestAlert = alerts.length > 0 ? alerts[alerts.length - 1] : null;

  return (
    <div style={{
      background: Theme.colors.cardBg,
      borderRadius: 12,
      padding: 16,
      border: `1px solid ${pct >= 80 ? '#ffaa00' : Theme.colors.border}`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ color: Theme.colors.textSecondary, fontSize: 12 }}>💰 Daily Spend</span>
        <span style={{ color: Theme.colors.text, fontSize: 14, fontWeight: 600 }}>
          ${data.daily_spend.toFixed(4)} / ${data.daily_limit?.toFixed(2) ?? '∞'}
        </span>
      </div>

      {/* Progress bar */}
      <div style={{
        height: 6, borderRadius: 3,
        background: 'rgba(255,255,255,0.08)', overflow: 'hidden', marginBottom: 8,
      }}>
        <div style={{
          width: `${Math.min(pct, 100)}%`, height: '100%',
          background: barColor, borderRadius: 3, transition: 'width 0.5s',
        }} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: Theme.colors.textSecondary }}>
        <span>Monthly: ${data.monthly_spend.toFixed(4)}</span>
        <span>Proj: ${data.daily_projection.toFixed(2)}/day</span>
      </div>

      {latestAlert && latestAlert >= 80 && (
        <div style={{
          marginTop: 8, padding: '4px 8px', borderRadius: 6, fontSize: 11,
          background: latestAlert >= 100 ? 'rgba(255,68,68,0.15)' : 'rgba(255,170,0,0.15)',
          color: latestAlert >= 100 ? '#ff4444' : '#ffaa00',
        }}>
          ⚠ Budget {latestAlert}% reached
        </div>
      )}
    </div>
  );
}
