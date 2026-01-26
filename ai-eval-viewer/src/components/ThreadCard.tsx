import type { Thread } from '../types';

interface ThreadCardProps {
  thread: Thread;
  isSelected: boolean;
  onSelect: () => void;
}

export function ThreadCard({ thread, isSelected, onSelect }: ThreadCardProps) {
  return (
    <div
      className={`list-item ${isSelected ? 'active' : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onSelect()}
    >
      <div className="flex-1">
        <div className="flex items-center gap-sm mb-sm">
          <StatusBadge status={thread.status} />
          <span className="text-secondary" style={{ fontSize: '12px' }}>
            {formatTime(thread.startTime)}
          </span>
        </div>
        <div style={{ fontWeight: 500, marginBottom: '4px' }}>{thread.name}</div>
        {thread.inputPreview && (
          <div className="text-muted" style={{ fontSize: '12px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '300px' }}>
            {thread.inputPreview}
          </div>
        )}
        {thread.tags.length > 0 && (
          <div className="flex gap-sm mt-sm">
            {thread.tags.map((tag) => (
              <span key={tag.id} className="tag" style={{ backgroundColor: tag.color + '20', color: tag.color }}>
                {tag.name}
              </span>
            ))}
          </div>
        )}
      </div>
      {thread.durationMs && (
        <div className="text-muted" style={{ fontSize: '12px' }}>
          {formatDuration(thread.durationMs)}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: Thread['status'] }) {
  const className = `badge badge-${status === 'success' ? 'success' : status === 'error' ? 'error' : 'pending'}`;
  const label = status === 'success' ? 'Success' : status === 'error' ? 'Error' : 'Running';

  return <span className={className}>{label}</span>;
}

function formatTime(date: Date): string {
  const now = new Date();
  const isToday = date.toDateString() === now.toDateString();

  if (isToday) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${seconds % 60}s`;
}
