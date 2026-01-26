import { useState, useEffect, useRef } from 'react';
import { useHotkeys } from '../providers/HotkeyProvider';

export function CommandPalette() {
  const { isCommandPaletteOpen, setCommandPaletteOpen, getHotkeys } = useHotkeys();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const hotkeys = getHotkeys();
  const filteredCommands = hotkeys.filter((h) =>
    h.description.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (isCommandPaletteOpen && inputRef.current) {
      inputRef.current.focus();
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isCommandPaletteOpen]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, filteredCommands.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
      e.preventDefault();
      filteredCommands[selectedIndex].action();
      setCommandPaletteOpen(false);
    } else if (e.key === 'Escape') {
      setCommandPaletteOpen(false);
    }
  };

  if (!isCommandPaletteOpen) return null;

  return (
    <div className="modal-overlay" onClick={() => setCommandPaletteOpen(false)}>
      <div className="modal command-palette" onClick={(e) => e.stopPropagation()}>
        <input
          ref={inputRef}
          type="text"
          className="command-palette-input"
          placeholder="Type a command..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <div className="command-palette-list">
          {filteredCommands.map((cmd, index) => (
            <div
              key={`${cmd.scope}:${cmd.key}`}
              className={`command-item ${index === selectedIndex ? 'selected' : ''}`}
              onClick={() => {
                cmd.action();
                setCommandPaletteOpen(false);
              }}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <span>{cmd.description}</span>
              <span className="command-shortcut">
                {formatKey(cmd.key).map((k, i) => (
                  <kbd key={i} className="kbd">{k}</kbd>
                ))}
              </span>
            </div>
          ))}
          {filteredCommands.length === 0 && (
            <div className="command-item text-muted">No commands found</div>
          )}
        </div>
      </div>
    </div>
  );
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
