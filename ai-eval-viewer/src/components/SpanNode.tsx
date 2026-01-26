import type { Span } from '../types';

interface SpanNodeProps {
  span: Span;
  depth: number;
  isSelected: boolean;
  isExpanded: boolean;
  selectedSpanId: string | null;
  expandedSpanIds: Set<string>;
  onSelect: () => void;
  onToggleExpand: () => void;
  onSelectDescendant: (spanId: string) => void;
  onToggleDescendantExpand: (spanId: string) => void;
}

export function SpanNode({
  span,
  depth,
  isSelected,
  isExpanded,
  selectedSpanId,
  expandedSpanIds,
  onSelect,
  onToggleExpand,
  onSelectDescendant,
  onToggleDescendantExpand,
}: SpanNodeProps) {
  const hasChildren = span.children.length > 0;

  return (
    <div className="tree-node">
      <div
        className={`tree-node-content ${isSelected ? 'active' : ''}`}
        onClick={onSelect}
        style={{ paddingLeft: `${depth * 20 + 8}px` }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter') onSelect();
          if (e.key === 'ArrowRight' && hasChildren && !isExpanded) onToggleExpand();
          if (e.key === 'ArrowLeft' && hasChildren && isExpanded) onToggleExpand();
        }}
      >
        {hasChildren ? (
          <span
            className={`tree-node-toggle ${isExpanded ? 'expanded' : ''}`}
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand();
            }}
          >
            <ChevronIcon />
          </span>
        ) : (
          <span className="tree-node-toggle" style={{ visibility: 'hidden' }}>
            <ChevronIcon />
          </span>
        )}
        <SpanTypeIcon type={span.type} />
        <span className="tree-node-name">{span.name}</span>
        <SpanStatusIcon status={span.status} />
        {span.durationMs && (
          <span className="text-muted" style={{ fontSize: '11px', marginLeft: 'auto' }}>
            {formatDuration(span.durationMs)}
          </span>
        )}
      </div>
      {hasChildren && isExpanded && (
        <div className="tree-node-children">
          {span.children.map((child) => (
            <SpanNode
              key={child.id}
              span={child}
              depth={depth + 1}
              isSelected={selectedSpanId === child.id}
              isExpanded={expandedSpanIds.has(child.id)}
              selectedSpanId={selectedSpanId}
              expandedSpanIds={expandedSpanIds}
              onSelect={() => onSelectDescendant(child.id)}
              onToggleExpand={() => onToggleDescendantExpand(child.id)}
              onSelectDescendant={onSelectDescendant}
              onToggleDescendantExpand={onToggleDescendantExpand}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ChevronIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <path d="M6.22 3.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.75.75 0 0 1-1.06-1.06L9.94 8 6.22 4.28a.75.75 0 0 1 0-1.06z" />
    </svg>
  );
}

function SpanTypeIcon({ type }: { type: Span['type'] }) {
  const icons: Record<Span['type'], { icon: string; color: string }> = {
    chain: { icon: '⛓', color: '#6366f1' },
    llm: { icon: '🤖', color: '#8b5cf6' },
    tool: { icon: '🔧', color: '#f59e0b' },
    retriever: { icon: '📚', color: '#10b981' },
  };

  const { icon, color } = icons[type];

  return (
    <span style={{ marginRight: '4px', color }}>
      {icon}
    </span>
  );
}

function SpanStatusIcon({ status }: { status: Span['status'] }) {
  if (status === 'success') {
    return <span style={{ color: 'var(--success-color)', marginLeft: '4px' }}>✓</span>;
  }
  if (status === 'error') {
    return <span style={{ color: 'var(--danger-color)', marginLeft: '4px' }}>✗</span>;
  }
  return <span style={{ color: 'var(--warning-color)', marginLeft: '4px' }}>●</span>;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const seconds = (ms / 1000).toFixed(1);
  return `${seconds}s`;
}
