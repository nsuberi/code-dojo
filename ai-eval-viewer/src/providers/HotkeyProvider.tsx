import React, { createContext, useContext, useCallback, useEffect, useState, useRef } from 'react';

interface HotkeyHandler {
  key: string;
  action: () => void;
  description: string;
  scope: string;
}

interface HotkeyContextValue {
  registerHotkey: (handler: HotkeyHandler) => () => void;
  unregisterHotkey: (key: string, scope: string) => void;
  currentScope: string;
  setScope: (scope: string) => void;
  getHotkeys: (scope?: string) => HotkeyHandler[];
  isCommandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;
  isHelpOpen: boolean;
  setHelpOpen: (open: boolean) => void;
}

const HotkeyContext = createContext<HotkeyContextValue | null>(null);

export function useHotkeys() {
  const context = useContext(HotkeyContext);
  if (!context) {
    throw new Error('useHotkeys must be used within a HotkeyProvider');
  }
  return context;
}

// Hook to register a single hotkey
export function useHotkey(
  key: string,
  action: () => void,
  description: string,
  scope: string = 'global',
  deps: React.DependencyList = []
) {
  const { registerHotkey } = useHotkeys();

  useEffect(() => {
    const unregister = registerHotkey({ key, action, description, scope });
    return unregister;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, scope, ...deps]);
}

interface HotkeyProviderProps {
  children: React.ReactNode;
}

export function HotkeyProvider({ children }: HotkeyProviderProps) {
  const [currentScope, setCurrentScope] = useState('global');
  const [isCommandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [isHelpOpen, setHelpOpen] = useState(false);
  const hotkeysRef = useRef<Map<string, HotkeyHandler>>(new Map());

  // Generate a unique key for the handler
  const getHandlerKey = (key: string, scope: string) => `${scope}:${key}`;

  const registerHotkey = useCallback((handler: HotkeyHandler) => {
    const handlerKey = getHandlerKey(handler.key, handler.scope);
    hotkeysRef.current.set(handlerKey, handler);

    return () => {
      hotkeysRef.current.delete(handlerKey);
    };
  }, []);

  const unregisterHotkey = useCallback((key: string, scope: string) => {
    const handlerKey = getHandlerKey(key, scope);
    hotkeysRef.current.delete(handlerKey);
  }, []);

  const getHotkeys = useCallback((scope?: string) => {
    const handlers: HotkeyHandler[] = [];
    hotkeysRef.current.forEach((handler) => {
      if (!scope || handler.scope === scope || handler.scope === 'global') {
        handlers.push(handler);
      }
    });
    return handlers;
  }, []);

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't handle hotkeys when typing in inputs
      const target = event.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        // Allow Escape to blur input
        if (event.key === 'Escape') {
          target.blur();
        }
        return;
      }

      // Build the key string
      let keyString = '';
      if (event.metaKey || event.ctrlKey) keyString += 'mod+';
      if (event.shiftKey) keyString += 'shift+';
      if (event.altKey) keyString += 'alt+';
      keyString += event.key.toLowerCase();

      // Handle special keys
      if (event.key === 'ArrowDown') keyString = keyString.replace('arrowdown', 'down');
      if (event.key === 'ArrowUp') keyString = keyString.replace('arrowup', 'up');
      if (event.key === 'ArrowLeft') keyString = keyString.replace('arrowleft', 'left');
      if (event.key === 'ArrowRight') keyString = keyString.replace('arrowright', 'right');

      // Command Palette: Cmd/Ctrl + K
      if (keyString === 'mod+k') {
        event.preventDefault();
        setCommandPaletteOpen((open) => !open);
        return;
      }

      // Help: ?
      if (event.key === '?' && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        setHelpOpen((open) => !open);
        return;
      }

      // Escape closes modals
      if (event.key === 'Escape') {
        if (isCommandPaletteOpen) {
          setCommandPaletteOpen(false);
          return;
        }
        if (isHelpOpen) {
          setHelpOpen(false);
          return;
        }
      }

      // Don't process other hotkeys when modals are open
      if (isCommandPaletteOpen || isHelpOpen) {
        return;
      }

      // Try current scope first, then global
      const scopes = [currentScope, 'global'];
      for (const scope of scopes) {
        const handlerKey = getHandlerKey(keyString, scope);
        const handler = hotkeysRef.current.get(handlerKey);
        if (handler) {
          event.preventDefault();
          handler.action();
          return;
        }

        // Also check without modifiers for simple keys
        if (!event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
          const simpleHandlerKey = getHandlerKey(event.key.toLowerCase(), scope);
          const simpleHandler = hotkeysRef.current.get(simpleHandlerKey);
          if (simpleHandler) {
            event.preventDefault();
            simpleHandler.action();
            return;
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentScope, isCommandPaletteOpen, isHelpOpen]);

  const value: HotkeyContextValue = {
    registerHotkey,
    unregisterHotkey,
    currentScope,
    setScope: setCurrentScope,
    getHotkeys,
    isCommandPaletteOpen,
    setCommandPaletteOpen,
    isHelpOpen,
    setHelpOpen,
  };

  return <HotkeyContext.Provider value={value}>{children}</HotkeyContext.Provider>;
}
