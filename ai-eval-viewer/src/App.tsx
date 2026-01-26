import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HotkeyProvider } from './providers/HotkeyProvider';
import { CommandPalette } from './components/CommandPalette';
import { HotkeyHelp } from './components/HotkeyHelp';
import { Dashboard } from './pages/Dashboard';
import { ThreadList } from './pages/ThreadList';
import { ThreadDetail } from './pages/ThreadDetail';
import './styles/design-system.css';

function App() {
  return (
    <BrowserRouter>
      <HotkeyProvider>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/feature/:featureId" element={<ThreadList />} />
          <Route path="/feature/:featureId/thread/:threadId" element={<ThreadDetail />} />
        </Routes>
        <CommandPalette />
        <HotkeyHelp />
      </HotkeyProvider>
    </BrowserRouter>
  );
}

export default App;
