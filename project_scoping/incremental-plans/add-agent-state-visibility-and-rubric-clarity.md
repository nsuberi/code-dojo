# Plan: Generalize Code Review & Add Real-Time Progress Tracking

## Overview

Address two critical improvements to the AI code review system:

1. **Generalize approach detection** - Remove authentication-specific hardcoding and make the system work for any challenge type
2. **Real-time progress tracking** - Show students which analysis steps are running during PR submission using LangGraph streaming

## Problem Analysis

### Issue 1: Approach Detection is Auth-Specific

**Current State:**
- `_detect_approach()` has hardcoded "authentication approach" in prompts (line 56 in agentic_review.py)
- Feedback synthesis assumes authentication context (lines 348, 431-433)
- Security analysis hardcodes "authentication implementation" (line 243)
- Works for API Auth challenge but not generalizable to other challenges (Claude API, database design, etc.)

**Root Cause:**
- Domain-specific language embedded in service layer instead of rubric data
- Learning points hardcoded instead of stored in rubric
- No `approach_type` field in rubric schema to indicate what kind of approaches these are

### Issue 2: No Visibility into Analysis Progress

**Current State:**
- PR submission uses synchronous `graph.invoke()` which blocks for 15-30 seconds
- User sees generic "Analyzing your approach..." spinner with no detail
- 11 internal analysis steps are invisible to the user
- No indication of what's happening or how long it will take

**Root Cause:**
- LangGraph has streaming capabilities (`graph.stream()`) but we use blocking `invoke()`
- No progress tracking model or API endpoint
- Frontend has no way to poll or receive progress updates
- `run_basic_review` node bundles 7 steps internally (invisible to graph streaming)

## Solution Design

### Part 1: Generalize Approach Detection

#### A. Add Contextual Fields to Rubric Schema

**New fields in ChallengeRubric.rubric_json:**

```python
{
  "version": "1.1",  # Bump version

  # NEW: Context for generalization
  "approach_type": "authentication",  # authentication, implementation_strategy, design_pattern, etc.
  "approach_type_label": "authentication approach",  # Used in natural language prompts
  "domain_context": "API security and access control",  # Background for Claude

  # NEW: Configurable learning points
  "learning_points": [
    "Authentication protects sensitive endpoints while keeping read operations accessible",
    "The decorator pattern provides clean, reusable authentication logic",
    "Different auth approaches have different tradeoffs - choose based on your use case"
  ],

  # EXISTING: No changes needed
  "title": "API Authentication Multi-Approach Rubric",
  "valid_approaches": [...],
  "universal_criteria": [...],
  "approach_specific_criteria": {...}
}
```

#### B. Update Service Methods to Use Rubric Context

**File: `services/agentic_review.py`**

**Changes:**

1. **`_detect_approach()` - Line 42-84**
   ```python
   # OLD
   prompt = f"""Analyze this code diff to determine which authentication approach was used.

   # NEW
   approach_type_label = rubric.get('approach_type_label', 'approach')
   prompt = f"""Analyze this code diff to determine which {approach_type_label} was used.
   ```

2. **`_analyze_security()` - Line 237-276**
   ```python
   # OLD
   prompt = f"""Perform a security analysis of this {approach_id} authentication implementation.

   # NEW
   domain_context = rubric.get('domain_context', 'implementation')
   prompt = f"""Perform a security analysis of this {approach_id} {domain_context}.
   ```

3. **`_synthesize_feedback()` - Line 328-435**
   ```python
   # OLD (hardcoded)
   feedback_parts.append(f"# Code Review: API Authentication\n")

   # NEW (from rubric)
   title = rubric.get('title', 'Code Review')
   feedback_parts.append(f"# {title}\n")

   # OLD (hardcoded learning points)
   feedback_parts.append("1. Authentication protects sensitive endpoints...")

   # NEW (from rubric)
   learning_points = rubric.get('learning_points', [])
   for i, point in enumerate(learning_points, 1):
       feedback_parts.append(f"{i}. {point}")
   ```

#### C. Update Existing Rubric Data

**File: `seed_data.py`**

Migrate API Auth rubric (lines 877-998) to include new fields:
```python
"rubric_json": json.dumps({
    "version": "1.1",
    "approach_type": "authentication",
    "approach_type_label": "authentication approach",
    "domain_context": "API security and access control",
    "learning_points": [
        "Authentication protects sensitive endpoints while keeping read operations accessible",
        "The decorator pattern provides clean, reusable authentication logic",
        "Different auth approaches have different tradeoffs - choose based on your use case"
    ],
    # ... existing fields
})
```

Migrate Claude API rubric (lines 141-209) to include:
```python
"rubric_json": json.dumps({
    "version": "1.1",
    "approach_type": "implementation_strategy",
    "approach_type_label": "LLM integration approach",
    "domain_context": "Claude API integration patterns",
    "learning_points": [
        "Different client libraries offer varying levels of abstraction",
        "Error handling is critical when working with external APIs",
        "Environment configuration keeps sensitive credentials secure"
    ],
    # ... existing fields
})
```

#### D. Add Backward Compatibility

**File: `services/agentic_review.py`**

Add fallback values for rubrics without new fields:
```python
def _detect_approach(self, diff_content, rubric):
    # Fallback to generic language if not specified
    approach_type_label = rubric.get('approach_type_label', 'approach')

def _synthesize_feedback(self, ..., rubric):
    # Fallback learning points
    learning_points = rubric.get('learning_points', [
        'Implementation follows best practices',
        'Different approaches have tradeoffs',
        'Consider your specific use case'
    ])
```

### Part 2: Real-Time Progress Tracking

#### A. Expose LangGraph Execution State via Streaming

**Current:** `graph.invoke(state)` blocks until complete

**New:** `graph.stream(state, stream_mode="updates")` yields events

**File: `services/review_orchestrator.py`**

Add new streaming function:
```python
def orchestrate_review_streaming(submission_id, challenge_md, diff_content, rubric=None,
                                  pr_metadata=None, pr_files=None, progress_callback=None):
    """
    Orchestrate review with real-time progress updates.

    Args:
        progress_callback: Function called with progress events
            Event format: {"step": str, "description": str, "progress": int, "status": str}
    """
    initial_state = ReviewState(...)
    graph = create_review_graph()

    # Define step metadata for user-friendly display
    step_metadata = {
        "initialize": {"description": "Setting up analysis", "weight": 5},
        "route_analysis": {"description": "Determining analysis path", "weight": 3},
        "run_basic_review": {"description": "Running core analysis", "weight": 50},
        "run_arch_analysis": {"description": "Analyzing architecture", "weight": 20},
        "enrich_feedback": {"description": "Cross-referencing insights", "weight": 7},
        "synthesize": {"description": "Creating feedback", "weight": 10},
        "save_results": {"description": "Saving results", "weight": 5}
    }

    total_weight = sum(meta["weight"] for meta in step_metadata.values())
    current_progress = 0

    # Stream events
    for event in graph.stream(initial_state, stream_mode="updates"):
        node_name = list(event.keys())[0]  # Node that just executed

        if node_name in step_metadata:
            meta = step_metadata[node_name]
            current_progress += meta["weight"]

            if progress_callback:
                progress_callback({
                    "step": node_name,
                    "description": meta["description"],
                    "progress": int((current_progress / total_weight) * 100),
                    "status": "running"
                })

    # Get final state
    final_state = {}
    for event in graph.stream(initial_state, stream_mode="values"):
        final_state = event

    if progress_callback:
        progress_callback({
            "step": "complete",
            "description": "Analysis complete",
            "progress": 100,
            "status": "complete"
        })

    return _convert_to_legacy_format(final_state)
```

#### B. Add Progress Tracking to Database

**File: `models/submission.py`**

Add progress fields:
```python
class Submission(db.Model):
    # ... existing fields

    # NEW: Progress tracking
    analysis_step = db.Column(db.String(100))  # Current step name
    analysis_progress = db.Column(db.Integer, default=0)  # 0-100
    analysis_step_description = db.Column(db.String(200))  # Human-readable
    analysis_status = db.Column(db.String(20), default='pending')  # pending, running, complete, error
```

#### C. Add Server-Sent Events Endpoint

**File: `routes/submissions.py`**

Add streaming endpoint:
```python
@submissions_bp.route('/<int:submission_id>/progress-stream')
def stream_analysis_progress(submission_id):
    """Server-Sent Events endpoint for real-time progress."""
    submission = Submission.query.get_or_404(submission_id)

    # Security check
    if submission.user_id != current_user.id and not current_user.is_instructor:
        return jsonify({'error': 'Unauthorized'}), 403

    def event_generator():
        """Generator function for SSE."""
        def send_progress(event):
            # Update database
            submission.analysis_step = event['step']
            submission.analysis_progress = event['progress']
            submission.analysis_step_description = event['description']
            submission.analysis_status = 'running' if event['status'] == 'running' else 'complete'
            db.session.commit()

            # Send to client
            yield f"data: {json.dumps(event)}\n\n"

        # Get PR data
        parsed = parse_pr_url(submission.pr_url)
        pr_metadata = fetch_pr_metadata(parsed['owner'], parsed['repo'], parsed['pr_number'])
        pr_files = fetch_pr_files(parsed['owner'], parsed['repo'], parsed['pr_number'])
        diff_content, _ = fetch_github_diff_from_pr(submission.pr_url)

        goal = LearningGoal.query.get(submission.goal_id)
        challenge_rubric = ChallengeRubric.query.filter_by(learning_goal_id=goal.id).first()

        # Run streaming analysis
        ai_result = orchestrate_review_streaming(
            submission_id=submission.id,
            challenge_md=goal.challenge_md,
            diff_content=diff_content,
            rubric=challenge_rubric.get_rubric() if challenge_rubric else None,
            pr_metadata=pr_metadata,
            pr_files=pr_files,
            progress_callback=send_progress
        )

        # Save final result
        if isinstance(ai_result, dict):
            ai_feedback = AIFeedback(
                submission_id=submission.id,
                content=ai_result.get('content', ''),
                detected_approach=ai_result.get('detected_approach'),
                evaluation_json=json.dumps(ai_result.get('evaluation')),
                alternative_approaches_json=json.dumps(ai_result.get('alternatives')),
                line_references_json=json.dumps(ai_result.get('line_references'))
            )
            db.session.add(ai_feedback)
            submission.status = 'ai_complete'
            submission.analysis_status = 'complete'
            db.session.commit()

    return Response(event_generator(), mimetype='text/event-stream')
```

#### D. Modify Submission Creation to Start Background Analysis

**File: `routes/submissions.py`**

Update `create_submission()`:
```python
@submissions_bp.route('/create', methods=['POST'])
@login_required
def create_submission():
    # ... existing validation code (lines 59-104)

    # Create submission
    submission = Submission(
        user_id=current_user.id,
        goal_id=goal.id,
        pr_url=pr_url,
        pr_number=parsed['pr_number'],
        pr_title=pr_metadata['title'],
        pr_state=pr_metadata['state'],
        pr_base_sha=pr_metadata['base']['sha'],
        pr_head_sha=pr_metadata['head']['sha'],
        status='pending',
        analysis_status='pending'  # NEW
    )
    db.session.add(submission)
    db.session.commit()

    # NEW: Redirect immediately; analysis happens via SSE
    flash('Submission received! Analysis is running...', 'info')
    return redirect(url_for('modules.goal_detail',
                           module_id=goal.module_id,
                           goal_id=goal.id) + '#tab-review')
```

#### E. Add Frontend Progress UI

**File: `templates/modules/goal.html`**

Replace static spinner (lines 493-503) with progress tracker:
```html
<!-- NEW: Progress tracker for pending analysis -->
<div class="analysis-progress" id="analysis-progress-{{ submission.id }}"
     data-submission-id="{{ submission.id }}"
     style="display: {% if submission.status == 'pending' %}block{% else %}none{% endif %}">

    <div class="progress-header">
        <h4>Analyzing Your Submission</h4>
        <span class="progress-percentage">0%</span>
    </div>

    <div class="progress-bar-container">
        <div class="progress-bar-fill" style="width: 0%"></div>
    </div>

    <div class="progress-steps">
        <div class="step" data-step="initialize">
            <span class="step-icon">○</span>
            <span class="step-label">Initializing</span>
        </div>
        <div class="step" data-step="run_basic_review">
            <span class="step-icon">○</span>
            <span class="step-label">Analyzing Code</span>
        </div>
        <div class="step" data-step="run_arch_analysis">
            <span class="step-icon">○</span>
            <span class="step-label">Architecture Review</span>
        </div>
        <div class="step" data-step="synthesize">
            <span class="step-icon">○</span>
            <span class="step-label">Creating Feedback</span>
        </div>
    </div>

    <p class="current-step-description">Setting up analysis...</p>
</div>
```

**File: `static/js/review-tab.js` (new file)**

Add progress tracking JavaScript:
```javascript
// Track analysis progress via Server-Sent Events
function trackAnalysisProgress(submissionId) {
    const progressContainer = document.getElementById(`analysis-progress-${submissionId}`);
    if (!progressContainer) return;

    const progressBar = progressContainer.querySelector('.progress-bar-fill');
    const progressPercentage = progressContainer.querySelector('.progress-percentage');
    const stepDescription = progressContainer.querySelector('.current-step-description');
    const steps = progressContainer.querySelectorAll('.step');

    // Connect to SSE endpoint
    const eventSource = new EventSource(`/submissions/${submissionId}/progress-stream`);

    eventSource.addEventListener('message', (event) => {
        const data = JSON.parse(event.data);

        // Update progress bar
        progressBar.style.width = data.progress + '%';
        progressPercentage.textContent = data.progress + '%';

        // Update step description
        stepDescription.textContent = data.description;

        // Update step indicators
        steps.forEach(step => {
            const stepName = step.getAttribute('data-step');
            const icon = step.querySelector('.step-icon');

            if (stepName === data.step) {
                icon.textContent = '●';  // Active
                step.classList.add('active');
            } else if (data.progress > getStepProgress(stepName)) {
                icon.textContent = '✓';  // Complete
                step.classList.add('complete');
                step.classList.remove('active');
            }
        });

        // Complete
        if (data.status === 'complete') {
            eventSource.close();
            setTimeout(() => {
                location.reload();  // Refresh to show feedback
            }, 1000);
        }
    });

    eventSource.addEventListener('error', (error) => {
        console.error('SSE error:', error);
        eventSource.close();
        stepDescription.textContent = 'Error during analysis. Please refresh the page.';
    });

    function getStepProgress(stepName) {
        const weights = {
            'initialize': 5,
            'route_analysis': 8,
            'run_basic_review': 58,
            'run_arch_analysis': 78,
            'enrich_feedback': 85,
            'synthesize': 95,
            'save_results': 100
        };
        return weights[stepName] || 0;
    }
}

// Auto-start tracking for pending submissions
document.addEventListener('DOMContentLoaded', () => {
    const progressContainers = document.querySelectorAll('.analysis-progress');
    progressContainers.forEach(container => {
        const submissionId = container.getAttribute('data-submission-id');
        trackAnalysisProgress(submissionId);
    });
});
```

**File: `static/css/styles.css`**

Add progress UI styles:
```css
.analysis-progress {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
}

.progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.progress-percentage {
    font-weight: bold;
    color: #0066cc;
    font-size: 1.2em;
}

.progress-bar-container {
    background: #e9ecef;
    border-radius: 4px;
    height: 24px;
    overflow: hidden;
    margin-bottom: 20px;
}

.progress-bar-fill {
    background: linear-gradient(90deg, #0066cc, #0099ff);
    height: 100%;
    transition: width 0.3s ease;
}

.progress-steps {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
}

.step {
    flex: 1;
    text-align: center;
    opacity: 0.5;
    transition: opacity 0.3s;
}

.step.active {
    opacity: 1;
    color: #0066cc;
}

.step.complete {
    opacity: 0.8;
    color: #28a745;
}

.step-icon {
    display: block;
    font-size: 1.5em;
    margin-bottom: 5px;
}

.current-step-description {
    text-align: center;
    color: #6c757d;
    font-style: italic;
}
```

## Implementation Phases

### Phase 1: Generalize Approach Detection (2-3 days)

**Tasks:**
1. Add new fields to rubric schema (approach_type, approach_type_label, domain_context, learning_points)
2. Update `_detect_approach()` to use `approach_type_label` from rubric
3. Update `_analyze_security()` to use `domain_context` from rubric
4. Update `_synthesize_feedback()` to use `learning_points` from rubric
5. Migrate existing rubrics in seed_data.py
6. Add backward compatibility fallbacks
7. Test with both API Auth and Claude API challenges

**Deliverable:** Approach detection works for any challenge type without code changes

### Phase 2: Add Progress Tracking Infrastructure (3-4 days)

**Tasks:**
1. Add progress fields to Submission model
2. Create streaming version of orchestrate_review
3. Add SSE endpoint `/submissions/<id>/progress-stream`
4. Modify submission creation to redirect immediately
5. Add database migration for new fields

**Deliverable:** Backend streaming infrastructure works

### Phase 3: Frontend Progress UI (2-3 days)

**Tasks:**
1. Create progress UI HTML in goal.html
2. Add JavaScript for SSE connection and UI updates
3. Add CSS for progress visualization
4. Test progress tracking end-to-end
5. Handle edge cases (errors, timeouts, connection drops)

**Deliverable:** Users see real-time progress during analysis

### Phase 4: Testing & Polish (1-2 days)

**Tasks:**
1. Test with various challenge types
2. Test progress tracking with slow/fast analyses
3. Verify backward compatibility with old rubrics
4. Add error handling for SSE connection failures
5. Performance testing (ensure no memory leaks)

**Deliverable:** Production-ready system

## Critical Files to Modify

### Part 1: Generalize Approach Detection
1. `services/agentic_review.py` - Update 3 methods to use rubric context
2. `seed_data.py` - Migrate 2 rubrics to new schema
3. `models/challenge_rubric.py` - Documentation updates only

### Part 2: Progress Tracking
1. `services/review_orchestrator.py` - Add streaming function
2. `models/submission.py` - Add progress fields
3. `routes/submissions.py` - Add SSE endpoint, modify create_submission
4. `templates/modules/goal.html` - Add progress UI
5. `static/js/review-tab.js` - NEW FILE for progress tracking
6. `static/css/styles.css` - Add progress styles
7. `migrations/add_submission_progress.py` - NEW FILE for migration

## Verification Steps

### Part 1: Generalized Approach Detection

1. Submit PR for API Auth challenge
   - Verify feedback uses "authentication approach" language
   - Verify learning points appear correctly

2. Submit PR for Claude API challenge
   - Verify feedback uses "LLM integration approach" language
   - Verify approach detection works (SDK vs LangChain vs HTTP)

3. Create new challenge with different approach type
   - Verify no code changes needed
   - Verify prompts use correct terminology

### Part 2: Progress Tracking

1. Submit PR and watch progress in real-time
   - Verify progress bar updates from 0% to 100%
   - Verify step indicators change (○ → ● → ✓)
   - Verify step descriptions update
   - Verify page auto-refreshes when complete

2. Test error handling
   - Kill server mid-analysis → verify frontend shows error
   - Submit invalid PR → verify error handling

3. Test multiple concurrent submissions
   - Submit 2 PRs simultaneously
   - Verify both progress trackers work independently

4. Test with/without architectural analysis
   - Small PR (<5 files) → verify simpler progress
   - Large PR (>10 files) → verify architectural analysis step appears

## Risk Mitigation

1. **Backward Compatibility**: Old rubrics without new fields use fallback values
2. **SSE Connection Failures**: Frontend shows error and allows manual refresh
3. **Performance**: SSE is lightweight; no database polling overhead
4. **Database Migration**: New fields are nullable; existing data unaffected
5. **LangGraph Streaming**: Falls back to `invoke()` if streaming fails

## Success Metrics

**Part 1: Generalization**
- ✓ Can create new challenge types without modifying agentic_review.py
- ✓ Prompts and feedback use challenge-appropriate language
- ✓ Learning points come from rubric, not code

**Part 2: Progress Tracking**
- ✓ Users see which analysis step is running in real-time
- ✓ Progress updates within 1 second of step completion
- ✓ SSE connection stable for 30+ second analyses
- ✓ No user confusion about analysis status
