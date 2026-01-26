import type { Span } from '../types';
import { SpanNode } from './SpanNode';

interface SpanTreeProps {
  spans: Span[];
  selectedSpanId: string | null;
  expandedSpanIds: Set<string>;
  onSelectSpan: (spanId: string) => void;
  onToggleExpand: (spanId: string) => void;
}

export function SpanTree({
  spans,
  selectedSpanId,
  expandedSpanIds,
  onSelectSpan,
  onToggleExpand,
}: SpanTreeProps) {
  return (
    <div className="span-tree">
      {spans.map((span) => (
        <SpanNode
          key={span.id}
          span={span}
          depth={0}
          isSelected={selectedSpanId === span.id}
          isExpanded={expandedSpanIds.has(span.id)}
          selectedSpanId={selectedSpanId}
          expandedSpanIds={expandedSpanIds}
          onSelect={() => onSelectSpan(span.id)}
          onToggleExpand={() => onToggleExpand(span.id)}
          onSelectDescendant={onSelectSpan}
          onToggleDescendantExpand={onToggleExpand}
        />
      ))}
    </div>
  );
}
