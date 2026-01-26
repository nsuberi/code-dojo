import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ThreadCard } from '../components/ThreadCard';
import { useHotkey, useHotkeys } from '../providers/HotkeyProvider';
import { getFeatureRuns, runToThread, FEATURES } from '../services/langsmith';
import type { Thread, FeatureId } from '../types';

export function ThreadList() {
  const { featureId } = useParams<{ featureId: FeatureId }>();
  const navigate = useNavigate();
  const { setScope } = useHotkeys();

  const [threads, setThreads] = useState<Thread[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [cursor, setCursor] = useState<string | undefined>();
  const [hasMore, setHasMore] = useState(false);

  const feature = FEATURES.find((f) => f.id === featureId);

  // Set scope on mount
  useEffect(() => {
    setScope('threadList');
  }, [setScope]);

  // Load threads
  useEffect(() => {
    if (!featureId) return;

    async function loadThreads() {
      setLoading(true);
      try {
        const { runs, cursors } = await getFeatureRuns(featureId as FeatureId, 10);
        const newThreads = runs.map((run) => runToThread(run, featureId as FeatureId));
        setThreads(newThreads);
        setCursor(cursors.next);
        setHasMore(!!cursors.next);
      } catch (err) {
        console.error('Failed to load threads:', err);
      } finally {
        setLoading(false);
      }
    }
    loadThreads();
  }, [featureId]);

  const loadMore = useCallback(async () => {
    if (!featureId || !cursor) return;

    try {
      const { runs, cursors } = await getFeatureRuns(featureId as FeatureId, 10, cursor);
      const newThreads = runs.map((run) => runToThread(run, featureId as FeatureId));
      setThreads((prev) => [...prev, ...newThreads]);
      setCursor(cursors.next);
      setHasMore(!!cursors.next);
    } catch (err) {
      console.error('Failed to load more threads:', err);
    }
  }, [featureId, cursor]);

  const openThread = useCallback((threadId: string) => {
    navigate(`/feature/${featureId}/thread/${threadId}`);
  }, [navigate, featureId]);

  // Hotkeys
  useHotkey('j', () => setSelectedIndex((i) => Math.min(i + 1, threads.length - 1)), 'Next thread', 'threadList', [threads.length]);
  useHotkey('k', () => setSelectedIndex((i) => Math.max(i - 1, 0)), 'Previous thread', 'threadList');
  useHotkey('down', () => setSelectedIndex((i) => Math.min(i + 1, threads.length - 1)), 'Next thread', 'threadList', [threads.length]);
  useHotkey('up', () => setSelectedIndex((i) => Math.max(i - 1, 0)), 'Previous thread', 'threadList');
  useHotkey('enter', () => threads[selectedIndex] && openThread(threads[selectedIndex].id), 'Open thread', 'threadList', [selectedIndex, threads, openThread]);
  useHotkey('g', () => navigate('/'), 'Go to dashboard', 'threadList', [navigate]); // simplified from g d sequence

  // Number hotkeys for quick jump
  useHotkey('1', () => threads[0] && openThread(threads[0].id), 'Jump to thread 1', 'threadList', [threads, openThread]);
  useHotkey('2', () => threads[1] && openThread(threads[1].id), 'Jump to thread 2', 'threadList', [threads, openThread]);
  useHotkey('3', () => threads[2] && openThread(threads[2].id), 'Jump to thread 3', 'threadList', [threads, openThread]);
  useHotkey('4', () => threads[3] && openThread(threads[3].id), 'Jump to thread 4', 'threadList', [threads, openThread]);
  useHotkey('5', () => threads[4] && openThread(threads[4].id), 'Jump to thread 5', 'threadList', [threads, openThread]);

  if (!feature) {
    return (
      <div className="container">
        <p className="text-error">Feature not found: {featureId}</p>
        <Link to="/" className="btn btn-secondary">Back to Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="layout" data-testid={loading ? "threads-loading" : (threads.length > 0 ? "threads-loaded" : "no-threads")}>
      <aside className="sidebar">
        <div className="sidebar-header" style={{ padding: 'var(--spacing-lg)', borderBottom: '1px solid var(--border-color)' }}>
          <nav className="breadcrumb mb-sm">
            <Link to="/" className="breadcrumb-link">Dashboard</Link>
            <span className="breadcrumb-separator">/</span>
            <span>{feature.name}</span>
          </nav>
          <h2 style={{ fontSize: '18px', fontWeight: 600, margin: 0 }}>
            {feature.name}
          </h2>
          <p className="text-secondary" style={{ fontSize: '13px', marginTop: '4px' }}>
            {feature.description}
          </p>
        </div>

        <div style={{ flex: 1, overflow: 'auto' }}>
          {loading ? (
            <div className="text-muted" style={{ padding: 'var(--spacing-lg)', textAlign: 'center' }}>
              Loading threads...
            </div>
          ) : threads.length === 0 ? (
            <div className="text-muted" style={{ padding: 'var(--spacing-lg)', textAlign: 'center' }}>
              No threads found for this feature.
            </div>
          ) : (
            <>
              {threads.map((thread, index) => (
                <ThreadCard
                  key={thread.id}
                  thread={thread}
                  isSelected={selectedIndex === index}
                  onSelect={() => openThread(thread.id)}
                />
              ))}
              {hasMore && (
                <div style={{ padding: 'var(--spacing-md)', textAlign: 'center' }}>
                  <button className="btn btn-secondary" onClick={loadMore}>
                    Load more
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        <div style={{ padding: 'var(--spacing-md)', borderTop: '1px solid var(--border-color)' }}>
          <span className="text-muted" style={{ fontSize: '12px' }}>
            {threads.length} threads • <kbd className="kbd">j</kbd>/<kbd className="kbd">k</kbd> to navigate
          </span>
        </div>
      </aside>

      <main className="main-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="text-muted" style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '48px', marginBottom: 'var(--spacing-md)' }}>👈</p>
          <p>Select a thread to view details</p>
          <p style={{ fontSize: '13px', marginTop: 'var(--spacing-sm)' }}>
            Press <kbd className="kbd">Enter</kbd> to open selected thread
          </p>
        </div>
      </main>
    </div>
  );
}
