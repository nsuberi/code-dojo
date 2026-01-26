# AI Eval Trace Viewer

A standalone React application for inspecting and annotating LangSmith traces from Code Dojo's AI features.

## Features

- **Feature Dashboard**: View all AI features (Digi-Trainer, Coding Planner, Code Review) with trace counts
- **Thread List**: Browse traces for each feature with pagination
- **Thread Detail**: Hierarchical span tree view with input/output inspection
- **Annotation System**: Add notes, tags, and dataset assignments to traces/spans
- **Keyboard Navigation**: Full keyboard support with vim-style navigation (j/k/h/l)
- **Command Palette**: Quick access to commands with Ctrl+K
- **Help Overlay**: View all keyboard shortcuts with ?

## Quick Start

```bash
# Install dependencies
npm install

# Create .env file with LangSmith credentials
cp .env.example .env
# Edit .env with your API key and project ID

# Start development server
npm run dev

# Run tests
npm run test:e2e
```

## Environment Variables

Create a `.env` file with:

```
VITE_LANGSMITH_API_KEY=your-langsmith-api-key
VITE_LANGSMITH_PROJECT_ID=your-project-id
```

## Keyboard Shortcuts

### Global
- `?` - Show help overlay
- `Ctrl+K` - Open command palette

### Dashboard
- `j/k` or `↓/↑` - Navigate features
- `Enter` - Open feature
- `1-3` - Jump to feature by number

### Thread List
- `j/k` or `↓/↑` - Navigate threads
- `Enter` - Open thread
- `g` - Back to dashboard
- `1-5` - Jump to thread by number

### Thread Detail
- `j/k` or `↓/↑` - Navigate spans
- `h/l` or `←/→` - Collapse/expand or parent/child
- `a` - Toggle annotation panel
- `n` - Annotate current span
- `t` - Annotate thread
- `g` - Back to thread list

## Project Structure

```
ai-eval-viewer/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components (Dashboard, ThreadList, ThreadDetail)
│   ├── providers/      # React context providers (HotkeyProvider)
│   ├── services/       # API services (LangSmith, annotations)
│   ├── styles/         # CSS design system
│   └── types/          # TypeScript type definitions
├── tests/              # Playwright E2E tests
└── playwright.config.ts
```

## Development

```bash
# Build for production
npm run build

# Run E2E tests with UI
npm run test:e2e:ui

# Lint code
npm run lint
```

## Tech Stack

- React 19 with TypeScript
- Vite for bundling
- React Router for navigation
- Playwright for E2E testing
- Local Storage for annotations (can be upgraded to SQLite)
