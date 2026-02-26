/**
 * SkillPanel — lists skills with activate/deactivate toggles.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Theme, API_BASE } from '../../theme';

interface Skill {
  name: string;
  description: string;
  active: boolean;
  source?: string;
}

export function SkillPanel(): React.ReactElement {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSkills = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/skills`);
      if (res.ok) setSkills(await res.json());
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { void fetchSkills(); }, [fetchSkills]);

  const toggleSkill = useCallback(async (name: string, currentlyActive: boolean) => {
    const action = currentlyActive ? 'deactivate' : 'activate';
    try {
      await fetch(`${API_BASE}/skills/${name}/${action}`, { method: 'POST' });
      setSkills(prev => prev.map(s => s.name === name ? { ...s, active: !currentlyActive } : s));
    } catch { /* ignore */ }
  }, []);

  return (
    <div style={{ backgroundColor: Theme.colors.surfaceLow, borderRadius: '12px', padding: '20px', border: `1px solid ${Theme.colors.border}` }}>
      <h3 style={{ fontSize: '14px', fontWeight: 600, color: Theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '16px' }}>
        Skills ({skills.filter(s => s.active).length}/{skills.length} active)
      </h3>
      {loading ? (
        <div style={{ color: Theme.colors.textMuted, fontSize: '13px' }}>Loading…</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {skills.map(s => (
            <div key={s.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', borderRadius: '8px', backgroundColor: Theme.colors.surfaceMid }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 500 }}>{s.name}</div>
                <div style={{ fontSize: '11px', color: Theme.colors.textMuted }}>{s.description}</div>
              </div>
              <button
                onClick={() => void toggleSkill(s.name, s.active)}
                style={{
                  padding: '4px 12px', borderRadius: '12px', border: 'none', cursor: 'pointer', fontSize: '11px', fontWeight: 600,
                  backgroundColor: s.active ? Theme.colors.success : Theme.colors.surfaceLow,
                  color: s.active ? Theme.colors.bg : Theme.colors.textMuted,
                }}
              >
                {s.active ? 'ON' : 'OFF'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
