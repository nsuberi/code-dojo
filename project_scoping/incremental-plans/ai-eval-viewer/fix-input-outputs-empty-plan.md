# Plan: Fix Integration Tests, UI Terminology, and LangSmith Trace I/O

## Overview
Three tasks:
1. Verify integration tests run correctly
2. Change "traces" to "threads" in ai-eval-viewer UI
3. Add inputs/outputs to LangSmith traces to fix empty I/O display

---

## Task 1: Verify Integration Tests Run

**Command:**
```bash
pytest tests/test_articulation_traces.py -v -s
```

**Prerequisites:**
- `ANTHROPIC_API_KEY` environment variable
- `LANGSMITH_API_KEY` environment variable

**Expected:** Tests create threads with up to 3 interactions per rubric item before awarding gems.

---

## Task 2: Fix UI Terminology (traces → threads)

### Files to Modify

**1. `ai-eval-viewer/src/pages/Dashboard.tsx` (line 63)**
```tsx
// FROM:
Inspect and annotate LangSmith traces from Code Dojo's AI features

// TO:
Inspect and annotate LangSmith threads from Code Dojo's AI features
```

**2. `ai-eval-viewer/src/components/FeatureCard.tsx` (line 24)**
```tsx
// FROM:
<span className="feature-stat-label">Traces</span>

// TO:
<span className="feature-stat-label">Threads</span>
```

**3. `ai-eval-viewer/src/pages/ThreadList.tsx`**

| Line | From | To |
|------|------|-----|
| 109 | `Loading traces...` | `Loading threads...` |
| 113 | `No traces found for this feature.` | `No threads found for this feature.` |
| 138 | `{threads.length} traces` | `{threads.length} threads` |
| 146 | `Select a trace to view details` | `Select a thread to view details` |
| 148 | `to open selected trace` | `to open selected thread` |

**4. `ai-eval-viewer/src/pages/ThreadDetail.tsx`**

| Line | From | To |
|------|------|-----|
| 176 | `Loading trace details...` | `Loading thread details...` |
| 201 | `<span>Trace</span>` | `<span>Thread</span>` |

---

## Task 3: Fix LangSmith Empty Input/Output

The traces use `trace()` context managers but don't pass `inputs` or `outputs` parameters.

### Files to Modify

**1. `services/articulation_harness.py`**

**a) `start_session()` trace (lines 83-92)** - Add inputs:
```python
self._session_trace_context = trace(
    name="articulation_harness_orchestration",
    inputs={
        "submission_id": self.submission_id,
        "user_id": self.user_id,
        "learning_goal_id": self.learning_goal_id,
        "focus_goal_id": focus_goal_id
    },
    metadata={...}  # existing metadata
)
```

**b) `process_message()` trace (lines 210-219)** - Add inputs and capture outputs:
```python
with trace(
    name="articulation_message_process",
    inputs={
        "user_message": user_message,
        "input_mode": input_mode,
        "voice_duration": voice_duration
    },
    metadata={...}  # existing metadata
) as run_tree:
    # ... existing processing ...
    # Before each return, set:
    # run_tree.outputs = {"response": result.get("response"), "engagement": result.get("engagement")}
```

**c) `process_voice_input()` trace (lines 254-262)** - Add inputs and outputs:
```python
with trace(
    name="articulation_voice_process",
    inputs={
        "audio_data_size": len(audio_data) if audio_data else 0,
        "session_id": self.session.id if self.session else None
    },
    metadata={...}
) as run_tree:
    # ... existing processing ...
    run_tree.outputs = {"transcription": result.get('transcription'), "success": True}
```

**d) `_focus_on_goal()` trace (lines 302-311)** - Add inputs:
```python
self._topic_trace_context = trace(
    name="articulation_topic_conversation",
    inputs={
        "goal_id": goal['id'],
        "goal_title": goal['title'],
        "introduce": introduce
    },
    metadata={...}
)
```

**e) Guided mode trace in `_goal_completed()` (lines 567-576)** - Same pattern as above.

**2. `services/socratic_harness_base.py`**

**`evaluate_rubric_item()` (lines 97-123)** - Add inputs and outputs:
```python
with trace(
    name="evaluate_rubric_item",
    inputs={
        "student_response": student_response,
        "criterion": rubric_item['criterion'],
        "pass_indicators": rubric_item['pass_indicators']
    },
    metadata=metadata
) as run_tree:
    # ... existing evaluation code ...
    run_tree.outputs = {"passed": result['passed'], "evaluation": result.get('evaluation', '')}
    return result['passed'], result.get('evaluation', '')
```

---

## Verification

### 1. Run integration tests (before changes - baseline):
```bash
pytest tests/test_articulation_traces.py::TestArticulationTraceGrouping::test_traces_grouped_as_thread -v -s
```

### 2. Add test to verify inputs/outputs are captured

Add new test to `tests/test_articulation_traces.py` in `TestArticulationTraceGrouping` class:

```python
@pytest.mark.integration
def test_traces_have_inputs_and_outputs(self, langsmith_enabled, articulation_test_data, client):
    """Verify traces have inputs and outputs populated for LangSmith visibility.

    This test ensures that trace() calls include inputs/outputs parameters
    so they're visible in the LangSmith UI and ai-eval-viewer.
    """
    with app.app_context():
        data = articulation_test_data
        harness = ArticulationHarness(
            data['submission'].id,
            data['user'].id,
            langsmith_project='code-dojo-tests'
        )

        # Start session
        session = harness.start_session()

        # Process messages to create traces
        harness.process_message("1", input_mode='text')
        harness.process_message(
            "I used @login_required decorator to protect routes.",
            input_mode='text'
        )

        harness.end_session()

        # Wait for traces to sync
        time.sleep(3)

        from langsmith import Client
        from models.agent_session import AgentSession

        ls_client = Client()
        db_session = AgentSession.query.get(session['session_id'])
        thread_id = db_session.langsmith_run_id

        # Query traces for this session
        filter_string = f'and(in(metadata_key, ["session_id"]), eq(metadata_value, "{thread_id}"))'
        runs = list(ls_client.list_runs(
            project_name='code-dojo-tests',
            filter=filter_string,
            limit=20
        ))

        # Check that traces have inputs and outputs
        traces_with_io = []
        for run in runs:
            has_input = run.inputs is not None and len(run.inputs) > 0
            has_output = run.outputs is not None and len(run.outputs) > 0
            print(f"\n{run.name}:")
            print(f"  inputs: {run.inputs}")
            print(f"  outputs: {run.outputs}")
            if has_input or has_output:
                traces_with_io.append(run.name)

        # After fix, these should have inputs/outputs:
        expected_traces_with_io = [
            'articulation_harness_orchestration',
            'articulation_message_process',
            'evaluate_rubric_item'
        ]

        for expected in expected_traces_with_io:
            matching = [t for t in traces_with_io if expected in t]
            assert len(matching) > 0, \
                f"Expected '{expected}' trace to have inputs/outputs but it was empty"
```

### 3. Run test (after making changes):
```bash
pytest tests/test_articulation_traces.py::TestArticulationTraceGrouping::test_traces_have_inputs_and_outputs -v -s
```

This test will:
- FAIL before the fix (traces have no inputs/outputs)
- PASS after adding inputs/outputs to trace() calls

### 4. Verify UI terminology:
```bash
cd ai-eval-viewer && npm run dev
```
- Check Dashboard shows "threads" in description
- Check Feature cards show "N Threads"
- Check ThreadList shows "Loading threads...", "N threads"
- Check breadcrumb shows "Thread"

### 5. Verify in LangSmith UI:
- Open LangSmith UI (`code-dojo-tests` project)
- Find traces from the test run
- Verify Input and Output tabs show data (not empty)

---

## Critical Files

| File | Purpose |
|------|---------|
| `services/articulation_harness.py` | Main trace I/O fixes (6 trace calls) |
| `services/socratic_harness_base.py` | evaluate_rubric_item trace fix |
| `ai-eval-viewer/src/pages/ThreadList.tsx` | Most terminology changes (5 locations) |
| `ai-eval-viewer/src/pages/ThreadDetail.tsx` | Breadcrumb + loading terminology |
| `ai-eval-viewer/src/pages/Dashboard.tsx` | Header terminology |
| `ai-eval-viewer/src/components/FeatureCard.tsx` | Card label terminology |
| `tests/test_articulation_traces.py` | Verification (no changes needed) |
