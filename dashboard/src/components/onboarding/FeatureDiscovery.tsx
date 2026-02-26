/**
 * FeatureDiscovery — Highlights new features after updates
 * 15.3.3
 */
import React from 'react';

interface Feature { id: string; title: string; description: string; version: string }

const NEW_FEATURES: Feature[] = [
  { id: 'observability', title: 'Observability Dashboard', description: 'Real-time health checks, Prometheus metrics, and structured logging.', version: '2.0.0' },
  { id: 'security', title: 'Security Vault', description: 'AES-256-GCM encrypted secrets with platform keychain integration.', version: '2.0.0' },
  { id: 'backup', title: 'Backup & Recovery', description: 'Automated backups with S3 upload and point-in-time restore.', version: '2.0.0' },
];

interface FeatureDiscoveryProps { onDismiss: () => void }

const FeatureDiscovery: React.FC<FeatureDiscoveryProps> = ({ onDismiss }) => {
  const seen = localStorage.getItem('supernova_features_seen') || '';
  const unseen = NEW_FEATURES.filter(f => !seen.includes(f.id));
  if (unseen.length === 0) return null;

  const dismiss = () => {
    localStorage.setItem('supernova_features_seen', NEW_FEATURES.map(f => f.id).join(','));
    onDismiss();
  };

  return (
    <div className="nv-feature-discovery">
      <h3 style={{ margin: '0 0 8px' }}>🆕 What's New</h3>
      {unseen.map(f => (
        <div key={f.id} className="nv-feature-item">
          <strong>{f.title}</strong> <span style={{ opacity: 0.5, fontSize: 11 }}>v{f.version}</span>
          <p style={{ margin: '2px 0 0', fontSize: 13, opacity: 0.8 }}>{f.description}</p>
        </div>
      ))}
      <button onClick={dismiss} className="nv-wizard-btn primary" style={{ marginTop: 8 }}>Got it</button>
    </div>
  );
};

export default FeatureDiscovery;
