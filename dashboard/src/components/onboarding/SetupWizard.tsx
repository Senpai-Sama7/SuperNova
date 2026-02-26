/**
 * SetupWizard — Multi-step first-run setup
 * Steps: API Keys → Model Selection → Privacy → Theme
 * 15.1.1–15.1.4
 */
import React, { useState, useEffect } from 'react';
import { API_BASE } from '../../theme/existing';

interface WizardStep { id: string; label: string; icon: string }

const STEPS: WizardStep[] = [
  { id: 'keys', label: 'API Keys', icon: '🔑' },
  { id: 'model', label: 'Model Selection', icon: '🤖' },
  { id: 'privacy', label: 'Privacy', icon: '🛡️' },
  { id: 'theme', label: 'Theme', icon: '🎨' },
];

const PROVIDERS = ['openai', 'anthropic', 'google', 'ollama'] as const;

interface CostRow { model: string; estimated_monthly_usd: number; tokens_per_month: number }

interface SetupWizardProps { onComplete: () => void }

const SetupWizard: React.FC<SetupWizardProps> = ({ onComplete }) => {
  const [step, setStep] = useState(0);
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [keyStatus, setKeyStatus] = useState<Record<string, { valid: boolean; message: string }>>({});
  const [model, setModel] = useState('gpt-4o-mini');
  const [privacy, setPrivacy] = useState(false);
  const [theme, setTheme] = useState('dark');
  const [costs, setCosts] = useState<CostRow[]>([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/setup/cost-estimate`).then(r => r.json())
      .then(d => setCosts(d.estimates || [])).catch(() => {});
  }, []);

  const validateKey = async (provider: string) => {
    const key = keys[provider];
    if (!key) return;
    try {
      const r = await fetch(`${API_BASE}/setup/validate-key`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: key }),
      });
      const d = await r.json();
      setKeyStatus(prev => ({ ...prev, [provider]: { valid: d.valid, message: d.message } }));
    } catch { setKeyStatus(prev => ({ ...prev, [provider]: { valid: false, message: 'Network error' } })); }
  };

  const finish = async () => {
    setSubmitting(true);
    try {
      await fetch(`${API_BASE}/setup/complete`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_keys: keys, default_model: model, privacy_mode: privacy, theme }),
      });
      localStorage.setItem('supernova_setup_complete', 'true');
      onComplete();
    } catch { alert('Setup failed — check connection'); }
    setSubmitting(false);
  };

  const canNext = step < STEPS.length - 1;
  const canBack = step > 0;

  return (
    <div className="nv-wizard-overlay" role="dialog" aria-label="Setup Wizard">
      <div className="nv-wizard-card">
        <h1 style={{ margin: '0 0 4px', fontSize: 22 }}>⚡ SuperNova Setup</h1>
        <div className="nv-wizard-steps" role="tablist">
          {STEPS.map((s, i) => (
            <button key={s.id} role="tab" aria-selected={i === step}
              className={`nv-wizard-step ${i === step ? 'active' : ''} ${i < step ? 'done' : ''}`}
              onClick={() => i <= step && setStep(i)}>
              <span>{s.icon}</span> {s.label}
            </button>
          ))}
        </div>

        <div className="nv-wizard-body">
          {step === 0 && (
            <div>
              <h2>Configure API Keys</h2>
              <p style={{ opacity: 0.7, fontSize: 13 }}>Enter keys for your preferred LLM providers.</p>
              {PROVIDERS.map(p => (
                <div key={p} style={{ marginBottom: 12 }}>
                  <label style={{ textTransform: 'capitalize', fontWeight: 600 }}>{p}</label>
                  <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
                    <input type="password" placeholder={p === 'ollama' ? 'No key needed' : `${p} API key`}
                      value={keys[p] || ''} disabled={p === 'ollama'}
                      onChange={e => setKeys(prev => ({ ...prev, [p]: e.target.value }))}
                      className="nv-wizard-input" />
                    {p !== 'ollama' && (
                      <button onClick={() => validateKey(p)} className="nv-wizard-btn-sm">Validate</button>
                    )}
                  </div>
                  {keyStatus[p] && (
                    <span style={{ fontSize: 12, color: keyStatus[p].valid ? '#00ffd5' : '#ff4d6a' }}>
                      {keyStatus[p].valid ? '✓' : '✗'} {keyStatus[p].message}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {step === 1 && (
            <div>
              <h2>Select Default Model</h2>
              <p style={{ opacity: 0.7, fontSize: 13 }}>Choose your primary model. You can change this later.</p>
              {costs.map(c => (
                <label key={c.model} className={`nv-wizard-radio ${model === c.model ? 'selected' : ''}`}>
                  <input type="radio" name="model" value={c.model} checked={model === c.model}
                    onChange={() => setModel(c.model)} />
                  <span style={{ fontWeight: 600 }}>{c.model}</span>
                  <span style={{ marginLeft: 'auto', opacity: 0.7 }}>
                    ~${c.estimated_monthly_usd}/mo
                  </span>
                </label>
              ))}
            </div>
          )}

          {step === 2 && (
            <div>
              <h2>Privacy Settings</h2>
              <label className="nv-wizard-toggle">
                <input type="checkbox" checked={privacy} onChange={e => setPrivacy(e.target.checked)} />
                <span>Enable Privacy Mode</span>
              </label>
              <p style={{ opacity: 0.7, fontSize: 13, marginTop: 8 }}>
                Privacy mode disables telemetry and keeps all data local.
              </p>
            </div>
          )}

          {step === 3 && (
            <div>
              <h2>Choose Theme</h2>
              <div style={{ display: 'flex', gap: 12 }}>
                {['dark', 'light', 'system'].map(t => (
                  <button key={t} onClick={() => setTheme(t)}
                    className={`nv-wizard-theme-btn ${theme === t ? 'selected' : ''}`}>
                    {t === 'dark' ? '🌙' : t === 'light' ? '☀️' : '💻'} {t}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="nv-wizard-footer">
          {canBack && <button onClick={() => setStep(s => s - 1)} className="nv-wizard-btn">← Back</button>}
          <div style={{ flex: 1 }} />
          {canNext && <button onClick={() => setStep(s => s + 1)} className="nv-wizard-btn primary">Next →</button>}
          {!canNext && (
            <button onClick={finish} disabled={submitting} className="nv-wizard-btn primary">
              {submitting ? 'Saving…' : '✓ Complete Setup'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default SetupWizard;
