import type { Feature } from '../types';

interface FeatureCardProps {
  feature: Feature;
  isSelected: boolean;
  onSelect: () => void;
  hotkeyHint?: string;
}

export function FeatureCard({ feature, isSelected, onSelect, hotkeyHint }: FeatureCardProps) {
  return (
    <div
      className={`feature-card ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onSelect()}
    >
      <div className="feature-card-title">{feature.name}</div>
      <div className="feature-card-description">{feature.description}</div>
      <div className="feature-card-stats">
        <div className="feature-stat">
          <span className="feature-stat-value">{feature.threadCount ?? '—'}</span>
          <span className="feature-stat-label">Threads</span>
        </div>
        <div className="feature-stat">
          <span className="feature-stat-value">
            {feature.lastActivity
              ? formatRelativeTime(feature.lastActivity)
              : '—'}
          </span>
          <span className="feature-stat-label">Last Activity</span>
        </div>
      </div>
      {hotkeyHint && <div className="hotkey-hint">{hotkeyHint}</div>}
    </div>
  );
}

function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return 'Just now';
}
