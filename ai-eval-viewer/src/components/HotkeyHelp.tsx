import { useHotkeys } from '../providers/HotkeyProvider';

export function HotkeyHelp() {
  const { isHelpOpen, setHelpOpen, getHotkeys, currentScope } = useHotkeys();

  if (!isHelpOpen) return null;

  const hotkeys = getHotkeys();

  // Group by scope
  const byScope = new Map<string, typeof hotkeys>();
  for (const h of hotkeys) {
    const existing = byScope.get(h.scope) || [];
    existing.push(h);
    byScope.set(h.scope, existing);
  }

  const scopeOrder = ['global', currentScope];
  const sortedScopes = Array.from(byScope.keys()).sort((a, b) => {
    const aIndex = scopeOrder.indexOf(a);
    const bIndex = scopeOrder.indexOf(b);
    if (aIndex === -1 && bIndex === -1) return a.localeCompare(b);
    if (aIndex === -1) return 1;
    if (bIndex === -1) return -1;
    return aIndex - bIndex;
  });

  return (
    <div className="modal-overlay" onClick={() => setHelpOpen(false)}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px' }}>
        <div className="modal-header">
          <span className="modal-title">Keyboard Shortcuts</span>
          <button className="modal-close" onClick={() => setHelpOpen(false)}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" />
            </svg>
          </button>
        </div>
        <div className="modal-body">
          {sortedScopes.map((scope) => (
            <div key={scope} style={{ marginBottom: 'var(--spacing-lg)' }}>
              <h3 style={{
                fontSize: '13px',
                fontWeight: 600,
                textTransform: 'capitalize',
                color: 'var(--text-secondary)',
                marginBottom: 'var(--spacing-sm)'
              }}>
                {scope === 'global' ? 'Global' : formatScopeName(scope)}
                {scope === currentScope && scope !== 'global' && (
                  <span className="badge badge-info" style={{ marginLeft: '8px', fontSize: '10px' }}>
                    Active
                  </span>
                )}
              </h3>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: 'var(--spacing-sm)'
              }}>
                {byScope.get(scope)?.map((h) => (
                  <div key={`${h.scope}:${h.key}`} className="flex items-center justify-between" style={{ padding: 'var(--spacing-xs) 0' }}>
                    <span>{h.description}</span>
                    <span className="command-shortcut">
                      {formatKey(h.key).map((k, i) => (
                        <kbd key={i} className="kbd">{k}</kbd>
                      ))}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="modal-footer" style={{ justifyContent: 'center' }}>
          <span className="text-muted">Press <kbd className="kbd">Esc</kbd> or <kbd className="kbd">?</kbd> to close</span>
        </div>
      </div>
    </div>
  );
}

function formatScopeName(scope: string): string {
  return scope.replace(/([A-Z])/g, ' $1').replace(/-/g, ' ').trim();
}

function formatKey(key: string): string[] {
  const parts = key.split('+');
  return parts.map((p) => {
    if (p === 'mod') return navigator.platform.includes('Mac') ? '⌘' : 'Ctrl';
    if (p === 'shift') return '⇧';
    if (p === 'alt') return navigator.platform.includes('Mac') ? '⌥' : 'Alt';
    if (p === 'down') return '↓';
    if (p === 'up') return '↑';
    if (p === 'left') return '←';
    if (p === 'right') return '→';
    if (p === 'enter') return '↵';
    if (p === 'escape') return 'Esc';
    return p.toUpperCase();
  });
}
