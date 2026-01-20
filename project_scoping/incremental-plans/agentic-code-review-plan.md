# Plan: Integrate arch-pr-analyzer with LangGraph-based AI Review

## Status: Phase 1 - Initial Understanding

### User Request
Explore whether the arch-pr-analyzer plugin can be used in the AI review of submitted PRs (currently using LangGraph), and how to replicate the plugin's behavior with LangGraph.

### Exploration Tasks
1. Understand current LangGraph-based AI review implementation
2. Understand arch-pr-analyzer plugin capabilities
3. Determine integration possibilities
4. Design LangGraph replication approach

### Progress
- [x] Exploring current AI review system (LangGraph)
- [x] Exploring arch-pr-analyzer plugin structure
- [x] Exploring PR submission and review workflow

### Key Findings from Phase 1

**Current System:**
- AI review in `services/agentic_review.py` - 8-step sequential pipeline
- Uses Claude API directly (Anthropic SDK), NOT LangGraph
- Only uses LangSmith for optional tracing
- Synchronous execution during PR submission
- Focus: Approach detection, rubric evaluation, test/security analysis

**Arch-PR-Analyzer Plugin:**
- Deleted from codebase (commit 84d230d)
- Performed architectural analysis: dependencies, APIs, schemas, data flows, components
- Generated Mermaid diagrams and detailed markdown reports
- Used GitHub MCP for PR data fetching
- Supported multi-granularity analysis (high/medium/low)

**PR Workflow:**
- Users submit PR URLs via `POST /submissions/create`
- System fetches PR metadata and unified diff from GitHub API
- AI feedback generated synchronously and stored in `AIFeedback` model
- Results displayed in Review Tab with Digi-Trainer chat

## Status: Phase 4 - Final Plan

---

# Implementation Plan: Architectural Analysis with LangGraph

## Overview

Integrate architectural analysis capabilities from the deleted arch-pr-analyzer plugin into the current AI review system using LangGraph for orchestration. This will enhance PR submissions with dependency analysis, API change detection, schema impact assessment, and visual diagrams while maintaining backward compatibility.

## Current System Analysis

**AI Review Pipeline** (`services/agentic_review.py`):
- 8-step sequential process using Claude API directly
- Uses LangSmith for tracing only (NOT LangGraph currently)
- Synchronous execution during PR submission
- Focus: approach detection, rubric evaluation, security analysis

**Key Insight**: The system does NOT use LangGraph currently - only LangSmith tracing. This is an opportunity to introduce LangGraph for better orchestration.

## Recommended Approach: Hybrid Augmentation with LangGraph

### Architecture
```
User submits PR → LangGraph Orchestrator
                       ↓
              Decision Router
                /           \
         Simple Path     Enhanced Path (PR)
              |              |
              |         ┌────┴────┐
              |    Parallel Nodes:
              |    - Approach Detection
              |    - Arch Analysis (NEW)
              |    - Dependency Analysis (NEW)
              |    - API Detection (NEW)
              |    - Schema Detection (NEW)
              |         ↓
              |    Enrichment (merge insights)
              |         ↓
              └─────→ Synthesis
                       ↓
                  Save Results
```

**Benefits:**
- Backward compatible (simple path unchanged)
- Parallel execution minimizes time impact
- Architectural insights enrich existing analysis
- Graceful degradation if arch analysis fails

## Critical Components to Build

### 1. LangGraph Orchestrator (NEW)
**File:** `services/review_orchestrator.py` (~600 lines)

**State Schema:**
```python
class ReviewState(TypedDict):
    # Existing
    submission_id: int
    diff_content: str
    rubric: Optional[Dict]

    # NEW - PR data
    pr_metadata: Optional[Dict]  # title, state, commits
    pr_files: Optional[List[Dict]]  # files with patches

    # NEW - Architectural analysis
    arch_components: Optional[Dict]
    arch_dependencies: Optional[Dict]
    arch_api_changes: Optional[Dict]
    arch_schema_changes: Optional[Dict]
    arch_diagrams: Optional[List[str]]  # Mermaid

    # Results
    final_content: str
    errors: List[str]
```

**Graph Structure:**
- Entry: `initialize_review` (load PR data)
- Router: `route_analysis_type` (simple vs enhanced)
- Simple path: `run_legacy_pipeline` (existing AgenticReviewService)
- Enhanced path: Parallel nodes for arch analysis
- Convergence: `enrich_with_architecture` (merge results)
- Synthesis: `synthesize_feedback` (generate markdown)
- Save: `save_results` (database)

### 2. Architectural Analyzer (NEW)
**File:** `services/architectural_analyzer.py` (~800 lines)

**Capabilities:**
- **Dependency Analysis**: Parse imports across Python/JS/Java, build graphs, detect changes
- **API Detection**: Find Flask/FastAPI/Express/Django routes, categorize as new/modified/removed/breaking
- **Schema Analysis**: Detect migration files, parse ORM changes, identify breaking changes
- **Component Mapping**: Identify architectural boundaries, map cross-component dependencies
- **Impact Assessment**: Score scope/risk/complexity (low/medium/high)

### 3. Code Parser (NEW)
**File:** `services/code_parser.py` (~500 lines)

Language-agnostic parsing utilities:
- Python: `import X`, `from X import Y`
- JavaScript: `import X from 'Y'`, `require('X')`
- Java: `import package.Class`
- API decorators: `@app.route()`, `@router.get()`
- ORM models: SQLAlchemy, Django ORM, Prisma

### 4. Diagram Generator (NEW)
**File:** `services/diagram_generator.py` (~400 lines)

Mermaid diagram generation:
- Component dependency graphs (before/after with color coding)
- Data flow diagrams (sequence diagrams)
- API surface diff (added/removed endpoints)

### 5. Database Model (NEW)
**File:** `models/architectural_analysis.py`

```python
class ArchitecturalAnalysis(db.Model):
    __tablename__ = 'architectural_analyses'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, ForeignKey('submissions.id'))

    # Structured data
    components_json = db.Column(db.Text)
    dependencies_diff_json = db.Column(db.Text)
    api_changes_json = db.Column(db.Text)
    schema_changes_json = db.Column(db.Text)

    # Impact scores
    scope_score = db.Column(db.String(20))  # low/medium/high
    risk_score = db.Column(db.String(20))
    complexity_score = db.Column(db.String(20))

    # Diagrams (Mermaid)
    component_diagram = db.Column(db.Text)
    dataflow_diagram = db.Column(db.Text)

    # Relationship
    submission = db.relationship('Submission', backref='arch_analysis')
```

**Migration:** `migrations/versions/xxx_add_architectural_analysis.py`

## Modified Components

### 1. AI Feedback Service (MODIFY)
**File:** `services/ai_feedback.py`

Change line 27-33:
```python
# OLD
from services.agentic_review import AgenticReviewService
service = AgenticReviewService(submission_id)
return service.run_full_review(...)

# NEW
from services.review_orchestrator import orchestrate_review
return orchestrate_review(
    submission_id=submission_id,
    challenge_md=challenge_description,
    diff_content=diff_content,
    rubric=challenge_rubric.get_rubric()
)
```

### 2. Agentic Review Service (REFACTOR)
**File:** `services/agentic_review.py`

- Extract methods (_detect_approach, _analyze_architecture, etc.) as standalone functions
- Keep @traceable decorators
- Make callable from LangGraph nodes
- Maintain backward compatibility for direct calls

## Enhanced Feedback Format

**New Sections Added to Markdown:**

```markdown
## Architectural Overview 🏗️
**Impact Assessment:**
- Scope: Medium (3 components)
- Risk: Low (no breaking changes)
- Complexity: Medium (245 lines, 8 files)

**Component Changes:**
[Mermaid diagram showing before/after]

## API Changes 🔌
**New Endpoints:**
- POST /auth/token
**Modified Endpoints:**
- GET /users/{id} (now requires JWT)

## Database Schema Changes 🗄️
**Tables Modified:**
- users: Added last_login_at, token_version

## Data Flow 🌊
[Mermaid sequence diagram]

## Dependency Changes 📦
**New Dependencies:**
- PyJWT, cryptography
[Dependency graph]
```

Existing sections (approach, evaluation, security, tests, alternatives) remain unchanged but are enriched with architectural context.

## Implementation Phases

### Phase 1: Foundation (Week 1 - 16h)
- Set up LangGraph orchestration with simple/enhanced routing
- Refactor agentic_review.py methods
- Create database model and migration
- **Deliverable:** LangGraph working with existing logic unchanged

### Phase 2: Architectural Core (Week 2 - 24h)
- Build code_parser.py (import/route/model parsing)
- Build architectural_analyzer.py (dependency/API/schema analysis)
- Add comprehensive tests
- **Deliverable:** Can analyze architectural changes independently

### Phase 3: Graph Integration (Week 2 - 16h)
- Add parallel architectural nodes to graph
- Implement enrichment logic
- Test parallel execution and timing
- **Deliverable:** End-to-end architectural analysis in graph

### Phase 4: Diagrams (Week 3 - 16h)
- Build diagram_generator.py
- Generate Mermaid diagrams
- Integrate into markdown synthesis
- **Deliverable:** Visual diagrams in feedback

### Phase 5: Polish (Week 3-4 - 20h)
- Performance optimization (caching, timeouts)
- Enhanced feedback format
- Frontend verification
- Configuration options
- **Deliverable:** Production-ready system

**Total Estimate:** 92 hours (~2.5 weeks for 1 developer)

## Performance Considerations

**Current:** ~15-30s (8 sequential Claude calls)
**Target:** ~17-30s (parallel execution offsets new analysis)

**Strategies:**
- Parallel LangGraph nodes for arch analysis
- PR metadata caching (1-hour TTL)
- Parsed dependency caching by file SHA
- Claude prompt caching for rubric evaluations
- Optional: Skip arch analysis for small PRs (<5 files)

**Graceful Degradation:**
- If arch analysis fails, still show basic feedback
- If timeout (>30s), use simpler analysis
- Configuration to disable arch analysis

## Data Storage

**AIFeedback table** (existing):
- Stores complete markdown with new architectural sections
- evaluation_json enriched with architectural evidence

**ArchitecturalAnalysis table** (new):
- Stores structured architectural data separately
- Enables querying/analytics across submissions
- One-to-one relationship with Submission

## Configuration Options

```python
# config.py additions
ARCH_ANALYSIS_ENABLED = True  # Master toggle
ARCH_ANALYSIS_TIMEOUT = 30  # seconds
ARCH_SKIP_SMALL_PRS = True  # Skip if <5 files
ARCH_DETAIL_LEVEL = "medium"  # basic/medium/deep
```

## Risk Mitigation

1. **Performance:** Parallel execution, caching, timeout handling, fallback to simple mode
2. **Complexity:** Incremental phases, comprehensive tests, clear documentation
3. **Breaking Changes:** Phase 1 ensures existing logic unchanged, feature flag for rollback
4. **LangGraph Learning Curve:** Start simple, build incrementally, pair programming

## Success Metrics

**Performance:**
- P90 latency <30s
- Error rate <2%

**Quality:**
- Architectural insights in >80% of PR submissions
- Dependency detection accuracy >90%
- API change detection accuracy >95%

**Educational Value:**
- Students understand component boundaries better
- Fewer breaking changes introduced
- More actionable feedback

## Critical Files List

1. `services/review_orchestrator.py` (NEW) - LangGraph state machine
2. `services/architectural_analyzer.py` (NEW) - Core analysis logic
3. `services/code_parser.py` (NEW) - Language parsing
4. `services/diagram_generator.py` (NEW) - Mermaid generation
5. `models/architectural_analysis.py` (NEW) - Database model
6. `services/ai_feedback.py` (MODIFY) - Call orchestrator
7. `services/agentic_review.py` (REFACTOR) - Extract functions
8. `migrations/versions/xxx_add_architectural_analysis.py` (NEW)

## Verification Steps

After implementation:
1. Submit test PR with 5-10 files changed
2. Verify architectural sections appear in feedback
3. Check Mermaid diagrams render correctly
4. Verify ArchitecturalAnalysis record created
5. Test timing under 30s
6. Test graceful degradation (no PR URL → simple path)
7. Test error handling (timeout, API failure)
8. Run full test suite
9. Check LangSmith traces show graph execution

---

## User Preferences (Confirmed)

✓ **Use LangGraph** for orchestration (parallel execution, observability)
✓ **Speed to implement** - Focus on core architectural features first
✓ **Enhance existing feedback** - Add architectural sections to current AI feedback (not separate tab)
✓ **Performance budget: up to 45 seconds** - Allows comprehensive analysis with moderate optimization

## Adjusted Scope for Speed

Based on "speed to implement" preference, **prioritize these features:**

**Phase 1-3 (Core - Must Have):**
- ✅ Dependency analysis (imports/requires parsing)
- ✅ API endpoint detection (Flask, FastAPI, Express)
- ✅ Schema change detection (migrations, ORM models)
- ✅ Component mapping (architectural boundaries)
- ✅ Impact assessment (scope/risk/complexity scores)
- ✅ Basic Mermaid diagrams (component graph, dependency graph)

**Phase 4+ (Enhanced - Nice to Have):**
- ⏸ Advanced data flow tracing (defer to later)
- ⏸ Complex sequence diagrams (defer to later)
- ⏸ Cross-repository analysis (not needed for student submissions)
- ⏸ Detailed ripple effect analysis (defer to later)

This focused scope reduces implementation to **~3 weeks** while delivering high-value architectural insights.
