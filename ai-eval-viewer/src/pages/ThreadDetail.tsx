import { useEffect, useState, useCallback, useMemo } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { SpanTree } from '../components/SpanTree';
import { AnnotationPanel } from '../components/AnnotationPanel';
import { useHotkey, useHotkeys } from '../providers/HotkeyProvider';
import { getThreadDetails, FEATURES } from '../services/langsmith';
import type { Thread, Span, FeatureId } from '../types';

export function ThreadDetail() {
  const { featureId, threadId } = useParams<{ featureId: FeatureId; threadId: string }>();
  const navigate = useNavigate();
  const { setScope } = useHotkeys();

  const [thread, setThread] = useState<Thread | null>(null);
  const [spans, setSpans] = useState<Span[]>([]);
  const [selectedSpanId, setSelectedSpanId] = useState<string | null>(null);
  const [expandedSpanIds, setExpandedSpanIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [detailTab, setDetailTab] = useState<'input' | 'output'>('input');
  const [annotationPanelOpen, setAnnotationPanelOpen] = useState(false);
  const [annotationTarget, setAnnotationTarget] = useState<'thread' | 'span'>('span');

  const feature = FEATURES.find((f) => f.id === featureId);

  // Set scope on mount
  useEffect(() => {
    setScope('threadDetail');
  }, [setScope]);

  // Load thread details
  useEffect(() => {
    if (!featureId || !threadId) return;

    async function loadThread() {
      setLoading(true);
      try {
        const { thread: t, spans: s } = await getThreadDetails(threadId!, featureId as FeatureId);
        setThread(t);
        setSpans(s);

        // Expand root spans by default
        const initialExpanded = new Set<string>();
        s.forEach((span) => initialExpanded.add(span.id));
        setExpandedSpanIds(initialExpanded);

        // Select first span
        if (s.length > 0) {
          setSelectedSpanId(s[0].id);
        }
      } catch (err) {
        console.error('Failed to load thread:', err);
      } finally {
        setLoading(false);
      }
    }
    loadThread();
  }, [featureId, threadId]);

  // Flatten spans for navigation
  const flattenedSpans = useMemo(() => {
    const result: Span[] = [];
    const flatten = (spans: Span[]) => {
      for (const span of spans) {
        result.push(span);
        if (expandedSpanIds.has(span.id) && span.children.length > 0) {
          flatten(span.children);
        }
      }
    };
    flatten(spans);
    return result;
  }, [spans, expandedSpanIds]);

  const selectedSpan = useMemo(() => {
    const findSpan = (spans: Span[]): Span | undefined => {
      for (const span of spans) {
        if (span.id === selectedSpanId) return span;
        const found = findSpan(span.children);
        if (found) return found;
      }
      return undefined;
    };
    return findSpan(spans);
  }, [spans, selectedSpanId]);

  const toggleExpand = useCallback((spanId: string) => {
    setExpandedSpanIds((prev) => {
      const next = new Set(prev);
      if (next.has(spanId)) {
        next.delete(spanId);
      } else {
        next.add(spanId);
      }
      return next;
    });
  }, []);

  // Navigation helpers
  const selectNextSpan = useCallback(() => {
    const currentIndex = flattenedSpans.findIndex((s) => s.id === selectedSpanId);
    if (currentIndex < flattenedSpans.length - 1) {
      setSelectedSpanId(flattenedSpans[currentIndex + 1].id);
    }
  }, [flattenedSpans, selectedSpanId]);

  const selectPrevSpan = useCallback(() => {
    const currentIndex = flattenedSpans.findIndex((s) => s.id === selectedSpanId);
    if (currentIndex > 0) {
      setSelectedSpanId(flattenedSpans[currentIndex - 1].id);
    }
  }, [flattenedSpans, selectedSpanId]);

  const collapseOrParent = useCallback(() => {
    if (!selectedSpan) return;

    if (expandedSpanIds.has(selectedSpan.id) && selectedSpan.children.length > 0) {
      // Collapse current
      toggleExpand(selectedSpan.id);
    } else if (selectedSpan.parentSpanId) {
      // Go to parent
      setSelectedSpanId(selectedSpan.parentSpanId);
    }
  }, [selectedSpan, expandedSpanIds, toggleExpand]);

  const expandOrChild = useCallback(() => {
    if (!selectedSpan) return;

    if (selectedSpan.children.length > 0) {
      if (!expandedSpanIds.has(selectedSpan.id)) {
        // Expand current
        toggleExpand(selectedSpan.id);
      } else {
        // Go to first child
        setSelectedSpanId(selectedSpan.children[0].id);
      }
    }
  }, [selectedSpan, expandedSpanIds, toggleExpand]);

  // Toggle annotation panel
  const toggleAnnotationPanel = useCallback((target?: 'thread' | 'span') => {
    if (target) {
      setAnnotationTarget(target);
      setAnnotationPanelOpen(true);
    } else {
      setAnnotationPanelOpen((open) => !open);
    }
  }, []);

  // Hotkeys
  useHotkey('j', selectNextSpan, 'Next span', 'threadDetail', [selectNextSpan]);
  useHotkey('k', selectPrevSpan, 'Previous span', 'threadDetail', [selectPrevSpan]);
  useHotkey('down', selectNextSpan, 'Next span', 'threadDetail', [selectNextSpan]);
  useHotkey('up', selectPrevSpan, 'Previous span', 'threadDetail', [selectPrevSpan]);
  useHotkey('h', collapseOrParent, 'Collapse / Parent', 'threadDetail', [collapseOrParent]);
  useHotkey('l', expandOrChild, 'Expand / Child', 'threadDetail', [expandOrChild]);
  useHotkey('left', collapseOrParent, 'Collapse / Parent', 'threadDetail', [collapseOrParent]);
  useHotkey('right', expandOrChild, 'Expand / Child', 'threadDetail', [expandOrChild]);
  useHotkey('g', () => navigate(`/feature/${featureId}`), 'Back to thread list', 'threadDetail', [navigate, featureId]);
  useHotkey('a', () => toggleAnnotationPanel(), 'Toggle annotations', 'threadDetail', [toggleAnnotationPanel]);
  useHotkey('n', () => toggleAnnotationPanel('span'), 'Annotate span', 'threadDetail', [toggleAnnotationPanel]);
  useHotkey('t', () => toggleAnnotationPanel('thread'), 'Annotate thread', 'threadDetail', [toggleAnnotationPanel]);

  if (!feature) {
    return (
      <div className="container" data-testid="feature-not-found">
        <p className="text-error">Feature not found: {featureId}</p>
        <Link to="/" className="btn btn-secondary">Back to Dashboard</Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="container" data-testid="thread-loading">
        <div className="text-muted" style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
          Loading thread details...
        </div>
      </div>
    );
  }

  if (!thread) {
    return (
      <div className="container" data-testid="thread-not-found">
        <p className="text-error">Thread not found: {threadId}</p>
        <Link to={`/feature/${featureId}`} className="btn btn-secondary">Back to Thread List</Link>
      </div>
    );
  }

  return (
    <div className="layout" data-testid={spans.length > 0 ? "span-tree-loaded" : "span-tree-empty"}>
      {/* Span Tree Sidebar */}
      <aside className="sidebar" style={{ width: '350px' }}>
        <div style={{ padding: 'var(--spacing-md) var(--spacing-lg)', borderBottom: '1px solid var(--border-color)' }}>
          <nav className="breadcrumb mb-sm">
            <Link to="/" className="breadcrumb-link">Dashboard</Link>
            <span className="breadcrumb-separator">/</span>
            <Link to={`/feature/${featureId}`} className="breadcrumb-link">{feature.name}</Link>
            <span className="breadcrumb-separator">/</span>
            <span>Thread</span>
          </nav>
          <h2 style={{ fontSize: '16px', fontWeight: 600, margin: 0, marginTop: '8px' }}>
            {thread.name}
          </h2>
          <div className="flex items-center gap-sm mt-sm">
            <span className={`badge badge-${thread.status}`}>
              {thread.status === 'success' ? 'Success' : thread.status === 'error' ? 'Error' : 'Running'}
            </span>
            {thread.durationMs && (
              <span className="text-muted" style={{ fontSize: '12px' }}>
                {formatDuration(thread.durationMs)}
              </span>
            )}
          </div>
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: 'var(--spacing-sm)' }}>
          <SpanTree
            spans={spans}
            selectedSpanId={selectedSpanId}
            expandedSpanIds={expandedSpanIds}
            onSelectSpan={setSelectedSpanId}
            onToggleExpand={toggleExpand}
          />
        </div>

        <div style={{ padding: 'var(--spacing-md)', borderTop: '1px solid var(--border-color)', fontSize: '12px' }}>
          <span className="text-muted">
            <kbd className="kbd">j</kbd>/<kbd className="kbd">k</kbd> navigate
            {' '}<kbd className="kbd">h</kbd>/<kbd className="kbd">l</kbd> expand/collapse
          </span>
        </div>
      </aside>

      {/* Span Detail */}
      <main className="main-content" style={{ padding: 'var(--spacing-lg)' }}>
        {selectedSpan ? (
          <div>
            <div className="flex items-center justify-between mb-lg">
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 600, margin: 0 }}>
                  {selectedSpan.name}
                </h3>
                <div className="flex items-center gap-sm mt-sm">
                  <span className={`badge badge-${selectedSpan.status}`}>
                    {selectedSpan.status}
                  </span>
                  <span className="badge badge-info">{selectedSpan.type}</span>
                  {selectedSpan.durationMs && (
                    <span className="text-muted" style={{ fontSize: '12px' }}>
                      {formatDuration(selectedSpan.durationMs)}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex gap-sm">
                <button
                  className="btn btn-secondary"
                  onClick={() => toggleAnnotationPanel('span')}
                  title="Annotate this span (n)"
                >
                  Annotate Span
                </button>
                <button
                  className="btn btn-ghost"
                  onClick={() => toggleAnnotationPanel('thread')}
                  title="Annotate thread (t)"
                >
                  Annotate Thread
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-sm mb-md" style={{ borderBottom: '1px solid var(--border-color)' }}>
              <button
                className={`btn btn-ghost ${detailTab === 'input' ? 'active' : ''}`}
                onClick={() => setDetailTab('input')}
                style={{
                  borderRadius: 0,
                  borderBottom: detailTab === 'input' ? '2px solid var(--primary-color)' : '2px solid transparent',
                  marginBottom: '-1px'
                }}
              >
                Input
              </button>
              <button
                className={`btn btn-ghost ${detailTab === 'output' ? 'active' : ''}`}
                onClick={() => setDetailTab('output')}
                style={{
                  borderRadius: 0,
                  borderBottom: detailTab === 'output' ? '2px solid var(--primary-color)' : '2px solid transparent',
                  marginBottom: '-1px'
                }}
              >
                Output
              </button>
            </div>

            {/* Content */}
            <div className="code-block" style={{ maxHeight: '60vh', overflow: 'auto', padding: 'var(--spacing-md)' }}>
              <JsonViewer
                data={detailTab === 'input' ? selectedSpan.input : selectedSpan.output}
              />
            </div>

            {/* Metadata */}
            {selectedSpan.metadata && Object.keys(selectedSpan.metadata).length > 0 && (
              <div style={{ marginTop: 'var(--spacing-lg)' }}>
                <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--spacing-sm)' }}>
                  Metadata
                </h4>
                <div className="code-block" style={{ padding: 'var(--spacing-md)' }}>
                  <JsonViewer data={selectedSpan.metadata} />
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-muted" style={{ textAlign: 'center', paddingTop: 'var(--spacing-xl)' }}>
            Select a span to view details
          </div>
        )}
      </main>

      {/* Annotation Panel */}
      <AnnotationPanel
        isOpen={annotationPanelOpen}
        onClose={() => setAnnotationPanelOpen(false)}
        targetId={annotationTarget === 'thread' ? (thread?.id || '') : (selectedSpan?.id || '')}
        targetType={annotationTarget}
        targetName={annotationTarget === 'thread' ? (thread?.name || 'Thread') : (selectedSpan?.name || 'Span')}
      />
    </div>
  );
}

// JSON Viewer component
function JsonViewer({ data }: { data: unknown }) {
  if (data === null || data === undefined) {
    return <span className="json-null">null</span>;
  }

  if (typeof data === 'string') {
    // Check if it's a long string
    if (data.length > 500) {
      return (
        <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
          {data}
        </div>
      );
    }
    return <span className="json-string">"{data}"</span>;
  }

  if (typeof data === 'number') {
    return <span className="json-number">{data}</span>;
  }

  if (typeof data === 'boolean') {
    return <span className="json-boolean">{data.toString()}</span>;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) return <span>[]</span>;
    return (
      <div style={{ paddingLeft: '16px' }}>
        {'[\n'}
        {data.map((item, i) => (
          <div key={i} style={{ paddingLeft: '16px' }}>
            <JsonViewer data={item} />
            {i < data.length - 1 && ','}
          </div>
        ))}
        {']'}
      </div>
    );
  }

  if (typeof data === 'object') {
    const entries = Object.entries(data);
    if (entries.length === 0) return <span>{'{}'}</span>;
    return (
      <div>
        {'{\n'}
        {entries.map(([key, value], i) => (
          <div key={key} style={{ paddingLeft: '16px' }}>
            <span className="json-key">"{key}"</span>: <JsonViewer data={value} />
            {i < entries.length - 1 && ','}
          </div>
        ))}
        {'}'}
      </div>
    );
  }

  return <span>{String(data)}</span>;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const seconds = (ms / 1000).toFixed(2);
  return `${seconds}s`;
}
