import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FeatureCard } from '../components/FeatureCard';
import { useHotkey, useHotkeys } from '../providers/HotkeyProvider';
import { FEATURES, getFeatureStats } from '../services/langsmith';
import type { Feature, FeatureId } from '../types';

export function Dashboard() {
  const navigate = useNavigate();
  const { setScope } = useHotkeys();
  const [features, setFeatures] = useState<Feature[]>(FEATURES);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  // Set scope on mount
  useEffect(() => {
    setScope('dashboard');
  }, [setScope]);

  // Load feature stats
  useEffect(() => {
    async function loadStats() {
      try {
        const stats = await getFeatureStats();
        setFeatures(FEATURES.map((f) => {
          const stat = stats.get(f.id);
          return {
            ...f,
            threadCount: stat?.count,
            lastActivity: stat?.lastActivity,
          };
        }));
      } catch (err) {
        console.error('Failed to load feature stats:', err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  const selectFeature = useCallback((featureId: FeatureId) => {
    navigate(`/feature/${featureId}`);
  }, [navigate]);

  // Hotkeys
  useHotkey('j', () => setSelectedIndex((i) => Math.min(i + 1, features.length - 1)), 'Next feature', 'dashboard', [features.length]);
  useHotkey('k', () => setSelectedIndex((i) => Math.max(i - 1, 0)), 'Previous feature', 'dashboard');
  useHotkey('down', () => setSelectedIndex((i) => Math.min(i + 1, features.length - 1)), 'Next feature', 'dashboard', [features.length]);
  useHotkey('up', () => setSelectedIndex((i) => Math.max(i - 1, 0)), 'Previous feature', 'dashboard');
  useHotkey('enter', () => selectFeature(features[selectedIndex].id), 'Open feature', 'dashboard', [selectedIndex, features, selectFeature]);
  useHotkey('1', () => features[0] && selectFeature(features[0].id), 'Jump to feature 1', 'dashboard', [features, selectFeature]);
  useHotkey('2', () => features[1] && selectFeature(features[1].id), 'Jump to feature 2', 'dashboard', [features, selectFeature]);
  useHotkey('3', () => features[2] && selectFeature(features[2].id), 'Jump to feature 3', 'dashboard', [features, selectFeature]);

  return (
    <div className="container" data-testid={loading ? "dashboard-loading" : "dashboard-loaded"}>
      <header style={{ marginBottom: 'var(--spacing-xl)' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 600, marginBottom: 'var(--spacing-xs)' }}>
          AI Eval Trace Viewer
        </h1>
        <p className="text-secondary">
          Inspect and annotate LangSmith threads from Code Dojo's AI features
        </p>
      </header>

      {loading ? (
        <div className="text-muted" style={{ textAlign: 'center', padding: 'var(--spacing-xl)' }}>
          Loading features...
        </div>
      ) : (
        <div className="feature-grid" data-testid="feature-cards-container">
          {features.map((feature, index) => (
            <FeatureCard
              key={feature.id}
              feature={feature}
              isSelected={selectedIndex === index}
              onSelect={() => selectFeature(feature.id)}
              hotkeyHint={`${index + 1}`}
            />
          ))}
        </div>
      )}

      <footer style={{ marginTop: 'var(--spacing-xl)', textAlign: 'center' }}>
        <span className="text-muted" style={{ fontSize: '13px' }}>
          Press <kbd className="kbd">?</kbd> for keyboard shortcuts
          {' '} or <kbd className="kbd">⌘</kbd><kbd className="kbd">K</kbd> for command palette
        </span>
      </footer>
    </div>
  );
}
