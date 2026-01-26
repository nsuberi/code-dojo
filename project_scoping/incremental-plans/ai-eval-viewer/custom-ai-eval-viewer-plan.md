# AI Eval Trace Viewer - Implementation Plan

---

## 🚀 Implementation Progress Tracking

### Phase 0: Service Verification ✅ COMPLETE
- [x] LangSmith API connection verified (200 OK)
- [x] Confirmed project ID: `87944481-6b8e-427b-9c0e-be36ed18cd5b`
- [x] Identified trace types:
  - `articulation_message_process` - Digi-Trainer message processing
  - `articulation_harness_orchestration` - Digi-Trainer session orchestration
  - `planning_harness_orchestration` - Coding Planner orchestration
  - `LangGraph` - Agentic code review orchestration
- [x] Confirmed `thread_id` is null for all traces (threading not configured)

### Phase 1: Core Navigation ✅ COMPLETE
- [x] Create React app structure in `ai-eval-viewer/`
- [x] Set up TypeScript types for Thread, Span, etc.
- [x] Implement LangSmith API service
- [x] Build Feature Dashboard page
- [x] Build Thread List page
- [x] Build Thread Detail page with span tree
- [x] Implement hotkey navigation (j/k/h/l)

### Phase 2: Hotkey System ✅ COMPLETE
- [x] HotkeyProvider context
- [x] Command Palette (⌘K)
- [x] Hotkey Help overlay (?)

### Phase 3: Annotation System ✅ COMPLETE
- [x] Local storage schema for annotations (can upgrade to SQLite)
- [x] Annotation Panel UI with notes, tags, datasets
- [x] Tag picker with search and creation
- [x] Dataset picker with creation

### Phase 4: Code Viewer (PENDING)
- [ ] Source mapping configuration
- [ ] Code display with syntax highlighting
- [ ] Editor deep linking

### Playwright E2E Tests ✅ COMPLETE
- [x] Dashboard loads with feature cards
- [x] Navigation to feature thread list
- [x] Keyboard shortcuts (j/k navigation)
- [x] Number key quick jumps
- [x] Command palette (Ctrl+K)
- [x] Help overlay (?)
- [x] Back navigation
- [x] LangSmith API integration (loads real traces)
- [x] Annotation panel opens with a key
- [x] Adding notes to spans

### Summary

**Completed Phases: 0, 1, 2, 3**
**Remaining: Phase 4 (Code Viewer)**

The AI Eval Viewer is now functional and can be used to:
1. Browse AI feature traces from LangSmith
2. Navigate with keyboard shortcuts (vim-style)
3. View span input/output details
4. Add annotations (notes, tags, datasets) to traces and spans

To run: `cd ai-eval-viewer && npm run dev`

---

## Guiding principle

Setup unit and integration tests, and use playwright when applicable, to test the UI iteratively before finishing this work. I will provide credentials in the .env file. When necessary, make sample scripts to pull data from the remote services, analyze the returned schema, and continue with your implementation. You can run the Code Dojo application with test data and playwright in order to generate semi-predictable sample threads in LangSmith that you use while designing the UI affordances for the AI Eval custom interface.

## Before starting

Check the connections to each service for which you have a key, and prompt me to provide it if you are not able to use. Do this before beginning, because it is crucial to your ability to do integration testing during development, which you must do.

## Keep in mind - LangSmith Thread capture appears not correctly configured

No matter what follows here, keep in mind that it appears that no Threads have been captured in the LangSmith code-dojo project. You will need to test this using the provided API key and some sample code (creation of threads vs. just traces)

There is a Trace captured called "LangGraph" which appears to show multiple tool calls for the code review function. This makes sense as it doesn't involve multiple stages of user input - it just takes a PR and orchestrates multiple agentic reviews of that PR to produce initial feedback by the digi-trainer

The digi-trainer articulation_harness interactions are currently showing up as single traces, where those should be bound together into Threads, because they represent multiple steps of user input.

## There is an oversight in the plan below -- a missing third AI feature

There is no mention of the agentic code-review orchestration, which produces traces called "LangGraph". This should be configured for the AI Eval viewer app we are configuring along with the other two.

## Overview
A standalone viewer application for inspecting LangSmith traces from Code Dojo's AI features (Coding Planner, Digi-Trainer). The viewer is **separate from the main application UI** but will re-use design patterns and potentially share backend services.

---

## Fit Analysis Table (Updated with Codebase Analysis)

| Shape | Existing Components to Re-use | New Components Needed | Integration Points |
|-------|------------------------------|----------------------|-------------------|
| **Feature Dashboard** | **Design Patterns**: `module-card` layout (styles.css:212-227), `stat-card` pattern (styles.css:641-666), `module-grid` responsive grid (styles.css:206-210) | `FeatureDashboard.tsx`, `FeatureCard.tsx` | LangSmith projects API |
| **Thread List** | **Design Patterns**: `file-tree` list component (styles.css:2427-2493, review-tab.js:321-355), `status-badge` system (styles.css:332-378), collapsible card pattern (styles.css:1611-1660), pagination via "load more" button | `ThreadList.tsx`, `ThreadCard.tsx`, `ThreadPaginator.tsx` | LangSmith runs API |
| **Thread Detail** | **Design Patterns**: `anatomy-sidebar` + `anatomy-elements-list` nested structure (styles.css:984-1063), `breadcrumb` navigation (styles.css:380-388), expandable element pattern with `.active` state | `ThreadDetail.tsx`, `SpanTree.tsx`, `SpanNode.tsx` | LangSmith spans API |
| **Annotation Panel** | **Design Patterns**: `chat-input-area` form layout (styles.css:1163-1209, 2036-2075), `form-group` input styling (styles.css:271-304), `tag`/badge pill styling (styles.css:362-378) | `AnnotationPanel.tsx`, `NoteEditor.tsx`, `TagPicker.tsx`, `DatasetPicker.tsx` | Local SQLite DB |
| **Code Viewer** | **Re-use Logic**: `format_diff` filter (app.py:45-218) provides diff parsing template, `parseDiffToHtml` (review-tab.js:400-447) for client-side rendering. **Styling**: `.highlight` Pygments classes (styles.css:862-941), `.diff-*` classes (styles.css:2500-2591) | `CodeViewerPanel.tsx`, `SourceDisplay.tsx`, `FileTree.tsx` | File system / GitHub API |
| **Hotkey System** | **None directly** - would be new. Reference: existing click handlers pattern (review-tab.js), keyboard-first not implemented | `HotkeyProvider.tsx`, `CommandPalette.tsx`, `HotkeyOverlay.tsx`, `useHotkey.ts` | All components |
| **Dataset Manager** | **Design Patterns**: `synthesis-modal` modal structure (styles.css:1306-1372), `modal-overlay` backdrop (styles.css:1283-1303), form action buttons (styles.css:623-627) | `DatasetManager.tsx`, `DatasetForm.tsx`, `DatasetList.tsx` | Local SQLite DB |

---

## CSS Design System Available for Re-use

The existing `styles.css` (2743 lines) provides a complete design system:

### CSS Variables (styles.css:2-17)
```css
--primary-color: #2563eb;
--success-color: #22c55e;
--danger-color: #ef4444;
--warning-color: #f59e0b;
--background: #f8fafc;
--card-bg: #ffffff;
--text-primary: #1e293b;
--text-secondary: #64748b;
--border-color: #e2e8f0;
--shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
```

### Reusable Component Patterns
| Pattern | Location | Use Case in Viewer |
|---------|----------|-------------------|
| `.btn`, `.btn-primary`, `.btn-secondary` | styles.css:86-131 | All buttons |
| `.status-badge`, `.badge-*` | styles.css:332-378 | Thread/span status |
| `.card-header`, `.collapsible-card` | styles.css:1611-1660 | Thread cards, span nodes |
| `.modal-overlay`, `.synthesis-modal` | styles.css:1283-1372 | Command palette, help overlay |
| `.chat-messages`, `.chat-input-area` | styles.css:1103-1209 | Annotation panel chat-like UI |
| `.anatomy-sidebar`, `.anatomy-element` | styles.css:984-1063 | Thread list sidebar |
| `.file-tree`, `.file-tree-item` | styles.css:2427-2493 | File tree in code viewer |
| `.diff-line`, `.diff-added`, `.diff-removed` | styles.css:2525-2591 | Code diff display |
| `.highlight .c`, `.k`, `.s`, etc. | styles.css:879-941 | Syntax highlighting tokens |

---

## JavaScript Patterns to Reference

### Class-based Component Pattern (voice-input.js, review-tab.js)
```javascript
class ComponentName {
    constructor(options = {}) {
        this.onCallback = options.onCallback || (() => {});
        this.state = {};
    }
    async init() { /* setup */ }
    render() { /* DOM manipulation */ }
}
```

### Existing Diff Parser Logic (review-tab.js:400-447)
The `parseDiffToHtml()` function already handles:
- Hunk header parsing (`@@` lines)
- Line number tracking (old/new)
- Addition/removal/context line classification
- HTML generation with proper classes

### File Tree Rendering (review-tab.js:321-355)
The `renderFileTree()` function shows:
- Status icons per file type
- Click handlers for expand/collapse
- Stats display (+/- lines)

---

## Architecture Decision: Tech Stack

**Recommendation**: Build as a **standalone React app** (separate from Flask app)

**Rationale**:
1. The viewer is independent tooling for developers, not student-facing
2. React provides better state management for complex UI (hotkeys, panels, tree navigation)
3. Can be deployed separately (e.g., Vercel, static hosting)
4. Can use the existing CSS design system by copying/importing the variables and component styles

**Alternative**: Vanilla JS following existing patterns
- Pro: Consistent with codebase
- Con: More manual state management for complex interactions

---

## Implementation Phases

### Phase 1: Core Navigation (Feature Dashboard → Thread List → Thread Detail)
**Files to create:**
- `src/App.tsx` - Router setup
- `src/pages/Dashboard.tsx` - Feature cards
- `src/pages/ThreadList.tsx` - Thread list with pagination
- `src/pages/ThreadDetail.tsx` - Span tree view
- `src/components/SpanTree.tsx` - Hierarchical span display
- `src/components/SpanNode.tsx` - Individual span with expand/collapse
- `src/services/langsmith.ts` - API client for LangSmith
- `src/styles/design-system.css` - Copy of relevant CSS variables and patterns

**Key re-use:**
- Copy CSS variables and `.card`, `.badge`, `.file-tree` patterns
- Reference `parseDiffToHtml` structure for span tree rendering

### Phase 2: Hotkey System
**Files to create:**
- `src/providers/HotkeyProvider.tsx` - Global hotkey context
- `src/hooks/useHotkey.ts` - Registration hook
- `src/components/CommandPalette.tsx` - ⌘K modal
- `src/components/HotkeyHelp.tsx` - ? overlay

**New implementation** - no existing hotkey system to re-use.

### Phase 3: Annotation System
**Files to create:**
- `src/components/AnnotationPanel.tsx` - Sliding panel
- `src/components/NoteEditor.tsx` - Text input
- `src/components/TagPicker.tsx` - Tag selection/creation
- `src/components/DatasetPicker.tsx` - Dataset assignment
- `src/services/annotations.ts` - Local persistence API
- `src/db/schema.ts` - SQLite schema (or localStorage)

**Key re-use:**
- `.chat-input-area` form pattern for note input
- `.badge` styling for tag pills

### Phase 4: Code Viewer
**Files to create:**
- `src/components/CodeViewerPanel.tsx` - Panel container
- `src/components/SourceDisplay.tsx` - Syntax highlighted code
- `src/services/source.ts` - Source mapping logic

**Key re-use:**
- Copy `format_diff` parsing logic to TypeScript
- Use `.highlight` Pygments classes or integrate Prism.js
- Reference `.diff-*` styling for code display

---

## Verification Plan

1. **Unit Tests**: Test hotkey registration, span tree navigation, API mocks
2. **Integration Tests**: Full flow from dashboard → thread → span detail
3. **Manual Testing**:
   - Navigate entirely via keyboard (j/k/h/l/Enter)
   - Add annotations at thread and span level
   - Toggle between annotation panel and code viewer
   - Open command palette and execute commands
4. **LangSmith Integration**: Connect to real traces from Coding Planner runs

---

## Critical Files Summary

| Existing File | What to Extract |
|---------------|-----------------|
| `static/css/styles.css` | CSS variables, component patterns, syntax highlighting |
| `app.py` (lines 45-218) | `format_diff` parsing logic as reference |
| `static/js/review-tab.js` | `parseDiffToHtml`, `renderFileTree` patterns |
| `static/js/voice-input.js` | Class-based component structure pattern |

---

## Confirmed Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **App Architecture** | Standalone React app | Better state management for hotkeys/panels, independent deployment |
| **Annotation Storage** | Local SQLite | Fast, simple, appropriate for developer tooling |

## Remaining Open Questions

1. **LangSmith API Access**: Do we have API keys configured? Need to verify access to projects/runs/spans endpoints.
2. **Source Mapping Strategy**: How will span names map to source files? Manual config JSON or automatic via stack traces?


---

I'll start by reading the breadboarding skill to apply Ryan Singer's methodology to this AI Eval trace viewer design.Let me also check the examples reference to ensure I produce the right level of detail:Now I have a complete picture of the breadboarding methodology. Let me create a comprehensive breadboard for your AI Eval Trace Viewer.

---

# Breadboard: AI Eval Trace Viewer

## Requirements Table

| ID | Requirement | Priority | Status | Notes |
|----|-------------|----------|--------|-------|
| R1 | View traces organized by AI feature (Coding Planner, Digi-Trainer) | Must | Confirmed | Feature selector on dashboard |
| R2 | Display top 5 threads with ability to scroll through older | Must | Confirmed | Lazy loading pagination |
| R3 | Show LangSmith-style agentic call hierarchy for each thread | Must | Confirmed | Tree/nested span view |
| R4 | Navigate traces/threads entirely via hotkeys | Must | Confirmed | Power user workflow |
| R5 | Add open text annotations to traces/threads | Must | Confirmed | Free-form notes |
| R6 | Add/reuse tags on traces/threads | Must | Confirmed | Tag taxonomy + quick create |
| R7 | Add traces/threads to testing datasets for failure modes | Must | Confirmed | Curated eval sets |
| R8 | View source code for traced functions | Should | Confirmed | Code viewer panel |
| R9 | Edit code and commit to project | Could | Deferred | GitHub Coder integration - future |
| R10 | Hotkey to toggle between trace view and code view | Should | Confirmed | Rapid context switching |
| R11 | Create new testing datasets from scratch | Should | Confirmed | Failure mode categorization |
| R12 | Filter traces by time range, status, tags | Should | Open | Discovery and triage |

## Shapes Table

| Shape | Description | Scope | Dependencies |
|-------|-------------|-------|--------------|
| Feature Dashboard | Landing page to select which AI feature's traces to view | Small | LangSmith API |
| Thread List | Paginated list of threads for selected feature with preview | Medium | Feature Dashboard |
| Thread Detail | Hierarchical view of spans within a thread | Medium | Thread List |
| Annotation Panel | Add notes, tags, dataset assignments to traces | Medium | Thread Detail |
| Code Viewer | Display source code for traced functions | Medium | Thread Detail |
| Hotkey System | Global keyboard navigation and command palette | Medium | All shapes |
| Dataset Manager | Create/manage testing datasets for failure modes | Small | Annotation Panel |

## Fit Analysis Table

| Shape | Existing Components | New Components | Integration Points |
|-------|---------------------|----------------|-------------------|
| Feature Dashboard | None | FeatureDashboard, FeatureCard | LangSmith projects API |
| Thread List | None | ThreadList, ThreadCard, ThreadPaginator | LangSmith runs API |
| Thread Detail | None | ThreadDetail, SpanTree, SpanNode | LangSmith spans API |
| Annotation Panel | None | AnnotationPanel, NoteEditor, TagPicker, DatasetPicker | Local DB + LangSmith annotations API |
| Code Viewer | None | CodeViewer, SourcePanel | File system or GitHub API |
| Hotkey System | None | HotkeyProvider, CommandPalette, HotkeyOverlay | All components |
| Dataset Manager | None | DatasetManager, DatasetForm, DatasetList | Local DB |

## Places Table

| Place | Status | Parent | Description |
|-------|--------|--------|-------------|
| Feature Dashboard | new | - | Landing page showing AI features |
| Thread List View | new | - | List of threads for selected feature |
| Thread Detail View | new | - | Full thread with span hierarchy |
| Annotation Panel | new | Thread Detail View | Sliding panel for annotation work |
| Code Viewer Panel | new | Thread Detail View | Sliding panel for source code |
| Command Palette | new | - | Modal for hotkey commands (⌘K style) |
| Hotkey Help Overlay | new | - | Modal showing all available hotkeys |
| Dataset Manager Modal | new | - | Modal for managing testing datasets |
| Tag Manager Modal | new | - | Modal for creating/editing tags |

## Affordances Table (Bill of Materials)

### Shape: Feature Dashboard

| ID | Type | Name | Description | Place |
|----|------|------|-------------|-------|
| U1 | UI | feature cards | Clickable cards for each AI feature | Feature Dashboard |
| U2 | UI | feature name | Display name (e.g., "Digi-Trainer") | Feature Dashboard |
| U3 | UI | thread count badge | Number of threads per feature | Feature Dashboard |
| U4 | UI | last activity timestamp | When feature was last used | Feature Dashboard |
| N1 | Code | getFeatures() | List configured AI features | - |
| N2 | Code | getFeatureStats() | Thread counts, last activity | - |

### Shape: Thread List

| ID | Type | Name | Description | Place |
|----|------|------|-------------|-------|
| U5 | UI | thread list | Scrollable list of thread cards | Thread List View |
| U6 | UI | thread card | Preview of a thread (title, timestamp, status) | Thread List View |
| U7 | UI | thread status indicator | Success/error/in-progress badge | Thread List View |
| U8 | UI | tag pills | Tags applied to this thread | Thread List View |
| U9 | UI | "load more" button | Fetch older threads | Thread List View |
| U10 | UI | filter bar | Time range, status, tag filters | Thread List View |
| U11 | UI | active thread highlight | Visual indicator for selected thread | Thread List View |
| N3 | Code | getThreads(featureId, cursor, filters) | Paginated thread fetch | - |
| N4 | Code | getThreadPreview(threadId) | Summary data for thread card | - |

### Shape: Thread Detail

| ID | Type | Name | Description | Place |
|----|------|------|-------------|-------|
| U12 | UI | span tree | Hierarchical tree of spans | Thread Detail View |
| U13 | UI | span node | Single span with expand/collapse | Thread Detail View |
| U14 | UI | span input/output tabs | View input and output for span | Thread Detail View |
| U15 | UI | span duration badge | How long the span took | Thread Detail View |
| U16 | UI | span status icon | Success/error indicator | Thread Detail View |
| U17 | UI | active span highlight | Visual indicator for selected span | Thread Detail View |
| U18 | UI | breadcrumb trail | Current position in span hierarchy | Thread Detail View |
| U19 | UI | span detail panel | Expanded view of selected span | Thread Detail View |
| N5 | Code | getThreadSpans(threadId) | Full span hierarchy | - |
| N6 | Code | getSpanDetail(spanId) | Full input/output/metadata | - |
| N7 | Code | Thread | Data model for thread | - |
| N8 | Code | Span | Data model for span | - |

### Shape: Annotation Panel

| ID | Type | Name | Description | Place |
|----|------|------|-------------|-------|
| U20 | UI | annotation panel toggle | Expand/collapse annotation panel | Thread Detail View |
| U21 | UI | note text area | Free-form annotation input | Annotation Panel |
| U22 | UI | existing notes list | Previously added notes | Annotation Panel |
| U23 | UI | tag picker dropdown | Select from existing tags | Annotation Panel |
| U24 | UI | tag search input | Filter/create tags | Annotation Panel |
| U25 | UI | applied tags list | Tags on current trace/thread | Annotation Panel |
| U26 | UI | "create tag" button | Add new tag to taxonomy | Annotation Panel |
| U27 | UI | dataset picker dropdown | Select testing dataset | Annotation Panel |
| U28 | UI | "add to dataset" button | Assign to selected dataset | Annotation Panel |
| U29 | UI | dataset membership list | Which datasets include this item | Annotation Panel |
| U30 | UI | annotation scope toggle | Thread-level vs span-level | Annotation Panel |
| N9 | Code | saveNote(targetId, targetType, text) | Persist annotation note | - |
| N10 | Code | getNotes(targetId) | Fetch existing notes | - |
| N11 | Code | addTag(targetId, targetType, tagId) | Apply tag | - |
| N12 | Code | removeTag(targetId, tagId) | Remove tag | - |
| N13 | Code | getTags() | List available tags | - |
| N14 | Code | createTag(name, color) | Create new tag | - |
| N15 | Code | addToDataset(targetId, targetType, datasetId) | Add to testing dataset | - |
| N16 | Code | removeFromDataset(targetId, datasetId) | Remove from dataset | - |
| N17 | Code | getDatasets() | List available datasets | - |
| N18 | Code | Annotation | Data model for note | - |
| N19 | Code | Tag | Data model for tag | - |
| N20 | Code | Dataset | Data model for testing dataset | - |
| N21 | Code | DatasetItem | Junction table for dataset membership | - |

### Shape: Code Viewer

| ID | Type | Name | Description | Place |
|----|------|------|-------------|-------|
| U31 | UI | code viewer panel toggle | Expand/collapse code panel | Thread Detail View |
| U32 | UI | source code display | Syntax-highlighted code | Code Viewer Panel |
| U33 | UI | file path header | Current file being viewed | Code Viewer Panel |
| U34 | UI | line number gutter | Clickable line numbers | Code Viewer Panel |
| U35 | UI | function highlight | Highlighted current function | Code Viewer Panel |
| U36 | UI | "open in editor" button | Deep link to external editor | Code Viewer Panel |
| U37 | UI | file tree sidebar | Navigate related files | Code Viewer Panel |
| N22 | Code | getSourceForSpan(spanId) | Find source file and line | - |
| N23 | Code | getFileContent(filePath) | Fetch file contents | - |
| N24 | Code | getFunctionBoundaries(filePath, functionName) | Start/end lines | - |
| N25 | Code | SourceMapping | Map span names to code locations | - |

### Shape: Hotkey System

| ID | Type | Name | Description | Place |
|----|------|------|-------------|-------|
| U38 | UI | command palette | ⌘K style quick command modal | Command Palette |
| U39 | UI | command search input | Filter commands | Command Palette |
| U40 | UI | command list | Available commands with hotkeys | Command Palette |
| U41 | UI | hotkey help overlay | Full hotkey reference (? key) | Hotkey Help Overlay |
| U42 | UI | hotkey hints | Inline hints on focusable elements | All |
| U43 | UI | action toast | Confirmation of hotkey action | All |
| N26 | Code | HotkeyProvider | React context for hotkey state | - |
| N27 | Code | registerHotkey(key, action, scope) | Register a hotkey handler | - |
| N28 | Code | executeCommand(commandId) | Run a command programmatically | - |
| N29 | Code | getAvailableCommands(scope) | Context-aware command list | - |

### Shape: Dataset Manager

| ID | Type | Name | Description | Place |
|----|------|------|-------------|-------|
| U44 | UI | dataset list | All testing datasets | Dataset Manager Modal |
| U45 | UI | dataset card | Name, description, item count | Dataset Manager Modal |
| U46 | UI | "create dataset" button | Open creation form | Dataset Manager Modal |
| U47 | UI | dataset name input | Name for new dataset | Dataset Manager Modal |
| U48 | UI | dataset description input | Description/failure mode | Dataset Manager Modal |
| U49 | UI | dataset items preview | Sample items in dataset | Dataset Manager Modal |
| U50 | UI | "export dataset" button | Export for eval pipeline | Dataset Manager Modal |
| N30 | Code | createDataset(name, description) | Create new dataset | - |
| N31 | Code | updateDataset(datasetId, updates) | Edit dataset metadata | - |
| N32 | Code | deleteDataset(datasetId) | Remove dataset | - |
| N33 | Code | exportDataset(datasetId, format) | Export for LangSmith/testing | - |
| N34 | Code | getDatasetItems(datasetId) | List items in dataset | - |

## Hotkey Specification

| Key | Scope | Action | Command |
|-----|-------|--------|---------|
| `j` / `↓` | Thread List | Next thread | selectNextThread() |
| `k` / `↑` | Thread List | Previous thread | selectPrevThread() |
| `Enter` | Thread List | Open selected thread | openThread() |
| `j` / `↓` | Thread Detail | Next span | selectNextSpan() |
| `k` / `↑` | Thread Detail | Previous span | selectPrevSpan() |
| `h` / `←` | Thread Detail | Collapse span / go to parent | collapseOrParent() |
| `l` / `→` | Thread Detail | Expand span / go to child | expandOrChild() |
| `Enter` | Thread Detail | Toggle span detail panel | toggleSpanDetail() |
| `n` | Any | Add note (opens note input) | focusNoteInput() |
| `t` | Any | Add tag (opens tag picker) | focusTagPicker() |
| `d` | Any | Add to dataset (opens picker) | focusDatasetPicker() |
| `a` | Thread Detail | Toggle annotation panel | toggleAnnotationPanel() |
| `c` | Thread Detail | Toggle code viewer panel | toggleCodeViewerPanel() |
| `⌘K` / `Ctrl+K` | Global | Open command palette | openCommandPalette() |
| `?` | Global | Show hotkey help | showHotkeyHelp() |
| `Esc` | Modal | Close modal/panel | closeModal() |
| `g` `l` | Global | Go to thread list | navigateToThreadList() |
| `g` `d` | Global | Go to dashboard | navigateToDashboard() |
| `1-5` | Thread List | Jump to thread by position | jumpToThread(n) |
| `⌘Enter` / `Ctrl+Enter` | Note Input | Save note | saveCurrentNote() |
| `Tab` | Tag Picker | Cycle through tag suggestions | cycleTags() |
| `⌘S` / `Ctrl+S` | Code Viewer | Open in external editor | openInEditor() |

## Wiring Diagram

```
┌─ PLACE: Feature Dashboard (new) ────────────────────────────────────────────┐
│                                                                              │
│  N1 getFeatures()                                                            │
│      └─→ U1 feature cards                                                    │
│          └─→ U2 feature name                                                 │
│          └─→ N2 getFeatureStats() ─→ U3 thread count badge                  │
│                                   ─→ U4 last activity timestamp              │
│                                                                              │
│  U1 feature cards ─[click/Enter]─→ NAVIGATE: Thread List View               │
│                                                                              │
│  HOTKEYS: j/k navigate cards, Enter select, ? help                          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─ PLACE: Thread List View (new) ─────────────────────────────────────────────┐
│                                                                              │
│  N3 getThreads(featureId, cursor, filters)                                   │
│      └─→ U5 thread list                                                      │
│          └─→ U6 thread card ←─ N4 getThreadPreview()                        │
│              └─→ U7 thread status indicator                                  │
│              └─→ U8 tag pills                                                │
│              └─→ U11 active thread highlight (state)                         │
│                                                                              │
│  U9 "load more" button ─[click]─→ N3 getThreads(cursor: nextCursor)         │
│                                                                              │
│  U10 filter bar ─[change]─→ N3 getThreads(filters: updated)                 │
│                                                                              │
│  U6 thread card ─[click/Enter]─→ NAVIGATE: Thread Detail View               │
│                                                                              │
│  HOTKEYS: j/k navigate, Enter open, 1-5 jump, g d → dashboard               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─ PLACE: Thread Detail View (new) ───────────────────────────────────────────┐
│                                                                              │
│  ┌─ MAIN PANEL ──────────────────────────────────────────────────────────┐  │
│  │                                                                        │  │
│  │  U18 breadcrumb trail ←─ navigation state                              │  │
│  │                                                                        │  │
│  │  N5 getThreadSpans(threadId)                                           │  │
│  │      └─→ U12 span tree                                                 │  │
│  │          └─→ U13 span node ←─ N6 getSpanDetail(spanId)                │  │
│  │              └─→ U15 span duration badge                               │  │
│  │              └─→ U16 span status icon                                  │  │
│  │              └─→ U17 active span highlight (state)                     │  │
│  │                                                                        │  │
│  │  U13 span node ─[click/Enter]─→ U19 span detail panel                 │  │
│  │                                 └─→ U14 span input/output tabs         │  │
│  │                                                                        │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ RIGHT SIDEBAR (toggleable) ──────────────────────────────────────────┐  │
│  │                                                                        │  │
│  │  U20 annotation panel toggle ─[a key]─→ toggle visibility              │  │
│  │  U31 code viewer panel toggle ─[c key]─→ toggle visibility             │  │
│  │                                                                        │  │
│  │  (Only one panel visible at a time, or split view)                     │  │
│  │                                                                        │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  HOTKEYS: j/k/h/l navigate tree, a annotations, c code, n note, t tag       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─ PLACE: Annotation Panel (new, sidebar) ────────────────────────────────────┐
│                                                                              │
│  U30 annotation scope toggle ─[toggle]─→ thread-level / span-level          │
│                                                                              │
│  ── NOTES SECTION ──                                                         │
│  N10 getNotes(targetId) ─→ U22 existing notes list                          │
│                                                                              │
│  U21 note text area ─[⌘Enter]─→ N9 saveNote(targetId, targetType, text)    │
│                                  └─→ U22 (refresh)                           │
│                                  └─→ U43 action toast "Note saved"           │
│                                                                              │
│  ── TAGS SECTION ──                                                          │
│  N13 getTags() ─→ U23 tag picker dropdown                                   │
│                                                                              │
│  U24 tag search input ─[type]─→ filter U23                                  │
│                       ─[Tab]─→ cycle through suggestions                     │
│                       ─[Enter on new]─→ U26 "create tag" flow               │
│                                                                              │
│  U26 "create tag" button ─[click]─→ N14 createTag(name, color)              │
│                                     └─→ N13 getTags() refresh                │
│                                                                              │
│  U23 tag picker ─[Enter/click]─→ N11 addTag(targetId, targetType, tagId)    │
│                                  └─→ U25 applied tags list (refresh)         │
│                                  └─→ U43 action toast "Tag added"            │
│                                                                              │
│  U25 applied tags list item ─[click x]─→ N12 removeTag()                    │
│                                                                              │
│  ── DATASETS SECTION ──                                                      │
│  N17 getDatasets() ─→ U27 dataset picker dropdown                           │
│  N34 getDatasetItems() ─→ U29 dataset membership list                       │
│                                                                              │
│  U28 "add to dataset" button                                                 │
│      └─[click]─→ N15 addToDataset(targetId, targetType, datasetId)          │
│                  └─→ U29 (refresh)                                           │
│                  └─→ U43 action toast "Added to [dataset]"                   │
│                                                                              │
│  U29 item ─[click x]─→ N16 removeFromDataset()                              │
│                                                                              │
│  HOTKEYS: n focus note, t focus tag, d focus dataset, Esc close             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ PLACE: Code Viewer Panel (new, sidebar) ───────────────────────────────────┐
│                                                                              │
│  N22 getSourceForSpan(spanId)                                                │
│      └─→ U33 file path header                                                │
│      └─→ N23 getFileContent(filePath)                                        │
│          └─→ U32 source code display                                         │
│              └─→ U34 line number gutter                                      │
│                                                                              │
│  N24 getFunctionBoundaries(filePath, functionName)                           │
│      └─→ U35 function highlight (scroll to + highlight)                      │
│                                                                              │
│  U37 file tree sidebar ─[click file]─→ N23 getFileContent()                 │
│                                                                              │
│  U36 "open in editor" button ─[click/⌘S]─→ deeplink to VSCode/editor        │
│                                                                              │
│  HOTKEYS: ⌘S open in editor, Esc close                                      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ PLACE: Command Palette (new, modal) ───────────────────────────────────────┐
│                                                                              │
│  TRIGGER: ⌘K / Ctrl+K ─→ show modal                                         │
│                                                                              │
│  N29 getAvailableCommands(scope)                                             │
│      └─→ U40 command list                                                    │
│                                                                              │
│  U39 command search input ─[type]─→ filter U40                              │
│                                                                              │
│  U40 command list item ─[Enter/click]─→ N28 executeCommand(commandId)       │
│                                        └─→ close modal                       │
│                                        └─→ U43 action toast (if applicable)  │
│                                                                              │
│  HOTKEYS: ↑/↓ navigate, Enter execute, Esc close                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ PLACE: Dataset Manager Modal (new) ────────────────────────────────────────┐
│                                                                              │
│  TRIGGER: command palette "Manage datasets" or hotkey                        │
│                                                                              │
│  N17 getDatasets() ─→ U44 dataset list                                      │
│                       └─→ U45 dataset card                                   │
│                                                                              │
│  U46 "create dataset" button ─[click]─→ show form                           │
│                                                                              │
│  U47 dataset name input ───┐                                                 │
│  U48 dataset description ──┼─[submit]─→ N30 createDataset(name, desc)       │
│                            │            └─→ N17 getDatasets() refresh        │
│                                                                              │
│  U45 dataset card ─[click]─→ N34 getDatasetItems() ─→ U49 items preview     │
│                                                                              │
│  U50 "export dataset" button ─[click]─→ N33 exportDataset(id, format)       │
│                                        └─→ download file                     │
│                                                                              │
│  HOTKEYS: Esc close, n new dataset                                           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ PLACE: Hotkey Help Overlay (new, modal) ───────────────────────────────────┐
│                                                                              │
│  TRIGGER: ? key from anywhere                                                │
│                                                                              │
│  Displays U41 hotkey help overlay                                            │
│  - Organized by scope (Global, Thread List, Thread Detail, etc.)             │
│  - Shows key combo + description                                             │
│  - Dismisses on Esc or any other key                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Wiring Table

| From | To | Wire Type | Description |
|------|-----|-----------|-------------|
| N1 getFeatures() | U1 feature cards | populates | Load available AI features |
| N2 getFeatureStats() | U3 thread count badge | populates | Show thread count |
| N2 getFeatureStats() | U4 last activity timestamp | populates | Show last used |
| U1 feature cards | Thread List View | navigates | Click/Enter opens feature |
| N3 getThreads() | U5 thread list | populates | Load paginated threads |
| N4 getThreadPreview() | U6 thread card | populates | Thread summary data |
| U9 load more | N3 getThreads() | calls | Fetch next page |
| U10 filter bar | N3 getThreads() | calls | Re-fetch with filters |
| U6 thread card | Thread Detail View | navigates | Click/Enter opens thread |
| N5 getThreadSpans() | U12 span tree | populates | Load span hierarchy |
| N6 getSpanDetail() | U13 span node | populates | Full span data |
| N6 getSpanDetail() | U19 span detail panel | populates | Expanded view |
| U13 span node | U19 span detail panel | shows | Click opens detail |
| U20 annotation panel toggle | Annotation Panel | shows | Toggle visibility |
| U31 code viewer panel toggle | Code Viewer Panel | shows | Toggle visibility |
| N10 getNotes() | U22 existing notes list | populates | Load notes |
| U21 note text area | N9 saveNote() | calls | ⌘Enter saves |
| N9 saveNote() | N18 Annotation | writes | Persist note |
| N9 saveNote() | U43 action toast | triggers | Confirm save |
| N13 getTags() | U23 tag picker dropdown | populates | Available tags |
| U23 tag picker | N11 addTag() | calls | Select applies tag |
| N11 addTag() | U25 applied tags list | updates | Refresh display |
| U26 create tag | N14 createTag() | calls | Make new tag |
| N14 createTag() | N19 Tag | writes | Persist tag |
| N17 getDatasets() | U27 dataset picker dropdown | populates | Available datasets |
| U28 add to dataset | N15 addToDataset() | calls | Add to dataset |
| N15 addToDataset() | N21 DatasetItem | writes | Create junction record |
| N22 getSourceForSpan() | U33 file path header | populates | Show file path |
| N22 getSourceForSpan() | N23 getFileContent() | calls | Load file |
| N23 getFileContent() | U32 source code display | populates | Show code |
| N24 getFunctionBoundaries() | U35 function highlight | populates | Highlight function |
| U36 open in editor | External Editor | navigates | Deep link |
| ⌘K hotkey | U38 command palette | shows | Open palette |
| N29 getAvailableCommands() | U40 command list | populates | Context-aware commands |
| U40 command list item | N28 executeCommand() | calls | Run command |
| N30 createDataset() | N20 Dataset | writes | Persist dataset |
| N33 exportDataset() | Download | triggers | Export file |

## Triggers Table

| Trigger | Handler | Initiates | Conditions |
|---------|---------|-----------|------------|
| App load | N1 getFeatures() | Feature Dashboard population | Always |
| Feature selected | N3 getThreads() | Thread List population | Feature exists |
| Thread selected | N5 getThreadSpans() | Thread Detail population | Thread exists |
| Span selected | N6 getSpanDetail() | Span detail + code lookup | Span exists |
| Span selected | N22 getSourceForSpan() | Code viewer update | Code panel open |
| Hotkey pressed | N26 HotkeyProvider | Command dispatch | Key registered for scope |
| Filter changed | N3 getThreads() | List refresh | Debounced 300ms |

---

## Implementation Plan: Core Navigation

### Overview
Implement the primary navigation flow: Feature Dashboard → Thread List → Thread Detail with keyboard-first interaction.

### Files to Create
| File | Purpose |
|------|---------|
| `src/providers/HotkeyProvider.tsx` | Global hotkey context and registration |
| `src/hooks/useHotkey.ts` | Hook for registering hotkeys |
| `src/pages/Dashboard.tsx` | Feature Dashboard |
| `src/pages/ThreadList.tsx` | Thread List View |
| `src/pages/ThreadDetail.tsx` | Thread Detail View |
| `src/components/FeatureCard.tsx` | U1 feature card |
| `src/components/ThreadCard.tsx` | U6 thread card |
| `src/components/SpanTree.tsx` | U12 span tree |
| `src/components/SpanNode.tsx` | U13 span node |
| `src/components/CommandPalette.tsx` | U38 command palette |
| `src/services/langsmith.ts` | N1, N2, N3, N4, N5, N6 LangSmith API calls |
| `src/types/index.ts` | N7 Thread, N8 Span types |

### Data Models

```typescript
// N7 Thread
interface Thread {
  id: string;
  featureId: string;
  name: string;
  status: 'success' | 'error' | 'running';
  startTime: Date;
  endTime?: Date;
  durationMs?: number;
  inputPreview?: string;
  outputPreview?: string;
  tags: Tag[];
  annotations: Annotation[];
}

// N8 Span
interface Span {
  id: string;
  threadId: string;
  parentSpanId?: string;
  name: string;
  type: 'chain' | 'llm' | 'tool' | 'retriever';
  status: 'success' | 'error' | 'running';
  startTime: Date;
  endTime?: Date;
  durationMs?: number;
  input?: unknown;
  output?: unknown;
  metadata?: Record<string, unknown>;
  children: Span[];
  sourceMapping?: SourceMapping;
}

// N18 Annotation
interface Annotation {
  id: string;
  targetId: string;
  targetType: 'thread' | 'span';
  text: string;
  createdAt: Date;
  createdBy?: string;
}

// N19 Tag
interface Tag {
  id: string;
  name: string;
  color: string;
}

// N20 Dataset
interface Dataset {
  id: string;
  name: string;
  description: string;
  createdAt: Date;
  itemCount: number;
}

// N25 SourceMapping
interface SourceMapping {
  filePath: string;
  functionName: string;
  startLine: number;
  endLine: number;
}
```

### Hotkey System Implementation

```typescript
// src/providers/HotkeyProvider.tsx
interface HotkeyContextValue {
  registerHotkey: (key: string, action: () => void, scope: string) => void;
  unregisterHotkey: (key: string, scope: string) => void;
  currentScope: string;
  setScope: (scope: string) => void;
}

// Scopes: 'global' | 'dashboard' | 'threadList' | 'threadDetail' | 'annotationPanel' | 'codeViewer' | 'modal'

// Vim-style navigation for tree:
// j/k: move selection up/down (flat list within visible items)
// h/l: collapse/expand or move to parent/child
// Enter: toggle detail panel for selected span
```

### Acceptance Criteria

- [ ] Dashboard shows feature cards with thread counts
- [ ] j/k navigates feature cards, Enter opens Thread List
- [ ] Thread List shows top 5 threads, loads more on scroll/click
- [ ] j/k navigates threads, Enter opens Thread Detail
- [ ] Span tree renders with proper nesting
- [ ] j/k/h/l navigates span tree intuitively
- [ ] Enter on span opens span detail panel
- [ ] ⌘K opens command palette anywhere
- [ ] ? shows hotkey help overlay
- [ ] g l navigates to thread list, g d to dashboard

---

## Implementation Plan: Annotation System

### Overview
Enable rapid annotation workflow with notes, tags, and dataset assignment, all accessible via hotkeys.

### Files to Create
| File | Purpose |
|------|---------|
| `src/components/AnnotationPanel.tsx` | U20-U30 annotation panel |
| `src/components/NoteEditor.tsx` | U21 note text area |
| `src/components/TagPicker.tsx` | U23-U26 tag selection/creation |
| `src/components/DatasetPicker.tsx` | U27-U29 dataset selection |
| `src/services/annotations.ts` | N9-N12 annotation API |
| `src/services/tags.ts` | N13-N14 tag API |
| `src/services/datasets.ts` | N15-N17, N30-N34 dataset API |
| `src/db/schema.ts` | Prisma/SQLite schema for local storage |

### Key Interactions

```
[n] → Focus note textarea → Type → [⌘Enter] → Save + Toast
[t] → Open tag picker → Type to filter → [Tab] cycle → [Enter] apply
[d] → Open dataset picker → Select → [Enter] add → Toast
```

### Acceptance Criteria

- [ ] `a` toggles annotation panel visibility
- [ ] `n` focuses note input, `⌘Enter` saves
- [ ] `t` opens tag picker with search
- [ ] Tab cycles through tag suggestions
- [ ] Enter on unmatched text prompts tag creation
- [ ] `d` opens dataset picker
- [ ] Toast confirms each action
- [ ] Scope toggle switches between thread/span annotation

---

## Implementation Plan: Code Viewer

### Overview
Display source code for traced functions with syntax highlighting and editor integration.

### Files to Create
| File | Purpose |
|------|---------|
| `src/components/CodeViewerPanel.tsx` | U31-U37 code viewer |
| `src/components/SourceDisplay.tsx` | U32 syntax-highlighted code |
| `src/components/FileTree.tsx` | U37 file navigation |
| `src/services/source.ts` | N22-N24 source mapping |
| `src/config/sourceMappings.json` | N25 span→code mappings |

### Source Mapping Strategy

The source mapping configuration lives in the project (not the viewer). The viewer consumes this:

```json
{
  "digi-trainer": {
    "check_understanding": {
      "file": "src/agents/trainer.py",
      "function": "check_understanding"
    },
    "generate_feedback": {
      "file": "src/agents/trainer.py", 
      "function": "generate_feedback"
    }
  },
  "coding-planner": {
    "analyze_challenge": {
      "file": "src/agents/planner.py",
      "function": "analyze_challenge"
    }
  }
}
```

### Acceptance Criteria

- [ ] `c` toggles code viewer panel
- [ ] Selected span auto-loads associated source file
- [ ] Function is highlighted and scrolled into view
- [ ] `⌘S` opens file in external editor
- [ ] File tree shows related files for navigation

---

This breadboard provides you with a complete map of UI affordances, code affordances, and their wiring for implementing the AI Eval Trace Viewer. The hotkey system is central to the design, enabling the rapid annotation workflow you described. Take this to Claude Code and it should have everything needed to execute independently.